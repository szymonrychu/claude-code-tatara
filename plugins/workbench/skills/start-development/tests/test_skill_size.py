"""SKILL.md is loaded whole on every trigger: at most 150 lines, every reference it names exists."""

import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
MAX_LINES = 150
KEPT = (
    "tickets.md",
    "worktrees.md",
    "non-negotiables.md",
    "hooks.md",
    "merge-hosts.md",
    "user-run-steps.md",
    "workbench-config.md",
)


def test_skill_md_within_line_cap():
    n = len((SKILL_DIR / "SKILL.md").read_text().splitlines())
    assert n <= MAX_LINES, f"SKILL.md is {n} lines, cap {MAX_LINES}"


def test_named_references_exist():
    text = (SKILL_DIR / "SKILL.md").read_text()
    named = set(re.findall(r"references/([a-z-]+\.md)", text))
    assert named, "SKILL.md names no reference"
    for name in named:
        assert (SKILL_DIR / "references" / name).is_file(), name


def test_every_kept_reference_is_linked_from_skill():
    text = (SKILL_DIR / "SKILL.md").read_text()
    for name in KEPT:
        assert (SKILL_DIR / "references" / name).is_file(), name
        assert f"references/{name}" in text, name
