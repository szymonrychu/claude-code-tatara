import json
import os
from pathlib import Path

import pytest
from harness.emit import registry
from harness.sources import load_sources
from harness.targets import antigravity
from harness.targets.antigravity import AntigravityError

GOLDEN = Path(__file__).parent / "golden" / "antigravity"


def render(tree):
    return registry()["antigravity"].render(load_sources(tree))


def test_registered():
    assert registry()["antigravity"].target == "antigravity"


def test_golden(tree):
    out = render(tree)
    if os.environ.get("BLESS_GOLDEN"):
        for rel, text in out.items():
            (GOLDEN / rel).parent.mkdir(parents=True, exist_ok=True)
            (GOLDEN / rel).write_text(text)
    expected = {str(p.relative_to(GOLDEN)): p.read_text() for p in GOLDEN.rglob("*") if p.is_file()}
    assert out == expected


def test_rule_triggers(tree):
    out = render(tree)
    py = out[".agents/rules/python.md"]
    assert py.startswith("---\ntrigger: glob\nglobs: ")
    assert "**/*.py" in py and "**/pyproject.toml" in py
    assert out[".agents/rules/always.md"].startswith("---\ntrigger: always_on\n---\n")


def test_unknown_trigger_fails():
    with pytest.raises(AntigravityError, match="trigger"):
        antigravity.check_trigger("always", "sometimes")


def test_agents_default_model_inherit(tree):
    out = render(tree)
    scout = out[".agents/agents/scout.md"]
    assert "name: scout\n" in scout and "model: inherit\n" in scout
    assert "tools" not in scout.split("---")[1]


def test_agent_body_rewritten(tree):
    (tree / "plugins/core/agents/scout.md").write_text(
        "---\nname: scout\ndescription: d\n---\nRun ${CLAUDE_PLUGIN_ROOT}/x.py via core:alpha.\n"
    )
    body = render(tree)[".agents/agents/scout.md"]
    assert "plugins/core/x.py" in body and "CLAUDE_PLUGIN_ROOT" not in body
    assert "core:alpha" not in body


def test_agent_may_mention_the_variable_name_in_prose(tree):
    (tree / "plugins/core/agents/scout.md").write_text(
        "---\nname: scout\ndescription: d\n---\nNever expand CLAUDE_PLUGIN_ROOT; it is unset.\n"
    )
    assert "CLAUDE_PLUGIN_ROOT" in render(tree)[".agents/agents/scout.md"]


def test_hooks_json(tree):
    hooks = json.loads(render(tree)[".agents/hooks.json"])["hooks"]
    pre = hooks["PreToolUse"]
    assert [g["matcher"] for g in pre] == [
        "run_command",
        "write_to_file|replace_file_content|multi_replace_file_content",
    ]
    cmd = pre[0]["hooks"][0]
    assert cmd["command"] == (
        "python3 plugins/core/hooks/adapter.py --harness antigravity "
        "--event pre-tool --hook guard-bash"
    )
    assert cmd["timeout"] == 10
    stop = hooks["Stop"][0]["hooks"][0]
    assert "--event stop --hook subagent-commit-guard" in stop["command"]
    blob = json.dumps(hooks)
    for claude_only in ("verify-recorder", "bash-output-filter", "format-file"):
        assert claude_only not in blob


def test_mcp_server_url(tree):
    mcp = json.loads(render(tree)[".agents/mcp_config.json"])
    assert mcp["mcpServers"]["docs"] == {"serverUrl": "https://example.invalid/mcp"}
    assert "url" not in mcp["mcpServers"]["docs"]


def test_no_mcp_file_without_mcp(tree):
    (tree / ".mcp.json").unlink()
    assert ".agents/mcp_config.json" not in render(tree)


def test_no_skills_written(tree):
    assert not [p for p in render(tree) if p.startswith(".agents/skills/")]


def test_agents_md_cap(tree):
    (tree / "AGENTS.md").write_text("x" * 24001)
    with pytest.raises(AntigravityError, match="24,000"):
        render(tree)
    (tree / "AGENTS.md").write_text("x" * 24000)
    render(tree)


def test_agents_md_cap_counts_synced_rules_block(tree):
    # Raw file under the cap, but the generated rules block pushes the synced file over it.
    rules = tree / "plugins/workbench/rules"
    rules.mkdir(parents=True, exist_ok=True)
    (rules / "tdd.md").write_text("# T\n" + "rule line\n" * 600)
    (tree / "AGENTS.md").write_text("x" * 20000)
    with pytest.raises(AntigravityError, match="24,000"):
        render(tree)
