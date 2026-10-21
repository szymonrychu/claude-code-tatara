"""The plugin lint task must gate the hook code with ruff."""

from pathlib import Path

import tomllib

PLUGIN = Path(__file__).resolve().parents[2]


def test_lint_task_runs_ruff_over_hooks():
    tasks = tomllib.loads((PLUGIN / ".mise.toml").read_text())["tasks"]
    ruff = [c for c in tasks["lint"]["run"] if c.startswith("ruff check")]
    assert ruff, "lint task has no ruff check"
    assert "hooks" in ruff[0].split()
