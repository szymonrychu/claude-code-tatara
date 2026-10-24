"""Docs run from a consuming repo use ${CLAUDE_PLUGIN_ROOT} paths."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLANNER = ROOT / "agents" / "planner.md"
STEPS = ROOT / "skills" / "start-development" / "references" / "user-run-steps.md"
PREFIX = "${CLAUDE_PLUGIN_ROOT}/"


def _bare_commands(text):
    return re.findall(r"(?<!/)(?:python3 (?:scripts|skills)/|node workflows/)\S*", text)


def test_planner_paths_prefixed():
    t = PLANNER.read_text()
    assert _bare_commands(t) == []
    assert PREFIX + "scripts/lib/workbench.py" in t
    assert not re.search(r"(?<![/\w])skills/start-development/", t)
    assert PREFIX + "skills/start-development/SKILL.md" in t


def test_user_run_steps_paths_prefixed():
    t = STEPS.read_text()
    assert _bare_commands(t) == []
    assert t.count(PREFIX + "skills/start-development/scripts/user-run-step.py") == 2


def test_skill_paths_prefixed():
    t = (ROOT / "skills" / "start-development" / "SKILL.md").read_text()
    assert _bare_commands(t) == []
    assert PREFIX + "skills/start-development/scripts/ticket.py" in t
