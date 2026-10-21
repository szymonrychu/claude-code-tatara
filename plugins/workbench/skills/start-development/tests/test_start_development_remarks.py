"""start-development routes to the planner, relaunch, multi-epic, suite and deploy tools."""

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


def test_phase_three_dispatches_planner():
    check(
        "## Phase 3 - Plan doc and tasks",
        [
            "workbench:planner",
            "{epic, briefs[], userDecisions[], relatedEpics[]}",
            "overlapIgnore",
            "references/workbench-config.md",
        ],
    )


def test_gate_batches_questions_and_records_decisions():
    check("## The gate", ["ticket.py questions", "every todo epic", "ticket.py decide"])


def test_phase_four_uses_relaunch_tools():
    check(
        "## Phase 4 - Execute",
        [
            "ticket.py args",
            "heartbeat.py --run <id>",
            "ticket.py continue",
            "--accept",
            "ticket.py rule",
            "ticket.py reap --epic <epic> --task <id>",
            "ticket.py amend",
            "ticket.py facts",
            "references/multi-epic.md",
        ],
    )


def test_phase_five_suites_from_config():
    check("## Phase 5 - Verify", ["suites", ".claude/workbench.json"])


def test_phase_six_deploy_hook_and_user_run_steps():
    check("## Phase 6 - Merge", ["deploy-hook.py", "deploy", "references/user-run-steps.md"])


def test_multi_epic_reference():
    text = flat((SD / "references" / "multi-epic.md").read_text())
    for n in [
        "ticket.py contract list",
        "ticket.py contract add",
        "graph --todo",
        "ticket.py roadmap",
        "concurrently",
        "when a run lands",
        "one epic per run",
    ]:
        assert n in text, n


def test_epic_worktrees_remove_reaps_one_task():
    text = (ROOT / "skills" / "epic-worktrees-remove" / "SKILL.md").read_text()
    assert "reap --epic <epic> --task <id>" in text


def test_skill_line_cap():
    assert len((SD / "SKILL.md").read_text().splitlines()) <= 470


def test_skill_routes_new_tools():
    text = flat(sd_text(SD / "SKILL.md"))
    for n in [
        "workbench:planner",
        "ticket.py args",
        "ticket.py continue",
        "ticket.py rule",
        "heartbeat.py --run <id>",
        "ticket.py questions",
        "ticket.py decide",
    ]:
        assert n in text, n


def test_skill_suites_deploy_user_run():
    text = flat(sd_text(SD / "SKILL.md"))
    for n in ["suites", ".claude/workbench.json", "deploy-hook.py", "references/user-run-steps.md"]:
        assert n in text, n


def test_multi_epic_has_running_concurrently_section():
    text = (SD / "references" / "multi-epic.md").read_text()
    assert "\n## Running epics concurrently\n" in text
