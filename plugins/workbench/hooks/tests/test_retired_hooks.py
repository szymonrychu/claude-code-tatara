"""verify-recorder and subagent-commit-guard are retired: nothing may wire or serve them."""

import json
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS))

from lib import core  # noqa: E402

PLUGIN_JSON = HOOKS.parent / ".claude-plugin" / "plugin.json"
RETIRED = ("verify-recorder", "subagent-commit-guard")


def test_core_registers_only_the_guards():
    assert sorted(core.HOOKS) == ["guard-bash", "protect-files"]


def test_core_has_no_stop_event_or_block_action():
    assert core.EVENTS == ("pre-tool", "post-tool")
    assert core.ACTIONS == ("allow", "deny")


@pytest.mark.parametrize(
    "name",
    ["verify_recorder", "write_verify_record", "subagent_commit_guard", "collect_worktrees"],
)
def test_core_dropped_retired_functions(name):
    assert not hasattr(core, name)


def test_plugin_json_wires_no_retired_hook():
    text = PLUGIN_JSON.read_text()
    for name in RETIRED:
        assert name not in text
    hooks = json.loads(text)["hooks"]
    assert "PostToolUseFailure" not in hooks
    assert "PostToolUse" in hooks and "SubagentStop" in hooks


@pytest.mark.parametrize("name", RETIRED)
def test_retired_hook_scripts_are_gone(name):
    assert not (HOOKS / f"{name}.py").exists()
