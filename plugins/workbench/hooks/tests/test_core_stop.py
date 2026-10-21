"""Drive the post-tool and stop guards through `decide` in temp git worktrees."""

import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS))

from lib.core import NormalizedEvent, decide, from_claude_payload  # noqa: E402
from worktree_lib import record_path  # noqa: E402


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def worktree(tmp_path: Path) -> Path:
    path = tmp_path / "wb" / ".claude" / "worktrees" / "t1-core"
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "t@example.com")
    git(path, "config", "user.name", "T")
    (path / "seed.txt").write_text("seed\n")
    git(path, "add", "seed.txt")
    git(path, "commit", "-qm", "seed")
    return path


def post(command: str, cwd, hook_event: str = "PostToolUse") -> NormalizedEvent:
    return from_claude_payload(
        {
            "hook_event_name": hook_event,
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": str(cwd),
        },
        "post-tool",
    )


def stop(cwd, **extra) -> NormalizedEvent:
    return from_claude_payload({"cwd": str(cwd), **extra}, "stop")


# --- verify-recorder ----------------------------------------------------------


def test_verify_recorder_record(worktree: Path):
    decision = decide("verify-recorder", post(f"cd {worktree} && pytest tests/", "/"))
    assert decision.action == "allow"
    assert decision.data["command"] == "pytest tests/"
    assert decision.data["head"] == git(worktree, "rev-parse", "HEAD")
    assert decision.data["dirty"] is False
    assert decision.data["passed"] is True
    assert decision.data["at"]
    assert not record_path(str(worktree)).exists()  # decide has no side effect


def test_recorder_marks_dirty_and_failed(worktree: Path):
    (worktree / "x.txt").write_text("x")
    data = decide("verify-recorder", post("pytest", worktree, "PostToolUseFailure")).data
    assert data["dirty"] is True
    assert data["passed"] is False


@pytest.mark.parametrize(
    "event",
    [
        lambda wt: post("pytest", wt, "PreToolUse"),
        lambda wt: post("ls -la", wt),
        lambda wt: post("pytest", wt.parent.parent.parent),  # not an agent worktree
        lambda wt: NormalizedEvent(
            event="pre-tool", tool_kind="shell", command="pytest", cwd=str(wt)
        ),
        lambda wt: from_claude_payload({"tool_name": "Edit", "cwd": str(wt)}, "post-tool"),
    ],
)
def test_recorder_records_nothing_otherwise(worktree: Path, event):
    decision = decide("verify-recorder", event(worktree))
    assert decision.action == "allow"
    assert decision.data == {}


# --- subagent-commit-guard ------------------------------------------------------


def test_guard_blocks_a_dirty_worktree(worktree: Path):
    (worktree / "a.txt").write_text("a")
    decision = decide("subagent-commit-guard", stop(worktree))
    assert decision.action == "block"
    assert "1 uncommitted file" in decision.reason
    assert str(worktree) in decision.reason


def test_guard_blocks_a_stale_verification(worktree: Path):
    record = decide("verify-recorder", post("pytest", worktree)).data
    path = record_path(str(worktree))
    import json

    path.write_text(json.dumps(record))
    (worktree / "b.txt").write_text("b")
    git(worktree, "add", "b.txt")
    git(worktree, "commit", "-qm", "later")
    decision = decide("subagent-commit-guard", stop(worktree))
    assert decision.action == "block"
    assert "last verification ran on" in decision.reason
    assert "Re-run pytest" in decision.reason


def test_guard_allows_clean_and_fresh(worktree: Path):
    assert decide("subagent-commit-guard", stop(worktree)).action == "allow"


def test_guard_allows_when_already_fired(worktree: Path):
    (worktree / "a.txt").write_text("a")
    event = stop(worktree, stop_hook_active=True)
    assert decide("subagent-commit-guard", event).action == "allow"


def test_guard_ignores_non_stop_events(worktree: Path):
    (worktree / "a.txt").write_text("a")
    event = NormalizedEvent(event="pre-tool", tool_kind="shell", cwd=str(worktree))
    assert decide("subagent-commit-guard", event).action == "allow"


def test_commit_guard_decisions(worktree: Path):
    import json

    assert decide("subagent-commit-guard", stop(worktree)).action == "allow"
    (worktree / "a.txt").write_text("a")
    dirty = decide("subagent-commit-guard", stop(worktree))
    assert dirty.action == "block"
    assert "1 uncommitted file" in dirty.reason
    git(worktree, "add", "a.txt")
    git(worktree, "commit", "-qm", "a")
    record = decide("verify-recorder", post("pytest", worktree)).data
    record_path(str(worktree)).write_text(json.dumps(record))
    assert decide("subagent-commit-guard", stop(worktree)).action == "allow"
    (worktree / "b.txt").write_text("b")
    git(worktree, "add", "b.txt")
    git(worktree, "commit", "-qm", "b")
    stale = decide("subagent-commit-guard", stop(worktree))
    assert stale.action == "block"
    assert "last verification ran on" in stale.reason
