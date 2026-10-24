"""Retirement pin: the independent-verifier tooling stays removed."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

RETIRED = [
    "plugins/workbench/scripts/verify-task.py",
    "plugins/workbench/scripts/triage.py",
    "plugins/workbench/scripts/lib/claude_json.py",
    "plugins/workbench/agents/verifier.md",
    "plugins/workbench/scripts/tests/fixtures",
]


def test_verifier_tooling_retired():
    out = subprocess.run(
        ["git", "ls-files", *RETIRED], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    assert out.strip() == ""
