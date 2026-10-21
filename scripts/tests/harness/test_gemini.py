import json
from pathlib import Path

import pytest
from harness import emit
from harness.setup import PATH_RULE_TARGETS
from harness.sources import load_sources

GOLDEN = Path(__file__).parent / "golden" / "gemini"


def render(tree):
    return emit.registry()["gemini"].render(load_sources(tree))


def test_golden(tree):
    out = render(tree)
    expected = {str(p.relative_to(GOLDEN)): p.read_text() for p in GOLDEN.rglob("*") if p.is_file()}
    assert out == expected


def test_settings_shape(tree):
    s = json.loads(render(tree)[".gemini/settings.json"])
    assert s["context"]["fileName"] == ["AGENTS.md", "GEMINI.md"]
    hooks = s["hooks"]
    assert set(hooks) == {"BeforeTool", "AfterAgent"}
    cmds = {h["name"]: h for groups in hooks.values() for g in groups for h in g["hooks"]}
    assert set(cmds) == {"guard-bash", "protect-files", "subagent-commit-guard"}
    matchers = [g["matcher"] for g in hooks["BeforeTool"]]
    assert matchers == ["run_shell_command", "write_file|replace"]
    assert "matcher" not in hooks["AfterAgent"][0]
    for h in cmds.values():
        assert h["type"] == "command"
        assert isinstance(h["timeout"], int) and h["timeout"] >= 1000
        assert "adapter.py --harness gemini" in h["command"]
    assert "--event stop --hook subagent-commit-guard" in cmds["subagent-commit-guard"]["command"]


def test_claude_only_hooks_not_emitted(tree):
    text = render(tree)[".gemini/settings.json"]
    for name in ("verify-recorder", "bash-output-filter", "format-file"):
        assert name not in text


def test_mcp_http_becomes_httpurl(tree):
    s = json.loads(render(tree)[".gemini/settings.json"])
    assert s["mcpServers"] == {"docs": {"httpUrl": "https://example.invalid/mcp"}}


def test_no_mcp_no_key(tree):
    (tree / ".mcp.json").unlink()
    assert "mcpServers" not in json.loads(render(tree)[".gemini/settings.json"])


def test_stdio_and_sse_servers(tree):
    (tree / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "a": {"command": "npx", "args": ["x"], "env": {"K": "v"}},
                    "b": {"type": "sse", "url": "https://s.invalid/sse"},
                }
            }
        )
    )
    s = json.loads(render(tree)[".gemini/settings.json"])["mcpServers"]
    assert s["a"] == {"command": "npx", "args": ["x"], "env": {"K": "v"}}
    assert s["b"] == {"url": "https://s.invalid/sse"}


def test_agents_per_plugin_agent(tree):
    out = render(tree)
    scout = out[".gemini/agents/scout.md"]
    assert scout.startswith("---\nname: scout\n")
    assert "model: inherit\n" in scout
    assert "tools:" not in scout
    assert ".gemini/agents/helper.md" in out


def test_model_override(tree):
    (tree / ".claude/workbench.json").write_text(
        json.dumps(
            {"harness": {"targets": ["gemini"], "models": {"gemini": {"opus": "gemini-2.5-pro"}}}}
        )
    )
    out = render(tree)
    assert "model: gemini-2.5-pro\n" in out[".gemini/agents/scout.md"]
    assert "model: inherit\n" in out[".gemini/agents/helper.md"]


def test_agent_body_rewritten_no_unresolved_variable(tree):
    f = tree / "plugins/core/agents/scout.md"
    f.write_text(f.read_text() + "Run `${CLAUDE_PLUGIN_ROOT}/hooks/x.py` via core:alpha.\n")
    body = render(tree)[".gemini/agents/scout.md"]
    assert "plugins/core/hooks/x.py" in body
    assert "via alpha." in body
    assert "CLAUDE_PLUGIN_ROOT" not in body


def test_unresolved_variable_rejected(tree):
    f = tree / "plugins/core/agents/scout.md"
    f.write_text(f.read_text() + "See ${CLAUDE_PLUGIN_DATA}/x and ${CLAUDE_PLUGIN_ROOTX}.\n")
    with pytest.raises(ValueError, match="CLAUDE_PLUGIN"):
        render(tree)


def test_gemini_gets_path_rules_block():
    assert "gemini" in PATH_RULE_TARGETS


def test_context_filename(tree):
    s = json.loads(render(tree)[".gemini/settings.json"])
    assert "AGENTS.md" in s["context"]["fileName"]


def test_stop_fallback_hook(tree):
    s = json.loads(render(tree)[".gemini/settings.json"])
    hook = s["hooks"]["AfterAgent"][0]["hooks"][0]
    assert hook["name"] == "subagent-commit-guard"
    assert "--event stop --hook subagent-commit-guard" in hook["command"]
