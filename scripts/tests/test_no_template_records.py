"""The published template ships no plans, research or handoff records."""

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


def test_no_plan_tree_tracked():
    assert _tracked("docs/plans") == []


def test_no_briefs_or_handoffs_tracked():
    assert _tracked("docs/research", "docs/handoffs") == []
