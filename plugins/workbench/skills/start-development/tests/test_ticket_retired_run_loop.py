"""Retirement pin: the run-loop and approval-ledger subcommands stay removed."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TICKET = ROOT / "plugins/workbench/skills/start-development/scripts/ticket.py"
REMOVED = [
    "apply-run",
    "args",
    "continue",
    "rule",
    "estimate",
    "facts",
    "decide",
    "contract",
    "graph",
]
KEPT = [
    "slug",
    "new-epic",
    "new-task",
    "check",
    "index",
    "existing",
    "tasks",
    "worktrees",
    "move",
    "stage",
    "review",
    "rename",
    "lint",
    "reap",
    "path",
    "amend",
    "close",
    "questions",
    "roadmap",
    "task",
]
CMDS = "plugins/workbench/skills/start-development/scripts/ticket_cmds"
KEPT_MODULES = {
    "__init__.py",
    "amend.py",
    "close_cmd.py",
    "questions.py",
    "roadmap.py",
    "task_cmd.py",
}


def _help_names() -> set[str]:
    out = subprocess.run(
        [sys.executable, str(TICKET), "--help"], capture_output=True, text=True, check=True
    ).stdout
    block = out.split("{", 1)[1].split("}", 1)[0]
    return set(block.split(","))


def test_run_loop_commands_retired():
    names = _help_names()
    assert not names & set(REMOVED)
    assert set(KEPT) <= names
    files = subprocess.run(
        [
            "git",
            "ls-files",
            CMDS,
            "plugins/workbench/scripts/lib/estimator.py",
            "plugins/workbench/scripts/lib/estimator.json",
            "plugins/workbench/scripts/tests/test_estimator.py",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert {Path(f).name for f in files if f.startswith(CMDS)} == KEPT_MODULES
    assert not [f for f in files if "estimator" in f]
