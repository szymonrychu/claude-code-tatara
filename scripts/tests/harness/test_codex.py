import json
import os
from pathlib import Path

import tomllib
from harness.sources import load_sources
from harness.targets.codex import CodexEmitter, toml_multiline

GOLDEN = Path(__file__).parent / "golden" / "codex"


def test_golden(tree):
    out = CodexEmitter().render(load_sources(tree))
    if os.environ.get("UPDATE_GOLDEN"):
        for rel, text in out.items():
            (GOLDEN / rel).parent.mkdir(parents=True, exist_ok=True)
            (GOLDEN / rel).write_text(text)
    want = {str(p.relative_to(GOLDEN)): p.read_text() for p in GOLDEN.rglob("*") if p.is_file()}
    assert out == want


def test_every_toml_parses(tree):
    out = CodexEmitter().render(load_sources(tree))
    tomls = {k: v for k, v in out.items() if k.endswith(".toml")}
    assert ".codex/config.toml" in tomls and ".codex/agents/scout.toml" in tomls
    for text in tomls.values():
        tomllib.loads(text)
    agent = tomllib.loads(out[".codex/agents/scout.toml"])
    assert agent["developer_instructions"] == "You are a scout.\n"
    assert "model" not in agent
    assert tomllib.loads(out[".codex/config.toml"])["mcp_servers"]["docs"]["url"]


def test_model_override(tree):
    cfg = tree / ".claude/workbench.json"
    cfg.write_text(
        json.dumps({"harness": {"targets": ["codex"], "models": {"codex": {"opus": "gpt-x"}}}})
    )
    out = CodexEmitter().render(load_sources(tree))
    assert tomllib.loads(out[".codex/agents/scout.toml"])["model"] == "gpt-x"
    assert "model" not in tomllib.loads(out[".codex/agents/helper.toml"])


def test_escaping_round_trips():
    for body in ["a'''b\n", 'it\'s\\ "q" \t\n', "ends '\n", "ctl \x01 x\n", 'tri """ q\n']:
        assert tomllib.loads("v = " + toml_multiline(body))["v"] == body


def test_hooks_only_registered_guards(tree):
    hooks = json.loads(CodexEmitter().render(load_sources(tree))[".codex/hooks.json"])["hooks"]
    pre = {g["matcher"]: g["hooks"][0]["command"] for g in hooks["PreToolUse"]}
    assert set(pre) == {"Bash", "apply_patch|Edit|MultiEdit|NotebookEdit|Write"}
    assert pre["Bash"] == (
        "python3 plugins/core/hooks/adapter.py --harness codex --event pre-tool --hook guard-bash"
    )
    assert "matcher" not in hooks["SubagentStop"][0]
    text = json.dumps(hooks)
    for gone in ("verify-recorder", "bash-output-filter", "format-file", "PostToolUse"):
        assert gone not in text


def test_no_mcp_no_config(tree):
    (tree / ".mcp.json").unlink()
    assert ".codex/config.toml" not in CodexEmitter().render(load_sources(tree))


def test_agent_body_rewritten(tree):
    f = tree / "plugins/core/agents/scout.md"
    f.write_text(f.read_text() + 'Run "${CLAUDE_PLUGIN_ROOT}/x.py" via core:alpha.\n')
    body = tomllib.loads(CodexEmitter().render(load_sources(tree))[".codex/agents/scout.toml"])[
        "developer_instructions"
    ]
    assert "plugins/core/x.py" in body and "CLAUDE_PLUGIN_ROOT" not in body and "core:" not in body


REPO = Path(__file__).resolve().parents[3]


def test_toml_parses_and_roundtrips(tree):
    f = tree / "plugins/core/agents/scout.md"
    f.write_text(f.read_text() + "tricky ''' printf '\\n' \\ \"q\" \x01\n")
    out = CodexEmitter().render(load_sources(tree))
    for text in out.values():
        if text.startswith("name ="):
            tomllib.loads(text)
    body = tomllib.loads(out[".codex/agents/scout.toml"])["developer_instructions"]
    assert body.endswith("tricky ''' printf '\\n' \\ \"q\" \x01\n")
    for s in ["a'''b printf '\\n' x\n", "q '''\\\n", 'x """ \\n \\\n']:
        assert tomllib.loads("v = " + toml_multiline(s))["v"] == s


def test_real_tree_renders_every_agent():
    out = CodexEmitter().render(load_sources(REPO))
    agents = {k for k in out if k.startswith(".codex/agents/")}
    assert ".codex/agents/verifier.toml" in agents
    for k in agents:
        tomllib.loads(out[k])


def test_apply_patch_hook():
    import subprocess
    import sys

    hooks = json.loads(CodexEmitter().render(load_sources(REPO))[".codex/hooks.json"])["hooks"]
    want = "apply_patch|Edit|MultiEdit|NotebookEdit|Write"
    grp = next(g for g in hooks["PreToolUse"] if g["matcher"] == want)
    cmd = grp["hooks"][0]["command"]
    assert "--hook protect-files" in cmd and "--harness codex" in cmd
    patch = "*** Begin Patch\n*** Update File: .git/config\n@@\n-a\n+b\n*** End Patch\n"
    payload = {
        "session_id": "s",
        "cwd": str(REPO),
        "hook_event_name": "PreToolUse",
        "tool_name": "apply_patch",
        "tool_input": {"command": patch},
    }
    run = subprocess.run(
        cmd.replace("python3", sys.executable, 1),
        shell=True,
        cwd=REPO,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    assert "BLOCKED by protect-files" in run.stdout + run.stderr


def test_path_rules_block(tree):
    from harness import agents_md
    from harness.setup import PATH_RULE_TARGETS

    assert "codex" in PATH_RULE_TARGETS
    assert agents_md.sync(tree, True)
    text = (tree / "AGENTS.md").read_text()
    assert "<!-- workbench:path-rules:begin -->" in text and "read `.claude/rules/" in text
