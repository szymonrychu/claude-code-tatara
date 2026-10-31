"""Pins the discipline skills: TDD, verification, receiving review, parallel dispatch."""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_checks import SKILLS, flat, problems, skill_text  # noqa: E402

NAMES = (
    "test-driven-development",
    "verification-before-completion",
    "receiving-code-review",
    "dispatching-parallel-agents",
)


@pytest.mark.parametrize("name", NAMES)
def test_structure(name):
    assert problems(name) == []


def test_tdd_keeps_its_iron_law_and_good_tests_reference():
    t = flat(skill_text("test-driven-development"))
    assert "NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST" in t
    assert "Red-Green-Refactor" in t
    assert "[writing-good-tests.md](writing-good-tests.md)" in t
    assert (SKILLS / "test-driven-development" / "writing-good-tests.md").is_file()


def test_verification_keeps_its_iron_law():
    t = flat(skill_text("verification-before-completion"))
    assert "NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE" in t
    assert "The Gate Function" in t


def test_receiving_review_routes_pr_threads_and_caps_rounds():
    t = flat(skill_text("receiving-code-review"))
    assert "`pullrequests-review-loop`" in t
    assert "PR review threads" in t
    assert "two-round cap" in t
    assert "at most two fix rounds" in t


def test_dispatching_sets_the_model_on_every_dispatch():
    raw = skill_text("dispatching-parallel-agents")
    t = flat(raw)
    assert "every dispatch sets the model explicitly" in t
    assert "AGENTS.md ground rule 2" in t
    for tier in ("research opus", "implementation sonnet", "review sonnet"):
        assert tier in t, tier
    dispatches = re.findall(r"^Subagent \(.*$", raw, flags=re.MULTILINE)
    assert dispatches
    for line in dispatches:
        assert "model: " in line, line
