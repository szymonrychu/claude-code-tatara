import json
import os
import re
import shlex
from pathlib import Path

import pytest
from harness.emit import registry
from harness.sources import Agent, PluginSource, load_sources
from harness.targets.copilot import CopilotEmitter

GOLDEN = Path(__file__).parent / "golden" / "copilot"
REPO = Path(__file__).resolve().parents[3]


def render(tree):
    return CopilotEmitter().render(load_sources(tree))


def test_registered():
    assert isinstance(registry()["copilot"], CopilotEmitter)


def test_golden(tree):
    out = render(tree)
    if os.environ.get("UPDATE_GOLDEN"):
        for rel, text in out.items():
            (GOLDEN / rel).parent.mkdir(parents=True, exist_ok=True)
            (GOLDEN / rel).write_text(text)
    expected = {str(p.relative_to(GOLDEN)): p.read_text() for p in GOLDEN.rglob("*") if p.is_file()}
    assert out == expected


def test_instructions_apply_to(tree):
    out = render(tree)
    assert (
        'applyTo: "**/*.py,**/pyproject.toml"' in out[".github/instructions/python.instructions.md"]
    )
    assert 'applyTo: "**"' in out[".github/instructions/always.instructions.md"]
    assert "Use type hints." in out[".github/instructions/python.instructions.md"]


def test_agent_tools_and_model(tree):
    out = render(tree)
    scout = out[".github/agents/scout.agent.md"]
    assert 'tools: ["read", "search", "execute"]' in scout
    assert "model" not in scout.split("---")[1]
    assert "You are a scout." in scout
    assert 'tools: ["read", "execute"]' in out[".github/agents/helper.agent.md"]


def test_model_override_written(tree):
    cfg = tree / ".claude/workbench.json"
    cfg.write_text(
        json.dumps({"harness": {"targets": ["copilot"], "models": {"copilot": {"opus": "gpt-x"}}}})
    )
    assert 'model: "gpt-x"' in render(tree)[".github/agents/scout.agent.md"]


def test_unmapped_tools_dropped_and_deduped(tree):
    p = tree / "plugins/core/agents/scout.md"
    p.write_text(
        "---\nname: scout\ndescription: d\ntools: [Edit, Write, LSP, ToolSearch, Task, WebFetch]\n"
        "---\nbody\n"
    )
    assert 'tools: ["edit", "agent", "web"]' in render(tree)[".github/agents/scout.agent.md"]


def test_agent_body_rewritten(tree):
    p = tree / "plugins/core/agents/scout.md"
    p.write_text(
        "---\nname: scout\ndescription: d\n---\nRun ${CLAUDE_PLUGIN_ROOT}/x.py via workbench:foo.\n"
    )
    body = render(tree)[".github/agents/scout.agent.md"]
    assert "plugins/core/x.py via foo." in body
    assert "CLAUDE_PLUGIN_ROOT" not in body


def test_unresolved_variable_fails(tree):
    p = tree / "plugins/core/agents/scout.md"
    p.write_text("---\nname: scout\ndescription: d\n---\nUse ${CLAUDE_PLUGIN_DATA}/x.\n")
    with pytest.raises(ValueError, match="CLAUDE_PLUGIN_DATA"):
        render(tree)


def test_prompt_cap(tree):
    src = load_sources(tree)
    big = Agent("big", "d", None, (), "x" * 30_001)
    plug = PluginSource("core", src.plugins[0].root, agents=(big,))
    src = type(src)(**{**src.__dict__, "plugins": (plug,)})
    with pytest.raises(ValueError, match="30,000"):
        CopilotEmitter().render(src)
    ok = Agent("ok", "d", None, (), "x" * 30_000)
    plug = PluginSource("core", src.plugins[0].root, agents=(ok,))
    src = type(src)(**{**src.__dict__, "plugins": (plug,)})
    assert ".github/agents/ok.agent.md" in CopilotEmitter().render(src)


def test_hooks_call_adapter(tree):
    hooks = json.loads(render(tree)[".github/hooks/workbench.json"])
    assert hooks["version"] == 1
    assert set(hooks["hooks"]) == {"PreToolUse", "SubagentStop"}
    cmds = [e["bash"] for entries in hooks["hooks"].values() for e in entries]
    assert len(cmds) == 3
    assert not any("verify-recorder" in c or "format" in c for c in cmds)
    for entries in hooks["hooks"].values():
        for e in entries:
            assert e["timeoutSec"] > 0
            tokens = shlex.split(e["bash"])
            assert tokens[:2] == ["python3", "plugins/workbench/hooks/adapter.py"]
            assert (REPO / tokens[1]).is_file()
            assert tokens[2:4] == ["--harness", "copilot"]
    stop = hooks["hooks"]["SubagentStop"][0]["bash"]
    assert re.search(r"--event stop --hook subagent-commit-guard$", stop)


def test_vscode_mcp(tree):
    mcp = json.loads(render(tree)[".vscode/mcp.json"])
    assert mcp == {"servers": {"docs": {"type": "http", "url": "https://example.invalid/mcp"}}}


def test_no_mcp_no_file(tree):
    (tree / ".mcp.json").unlink()
    assert ".vscode/mcp.json" not in render(tree)
