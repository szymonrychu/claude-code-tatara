"""Pins finishing-a-development-branch: one worktree-merger lands the plan, no options menu."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_checks import SKILLS, flat, problems  # noqa: E402

NAME = "finishing-a-development-branch"


def text() -> str:
    return flat((SKILLS / NAME / "SKILL.md").read_text())


def test_structure():
    assert problems(NAME) == []


def test_one_worktree_merger_with_the_absolute_ticket_path():
    t = text()
    assert "one `workbench:worktree-merger` (sonnet)" in t
    assert "absolute ticket.py path" in t


def test_meta_mode_closes_through_ticket_close():
    t = text()
    assert "ticket.py close <plan> --verify '<final verify>'" in t
    assert "fast-forward" in t
    assert "only when" in t


def test_component_mode_merges_the_moment_it_is_green():
    t = text()
    for skill in (
        "git-worktrees-commit",
        "git-worktrees-push",
        "pullrequests-update",
        "pullrequests-watch",
    ):
        assert f"`{skill}`" in t, skill
    assert "the moment it is green, mergeable and review-clean" in t


def test_plan_moves_to_done_and_trees_are_reaped():
    t = text()
    assert "ticket.py move <plan> done" in t
    assert "ticket.py reap --plan <plan>" in t


def test_one_short_closing_message_relays_the_recommendations():
    t = text()
    assert "one closing message" in t.lower()
    assert "three lines" in t
    assert "retro.md" in t
    assert "Recommendations" in t


def test_options_menu_absent():
    t = text()
    assert "Option 1" not in t
    assert "Discard" not in t
    assert "keep the branch as-is" not in t.lower()
    assert "Which option?" not in t
