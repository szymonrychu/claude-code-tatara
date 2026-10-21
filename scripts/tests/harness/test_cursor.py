import json
import os
from pathlib import Path

import pytest
from harness.emit import registry
from harness.sources import load_sources

GOLDEN = Path(__file__).parent / "golden" / "cursor"


def render(tree):
    return registry()["cursor"].render(load_sources(tree))


def test_golden(tree):
    out = render(tree)
    if os.environ.get("UPDATE_GOLDEN"):
        for p, t in out.items():
            f = GOLDEN / p
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(t)
    want = {str(f.relative_to(GOLDEN)): f.read_text() for f in GOLDEN.rglob("*") if f.is_file()}
    assert out == want


def test_rules_mdc(tree):
    out = render(tree)
    assert not any(p.endswith(".md") for p in out if p.startswith(".cursor/rules/"))
    py = out[".cursor/rules/python.mdc"]
    assert "globs: **/*.py,**/pyproject.toml" in py and "alwaysApply: false" in py
    assert "alwaysApply: true" in out[".cursor/rules/always.mdc"]
    assert "globs" not in out[".cursor/rules/always.mdc"]


def test_agents_readonly_and_model(tree):
    out = render(tree)
    scout = out[".cursor/agents/scout.md"]
    assert "readonly: true" in scout and "model: gpt-fixture" in scout
    assert "model: inherit" in out[".cursor/agents/helper.md"]
    (tree / ".claude/workbench.json").write_text(
        json.dumps(
            {"harness": {"targets": ["cursor"], "models": {"cursor": {"sonnet": "composer-2"}}}}
        )
    )
    helper = render(tree)[".cursor/agents/helper.md"]
    assert "model: composer-2" in helper


def test_agent_with_write_tool_not_readonly(tree):
    a = tree / "plugins/core/agents/scout.md"
    a.write_text(a.read_text().replace("[Read, Grep, Glob, Bash]", "[Read, Edit]"))
    assert "readonly" not in render(tree)[".cursor/agents/scout.md"]


def test_agent_body_rewritten(tree):
    a = tree / "plugins/core/agents/scout.md"
    a.write_text(a.read_text() + "\nRun ${CLAUDE_PLUGIN_ROOT}/x.py via core:thing.\n")
    body = render(tree)[".cursor/agents/scout.md"]
    assert "plugins/core/x.py" in body and "CLAUDE_PLUGIN_ROOT" not in body
    assert "core:thing" not in body


def test_hooks_fail_closed(tree):
    hooks = json.loads(render(tree)[".cursor/hooks.json"])
    assert hooks["version"] == 1
    pre = hooks["hooks"]["preToolUse"]
    assert {h["matcher"] for h in pre} == {"Shell", "Write|Delete"}
    assert all(h["failClosed"] is True for h in pre)
    assert all("adapter.py --harness cursor" in h["command"] for h in pre)
    assert "subagent-commit-guard" in hooks["hooks"]["subagentStop"][0]["command"]
    text = json.dumps(hooks)
    for claude_only in ("verify-recorder", "bash-output-filter", "format-file"):
        assert claude_only not in text


def test_mcp_env_syntax(tree):
    (tree / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"x": {"url": "https://h/${TOKEN}", "env": {"K": "${A:-d}"}}}})
    )
    mcp = json.loads(render(tree)[".cursor/mcp.json"])
    assert mcp["mcpServers"]["x"]["url"] == "https://h/${env:TOKEN}"
    assert mcp["mcpServers"]["x"]["env"]["K"] == "${env:A}"


def test_no_mcp_file_no_output(tree):
    (tree / ".mcp.json").unlink()
    assert ".cursor/mcp.json" not in render(tree)


@pytest.mark.parametrize("p", ["AGENTS.md", ".agents/skills"])
def test_native_paths_not_written(tree, p):
    assert not any(k.startswith(p) for k in render(tree))


def test_bare_prose_plugin_root_mention_ok(tree):
    a = tree / "plugins/core/agents/scout.md"
    a.write_text(a.read_text() + "\nnever expand CLAUDE_PLUGIN_ROOT yourself.\n")
    assert "CLAUDE_PLUGIN_ROOT" in render(tree)[".cursor/agents/scout.md"]


def test_braced_plugin_root_rewritten(tree):
    a = tree / "plugins/core/agents/scout.md"
    a.write_text(a.read_text() + "\nuse ${CLAUDE_PLUGIN_ROOT}/x\n")
    out = render(tree)
    assert "plugins/core/x" in out[".cursor/agents/scout.md"]


def test_mcp_project_dir_to_workspace_folder(tree):
    (tree / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"x": {"args": ["${CLAUDE_PROJECT_DIR}/s.py"]}}})
    )
    mcp = json.loads(render(tree)[".cursor/mcp.json"])
    assert mcp["mcpServers"]["x"]["args"] == ["${workspaceFolder}/s.py"]


def test_real_tree_renders():
    root = Path(__file__).resolve().parents[3]
    assert ".cursor/hooks.json" in registry()["cursor"].render(load_sources(root))
