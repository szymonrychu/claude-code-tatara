"""Retirement pin: the run-loop, approval-ledger and task-machinery subcommands stay removed,
and the epic flow's files are gone from the index."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
TICKET = ROOT / "plugins/workbench/skills/start-development/scripts/ticket.py"
RUN_LOOP = ["apply-run", "args", "continue", "rule", "estimate", "facts", "decide", "contract"]
RUN_LOOP += ["graph"]
TASK_MACHINERY = [
    "new-epic",
    "new-task",
    "tasks",
    "task",
    "amend",
    "questions",
    "lint",
    "stage",
    "review",
    "actuals",
    "deltas",
    "retro",
    "roadmap",
    "index",
    "existing",
]
KEPT = ["slug", "new", "check", "path", "rename", "move", "worktrees", "close", "reap"]
PLUGIN = "plugins/workbench"
SD = f"{PLUGIN}/skills/start-development"
DELETED = [
    *(
        f"{PLUGIN}/skills/{d}"
        for d in (
            "epic-create",
            "epic-migrate",
            "epic-move",
            "epic-task-create",
            "epic-worktrees-remove",
        )
    ),
    *(f"{SD}/templates/{n}" for n in ("design.md", "epic.md", "record.md", "task.md")),
    *(
        f"{SD}/scripts/ticket_cmds/{n}.py"
        for n in (
            "actuals",
            "amend",
            "deltas",
            "questions",
            "retro",
            "roadmap",
            "task_cmd",
            "migrate",
        )
    ),
    *(
        f"{SD}/tests/{n}.py"
        for n in (
            "test_ticket_amend",
            "test_ticket_deltas",
            "test_ticket_lint",
            "test_ticket_questions",
            "test_ticket_reap_task",
            "test_ticket_retro",
            "test_ticket_roadmap",
            "test_ticket_task_status",
            "test_ticket_names",
            "test_ticket_overlap_ignore",
            "test_ticket_migrate_map",
            "test_ticket_migrate",
            "test_epic_skills_structure",
            "test_ticket_retired_run_loop",
        )
    ),
    f"{PLUGIN}/scripts/lib/estimator.py",
    f"{PLUGIN}/scripts/lib/estimator.json",
    f"{PLUGIN}/scripts/tests/test_estimator.py",
]


def _help_names() -> set[str]:
    out = subprocess.run(
        [sys.executable, str(TICKET), "--help"], capture_output=True, text=True, check=True
    ).stdout
    block = out.split("{", 1)[1].split("}", 1)[0]
    return set(block.split(","))


def test_kept_subcommands_are_listed():
    assert set(KEPT) <= _help_names()


@pytest.mark.parametrize("name", RUN_LOOP + TASK_MACHINERY)
def test_retired_subcommand_is_not_a_choice(name):
    assert name not in _help_names()
    r = subprocess.run([sys.executable, str(TICKET), name], capture_output=True, text=True)
    assert r.returncode == 2 and "invalid choice" in r.stderr


def test_ticket_py_imports_no_estimate_libraries():
    src = TICKET.read_text()
    assert "import calibration" not in src and "import agent_usage" not in src


@pytest.mark.parametrize("path", DELETED)
def test_retired_files_are_not_tracked(path):
    out = subprocess.run(
        ["git", "ls-files", "--", path], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    assert out == "", out
