"""The personal lint is a mise file task and the whole tracked tree passes it."""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "mise-tasks" / "lint" / "personal"


def test_task_exists_and_is_executable():
    assert TASK.is_file()
    assert os.access(TASK, os.X_OK)
    assert "scripts/check_personal.py" in TASK.read_text()


def test_tracked_tree_passes_personal_lint():
    proc = subprocess.run([str(TASK)], cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
