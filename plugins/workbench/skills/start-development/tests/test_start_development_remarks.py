"""start-development routes to the planner, the epic-run loop, the suites and the deploy tools."""

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


def test_phase_three_dispatches_planner():
    check(
        "## Phase 3 - Tasks",
        [
            "workbench:planner",
            "{epic, briefs[], userDecisions[]}",
            "ticket.py lint <epic>",
            "builder check",
            "general-purpose agent on sonnet",
            "only the questions",
            "one test file's worth of behaviour, at most 8 files",
            "more than five files",
        ],
    )


def test_gate_batches_questions():
    check("## The gate", ["ticket.py questions", "every todo epic", "as one batch, numbered"])


def test_phase_four_names_the_loop_tools():
    check(
        "## Phase 4 - Execute",
        ["epic-run", "ticket.py tasks <epic>", "ticket.py task <epic> <task>", "ticket.py amend"],
    )


def test_phase_five_suites_from_config():
    check("## Phase 5 - Epic review", ["suites", ".claude/workbench.json", "mise run lint"])


def test_phase_six_deploy_hook_and_user_run_steps():
    check(
        "## Phase 6 - Close or merge",
        ["deploy-hook.py", "deploy", "references/user-run-steps.md"],
    )


def test_skill_line_cap():
    assert len(TEXT.splitlines()) <= 150
