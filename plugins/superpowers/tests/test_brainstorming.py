"""Pins the brainstorming adaptation: discovery subagents, one opus plan-writer, one gate."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_checks import SKILLS, flat, problems, skill_text  # noqa: E402

NAME = "brainstorming"


def test_structure():
    assert problems(NAME) == []


def test_size_the_work_kept():
    text = flat((SKILLS / NAME / "SKILL.md").read_text())
    assert "## Size the Work" in text
    assert "| Size |" in text


def test_discovery_lanes_are_opus_subagents_ending_in_plan_inputs():
    text = flat(skill_text(NAME))
    for lane in (
        "workbench:codebase-cartographer",
        "workbench:start-research",
        "research-code-internal",
    ):
        assert lane in text
    assert "opus" in text
    assert "## Plan inputs" in text
    for entry in ("`reuse`", "`do-not-build`", "`fix-as-ac`", "`ideas`"):
        assert entry in text


def test_ticket_check_and_new_through_the_plugin_script():
    text = flat(skill_text(NAME))
    assert "${CLAUDE_PLUGIN_ROOT}/scripts/ticket.py" in text
    assert "ticket.py check --title" in text
    assert "ticket.py new --title" in text


def test_one_opus_plan_writer_fills_the_template():
    skill = flat((SKILLS / NAME / "SKILL.md").read_text())
    prompt = flat((SKILLS / NAME / "plan-writer-prompt.md").read_text())
    assert "plan-writer-prompt.md" in skill
    assert "templates/plan.md" in prompt
    for section in (
        "What and why",
        "scope ladder",
        "recommended rung",
        "Non-goals",
        "Design",
        "Decisions",
        "(my call)",
        "[recommended: ",
        "Research",
        "Irreversible operations",
    ):
        assert section in prompt, section
    assert "docs(plan): <plan> plan" in prompt
    assert "opus" in skill


def test_plan_writer_prompt_carries_both_modes():
    prompt = flat((SKILLS / NAME / "plan-writer-prompt.md").read_text())
    assert "## Mode: plan" in prompt
    assert "## Mode: implementation" in prompt
    assert "docs(plan): <plan> implementation plan" in prompt


def test_hard_gate_and_one_batched_gate():
    text = flat((SKILLS / NAME / "SKILL.md").read_text())
    assert "<HARD-GATE>" in text
    assert (
        "nothing is built until the user picks a rung and answers the open questions"
        in text.lower()
    )
    assert "ONE gate" in text


def test_builder_check_kept():
    assert (SKILLS / NAME / "builder-check-prompt.md").is_file()
    assert "builder-check-prompt.md" in (SKILLS / NAME / "SKILL.md").read_text()


def test_dropped_upstream_parts_absent():
    text = flat(skill_text(NAME))
    assert "Visual Companion" not in text
    assert "visual-companion" not in text
    assert "docs/superpowers/specs" not in text
    assert "second approval" not in text.lower()
    assert not (SKILLS / NAME / "visual-companion.md").exists()
    assert not (SKILLS / NAME / "scripts").exists()
