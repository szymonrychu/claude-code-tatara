"""Pins the writing-plans adaptation: implementation-plan.md for the agreed rung, no second gate."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_checks import SKILLS, flat, problems  # noqa: E402

NAME = "writing-plans"


def text() -> str:
    return flat((SKILLS / NAME / "SKILL.md").read_text())


def test_structure():
    assert problems(NAME) == []


def test_input_is_the_gate_answer_recorded_in_plan_md():
    t = text()
    assert "gate answer verbatim" in t
    assert "Agreed scope" in t
    assert "[answer: ...]" in t
    assert "`rung`" in t


def test_output_is_the_agreed_rung_only_from_the_template():
    t = text()
    assert "ticket.py path <plan> implementation" in t
    assert "templates/implementation-plan.md" in t
    assert "agreed rung only" in t


def test_chunks_and_steps_shape():
    t = text()
    assert "## Chunk <k>: <name> (model: <sonnet|opus>)" in t
    for field in ("Files", "Covers", "Test first", "Change", "Verify"):
        assert f"**{field}**" in t or f"{field}:" in t, field
    for section in ("Files to delete", "Final verify", "After merge"):
        assert section in t, section
    assert "docs(plan): <plan> implementation plan" in t
    assert "no second gate" in t.lower()


def test_upstream_sections_kept():
    t = text()
    assert "## File Structure" in t
    assert "## Task Right-Sizing" in t


def test_execution_choice_and_upstream_paths_absent():
    t = text()
    assert "Native" not in t
    assert "Subagent-driven" not in t
    assert "docs/superpowers/plans" not in t
    assert "superpowers:executing-plans" not in t
