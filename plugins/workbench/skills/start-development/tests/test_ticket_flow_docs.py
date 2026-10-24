"""start-development runs on tickets: the prose names the ticket.py commands in each phase."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SD = ROOT / "skills" / "start-development"
TEXT = (SD / "SKILL.md").read_text()


def flat(text):
    return re.sub(r"\s+", " ", text)


def section(heading):
    start = TEXT.index(heading)
    end = TEXT.find("\n## ", start + 1)
    return flat(TEXT[start:] if end == -1 else TEXT[start:end])


def check(heading, needles):
    body = section(heading)
    for n in needles:
        assert n in body, f"{heading!r} does not contain {n!r}"


def test_phase_two_creates_the_epic():
    check(
        "## Phase 2 - Design doc",
        [
            "ticket.py check",
            "ticket.py new-epic",
            "ticket.py path <epic> design",
            "templates/design.md",
            "(my call)",
            "architect-researcher",
        ],
    )


def test_phase_three_writes_tasks():
    check("## Phase 3 - Tasks", ["epic-task-create", "ticket.py lint <epic>", "lint: ok"])


def test_lean_size_has_no_design_doc():
    check("## Phase 0 - Size the work", ["Lean", "Full", "design.md", "ticket.py new-task"])


def test_gate_covers_several_epics():
    check("## The gate", ["several epics"])


def test_phase_four_claims_the_epic_and_records_each_task():
    check(
        "## Phase 4 - Execute",
        [
            "ticket.py move <epic> in-progress",
            "integration tree",
            "branch `<epic>`",
            "ticket.py tasks <epic>",
            "ticket.py task <epic> <task> --status done --verified-head <head>",
        ],
    )


def test_phases_six_and_seven_close_the_epic():
    check("## Phase 6 - Close or merge", ["epic-move", "epic-worktrees-remove", "worktree-merger"])
    check("## Phase 7 - Record", ["ticket.py path <epic> record", "record-writer", "three lines"])


def test_ticket_commits_its_own_changes():
    t = flat(TEXT)
    assert "chore(ticket): <epic> <event>" in t
    assert "the orchestrator commits them" in t


def test_start_development_names_epic_skills():
    for needle in (
        "epic-create",
        "epic-task-create",
        "epic-move",
        "epic-worktrees-remove",
        "epic-run",
        "workbench:implementer",
        "workbench:reviewer",
    ):
        assert needle in TEXT, needle


def test_readme_names_epic_skills():
    readme = (ROOT / "README.md").read_text()
    for name in (
        "epic-create",
        "epic-task-create",
        "epic-move",
        "epic-worktrees-remove",
        "epic-run",
    ):
        assert name in readme, name
