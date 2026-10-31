"""The review loop judges bot findings through vanilla superpowers:receiving-code-review."""

from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


def test_judging_defers_to_receiving_code_review():
    text = SKILL.read_text()
    assert "review-" + "checklist" not in text
    for needle in (
        "superpowers:receiving-code-review",
        "missing",
        "extra",
        "wrong",
        "quality",
        "evidence",
        "declined",
        "not certain",
        "requesting-code-review",
        "critical",
        "high",
        "medium",
    ):
        assert needle in text, needle


def test_code_review_is_gone_and_ascii():
    text = SKILL.read_text()
    assert "/code-review" not in text
    text.encode("ascii")


def test_skill_names_pullrequests_watch():
    text = SKILL.read_text()
    assert "name: pullrequests-review-loop" in text
    assert "pullrequests-watch" in text
    assert "GitHub only" in text


def test_names_no_epic_and_the_merge_step_is_finishing_a_branch():
    import re

    text = " ".join(SKILL.read_text().split())
    assert not re.search(r"\bepics?\b", text, re.I)
    assert "worktree-" + "merger" not in text
    assert "superpowers:finishing-a-development-branch" in text
