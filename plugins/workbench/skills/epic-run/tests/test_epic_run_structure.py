import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
ROOT = Path(__file__).resolve().parents[3]
DESCRIPTION = (
    "Execute one planned epic: claim it, run its tasks in dependency order through one "
    "implementer and one reviewer each with at most two fix rounds, audit scope, close. "
    "Use after the gate of start-development or to run an epic planned in another session."
)


def _frontmatter():
    text = SKILL.read_text()
    assert text.startswith("---\n")
    end = text.index("\n---", 4)
    fm = {}
    for line in text[4:end].splitlines():
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip().strip('"')
    return fm


def test_skill_structure():
    fm = _frontmatter()
    assert fm["name"] == "epic-run"
    assert fm["description"] == DESCRIPTION
    text = re.sub(r"\s+", " ", SKILL.read_text())
    for term in (
        "start-development",
        "phase 4",
        "ticket.py tasks",
        "ticket.py task",
        "workbench:implementer",
        "workbench:reviewer",
        "SendMessage",
        "ticket.py lint",
        "--verified-head",
        "escalated",
        "discovered",
        "undelivered",
    ):
        assert term in text, f"SKILL.md does not mention {term!r}"
    assert (ROOT / "agents" / "implementer.md").is_file()
    assert (ROOT / "agents" / "reviewer.md").is_file()
    assert (ROOT / "skills" / "start-development" / "SKILL.md").is_file()
    assert (ROOT / "skills" / "start-development" / "scripts" / "ticket.py").is_file()


def test_no_retired_words():
    text = SKILL.read_text()
    for word in ("plan-execute", "heartbeat", "Workflow(", "approvals"):
        assert word not in text, f"SKILL.md still contains {word!r}"
