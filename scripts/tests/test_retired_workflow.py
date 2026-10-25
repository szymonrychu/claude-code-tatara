"""Retirement test: the Workflow runtime and its watchers are gone from git."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

RETIRED = [
    "plugins/workbench/workflows",
    "plugins/workbench/skills/heartbeat",
    "plugins/workbench/scripts/hook-evidence.py",
    "plugins/workbench/scripts/tests/test_hook_evidence.py",
    "scripts/harness/fallbacks/plan-execute",
]


def test_workflow_runtime_retired():
    out = subprocess.run(
        ["git", "ls-files", *RETIRED],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    assert out.strip() == "", out
