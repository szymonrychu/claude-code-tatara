"""Pins the S-74 amendments to the superpowers-flow rule."""

from pathlib import Path

RULE = Path(__file__).resolve().parents[2] / "plugins/workbench/rules/superpowers-flow.md"
TEXT = RULE.read_text()


def test_task_classes_defined():
    for word in ("spike", "bounded", "architectural"):
        assert f"class:{word}" in TEXT


def test_items_1_to_9_numbering_kept():
    lines = TEXT.splitlines()
    for n, title in enumerate(
        [
            "Research first.",
            "One human gate.",
            "Paths.",
            "Final reviewer.",
            "The orchestrator never edits.",
            "Taskboard lifecycle.",
            "Specs on the server.",
            "Approved spec starts implementation.",
            "Approvals.",
        ],
        start=1,
    ):
        assert any(line.startswith(f"{n}. **{title}**") for line in lines)


def test_native_mechanics_item():
    for phrase in ("git status --porcelain", "git-worktrees-"):
        assert phrase in TEXT


def test_tdd_amendment():
    assert "12. **Tests earn their place.**" in TEXT
    for phrase in ("observable behaviour", "parametrise", "test count"):
        assert phrase in TEXT
