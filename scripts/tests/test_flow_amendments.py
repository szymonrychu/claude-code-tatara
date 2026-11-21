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


def test_review_item():
    assert "13. **Review.**" in TEXT
    for phrase in ("/code-review", "workbench:spec-reviewer", "superpowers:receiving-code-review"):
        assert phrase in TEXT
    item4 = TEXT.split("4. **Final reviewer.**")[1].split("5. **")[0]
    assert "workbench:spec-reviewer" in item4


def test_spec_reviewer_agent_writes_only_retro():
    text = (RULE.parents[1] / "agents/spec-reviewer.md").read_text()
    front = text.split("---")[1]
    assert "name: spec-reviewer" in front
    assert "model: sonnet" in front
    tools = next(ln for ln in front.splitlines() if ln.startswith("tools:"))
    assert "Edit" not in tools
    assert "Write" in tools
    assert "exactly one file, the retro path" in text
    assert "Verdict: PASS|FAIL" in text
