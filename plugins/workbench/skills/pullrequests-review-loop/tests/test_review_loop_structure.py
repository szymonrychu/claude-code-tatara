"""The review loop judges bot findings through the shared review checklist."""

from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


def test_judging_uses_the_review_checklist():
    text = SKILL.read_text()
    for needle in (
        "references/review-checklist.md",
        "missing",
        "extra",
        "wrong",
        "quality",
        "evidence",
        "declined",
        "not certain",
        "start-review",
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
