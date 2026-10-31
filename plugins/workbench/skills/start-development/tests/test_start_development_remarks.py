"""start-development routes to the plan-writer, plan-run, the deploy tools and the config."""

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


def test_phase_two_dispatches_plan_writer():
    check(
        "## Phase 2 - Plan",
        ["workbench:plan-writer", "{plan, briefs[]}", "docs(plan): <plan> plan", "opus"],
    )


def test_phase_one_ends_in_plan_inputs():
    check("## Phase 1 - Discovery", ["Plan inputs", "reuse", "do-not-build", "fix-as-ac", "ideas"])


def test_phase_four_names_the_loop_tools():
    check(
        "## Phase 4 - Run",
        ["plan-run", "ticket.py move <plan> in-progress", "ticket.py close <plan>", "retro.md"],
    )


def test_phase_four_deploy_hook_and_user_run_steps():
    check("## Phase 4 - Run", ["deploy-hook.py", "deploy", "references/user-run-steps.md"])


def test_config_keys_are_read_by_the_right_readers():
    cfg = flat((SD / "references" / "workbench-config.md").read_text())
    assert "read by the plan-writer" in cfg
    assert "Read by worktree-merge only" in cfg
    assert "planner" not in cfg and "epic" not in cfg.lower()


def test_skill_line_cap():
    assert len(TEXT.splitlines()) <= 150
