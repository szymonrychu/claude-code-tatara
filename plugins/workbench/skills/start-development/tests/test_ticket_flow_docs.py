"""start-development runs on tickets: the prose names the ticket.py commands in each phase."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SD = ROOT / "skills" / "start-development"


_MOVED = ("phases-1-3.md", "phase-4-execute.md", "phases-5-7.md", "non-negotiables.md")


def sd_text(skill):
    """SKILL.md plus the reference files its blocks moved to. References come first, so a section
    heading resolves to its full text rather than to the pointer left in SKILL.md."""
    refs = skill.parent / "references"
    return "\n".join([*((refs / n).read_text() for n in _MOVED), skill.read_text()])


def flat(text):
    return re.sub(r"\s+", " ", text)


def section(heading):
    text = sd_text(SD / "SKILL.md")
    start = text.index(heading)
    end = text.find("\n## ", start + 1)
    return flat(text[start:] if end == -1 else text[start:end])


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
            "user's input",
            "research",
            "scope discussion",
        ],
    )


def test_phase_three_writes_tasks():
    check(
        "## Phase 3 - Plan doc and tasks",
        [
            "ticket.py new-task",
            "<epic dir>/approvals.json",
            "validate-tasks.mjs --epic <epic dir>",
            "lean path",
            "no design.md",
        ],
    )
    body = section("## Phase 3 - Plan doc and tasks")
    assert "templates/plan.md" not in body
    assert "--plan <plan.md>" not in body


def test_gate_approves_several_epics():
    check("## The gate", ["several epics", "one plan-execute run per epic"])


def test_phase_four_runs_per_epic():
    check(
        "## Phase 4 - Execute",
        [
            "ticket.py move <epic> in-progress",
            "ticket.py worktrees <epic>",
            "ticket.py tasks <epic> --out",
            "named-copy.mjs plan-execute <epic>",
            "--args",
            "args.epic",
            "integration branch",
            "epic slug",
            "ticket.py apply-run",
            "`move in-progress` creates",
            "integration tree",
            "land-failed",
            "ticket.py worktrees <epic> --integration",
            "--base <epic>",
        ],
    )


def test_close_order_and_landing_docs():
    t = flat((SD / "references" / "phases-5-7.md").read_text())
    for needle in (
        "prints no MERGE line",
        "ticket.py close <epic> --verify",
        "rebases `<epic>` onto main",
        "fast-forwards main",
        "pre-fast-forward SHA",
        "`close.json`",
        "ticket.py move <epic> done",
    ):
        assert needle in t, needle
    assert "landed" in flat((SD / "references" / "run-handback.md").read_text())
    assert "forkPoint" in flat((SD / "references" / "run-handback.md").read_text())
    assert "own integration tree" in flat((SD / "references" / "multi-epic.md").read_text())


def test_phases_six_and_seven_close_the_epic():
    for h in ("## Phase 6 - Merge", "## Phase 7 - Record"):
        check(h, ["ticket.py path <epic> record", "epic-move", "epic-worktrees-remove"])


def test_ticket_commits_its_own_changes():
    t = flat(sd_text(SD / "SKILL.md"))
    assert "chore(ticket): <epic> <event>" in t
    assert "the orchestrator commits them" in t


def test_approvals_reference():
    t = flat((SD / "references" / "approvals.md").read_text())
    assert "<epic dir>/approvals.json" in t and "task slugs" in t
    assert "validate-tasks.mjs --epic <epic dir>" in t
    assert "--plan <plan.md>" not in t


def test_start_development_names_epic_skills():
    text = sd_text(SD / "SKILL.md")
    for needle in (
        "epic-create",
        "epic-task-create",
        "epic-move",
        "epic-worktrees-remove",
        "workbench:implementer",
    ):
        assert needle in text, needle


def test_readme_names_epic_skills():
    readme = (ROOT / "README.md").read_text()
    for name in ("epic-create", "epic-task-create", "epic-move", "epic-worktrees-remove"):
        assert name in readme, name
