"""Pins using-git-worktrees (the plan tree) and requesting-code-review (the whole-diff review)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_checks import SKILLS, flat, problems  # noqa: E402

WORKTREES = "using-git-worktrees"
REVIEW = "requesting-code-review"


def read(skill: str, name: str = "SKILL.md") -> str:
    return flat((SKILLS / skill / name).read_text())


def test_structure():
    assert problems(WORKTREES) == []
    assert problems(REVIEW) == []


def test_ticket_move_is_the_one_way_a_plan_tree_is_made():
    t = read(WORKTREES)
    assert "`ticket.py move <plan> in-progress`" in t
    assert "the one way a plan tree is made" in t
    assert "`ticket.py worktrees <plan> --refresh`" in t


def test_worktrees_drop_the_upstream_creation_paths():
    t = read(WORKTREES)
    assert "git worktree add" not in t
    assert ".worktrees/" not in t
    assert "Would you like me to set up an isolated worktree?" not in t


def test_review_dispatches_the_workbench_reviewer_with_code_reviewer_md():
    t = read(REVIEW)
    assert "`workbench:reviewer` (sonnet)" in t
    assert "[code-reviewer.md](code-reviewer.md)" in t
    assert "git diff <base>...HEAD" in t


def test_code_reviewer_holds_the_delivery_checklist():
    t = read(REVIEW, "code-reviewer.md")
    low = t.lower()
    assert "under-delivery" in low
    assert "over-delivery" in low
    assert "every agreed item" in t
    assert "no step covers" in t
    assert "references/review-checklist.md" in t
    assert "workbench" in t


def test_code_reviewer_ends_with_retro_on_a_pass():
    t = read(REVIEW, "code-reviewer.md")
    assert "retro.md" in t
    assert "templates/retro.md" in t
    assert "Recommendations" in t
    assert "retro.md" in t.split("## ")[-1]
