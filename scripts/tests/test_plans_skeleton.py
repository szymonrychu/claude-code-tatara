"""The published template ships empty plan folders and no research or handoff records."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _tracked(*paths: str) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "--", *paths],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return out.split()


def test_plan_folders_tracked():
    tracked = set(_tracked("docs/plans"))
    for folder in ("todo", "in-progress", "done"):
        assert f"docs/plans/{folder}/.gitkeep" in tracked


def test_no_briefs_or_handoffs_tracked():
    assert _tracked("docs/research", "docs/handoffs") == []
