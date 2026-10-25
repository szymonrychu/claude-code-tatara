"""bash-output-filter's wrapper must be invisible to the verify recorder and commit guard."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS))
import worktree_lib as wl  # noqa: E402

spec = importlib.util.spec_from_file_location("bash_output_filter", HOOKS / "bash-output-filter.py")
bof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bof)

RECORDER = HOOKS / "verify-recorder.py"


def git(repo, *args):
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def worktree(tmp_path):
    path = tmp_path / "wb" / ".claude" / "worktrees" / "t12"
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "t@example.com")
    git(path, "config", "user.name", "T")
    (path / "seed.txt").write_text("seed\n")
    git(path, "add", "seed.txt")
    git(path, "commit", "-qm", "seed")
    return path


def test_unwrap_returns_original_command():
    original = "cd /x/.claude/worktrees/a && mise run test"
    assert wl.unwrap_output_filter(bof.build_new_cmd(original)) == original


def test_unwrap_returns_pytest_with_added_flags():
    wrapped = bof.build_new_cmd("cd /x && pytest -q")
    inner = wl.unwrap_output_filter(wrapped)
    assert inner.startswith("cd /x && pytest -q")
    assert "TMP_OUT" not in inner


def test_unwrap_multiline_command():
    original = "cd /x && mise run test\n# trailing comment"
    assert wl.unwrap_output_filter(bof.build_new_cmd(original)) == original


@pytest.mark.parametrize(
    "command",
    [
        "pytest -q",
        "cd /x && ls",
        "",
        "TMP_OUT=1; echo hi",
        bof.build_kubectl_tail_cmd("kubectl logs pod"),
    ],
)
def test_unwrap_leaves_other_commands_unchanged(command):
    assert wl.unwrap_output_filter(command) == command


def test_recorder_records_through_wrapper(worktree):
    wrapped = bof.build_new_cmd(f"cd {worktree} && pytest -q")
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": wrapped},
        "cwd": str(worktree.parents[2]),
    }
    subprocess.run([sys.executable, str(RECORDER)], input=json.dumps(payload), text=True)
    rec = json.loads((worktree / ".git" / "workbench-verify.json").read_text())
    assert rec["command"].startswith("pytest")
    assert "TMP_OUT" not in rec["command"]
    assert rec["head"] == git(worktree, "rev-parse", "HEAD")
    assert rec["passed"] is True


def test_recorder_wrapped_failure_records_not_passed(worktree):
    wrapped = bof.build_new_cmd(f"cd {worktree} && mise run test")
    payload = {
        "hook_event_name": "PostToolUseFailure",
        "tool_name": "Bash",
        "tool_input": {"command": wrapped},
        "cwd": str(worktree.parents[2]),
    }
    subprocess.run([sys.executable, str(RECORDER)], input=json.dumps(payload), text=True)
    rec = json.loads((worktree / ".git" / "workbench-verify.json").read_text())
    assert rec["passed"] is False


def test_unwrap_any_spill_dir():
    original = "cd /x && mise run test"
    spill_dirs = (None, "/main/.logs/bash-output", "/main with space/.logs/b", "/it's/.logs")
    for spill_dir in spill_dirs:
        wrapped = wl.wrap_output_filter(original, 4000, spill_dir)
        assert wrapped != original
        assert wl.unwrap_output_filter(wrapped) == original
    assert wl.unwrap_output_filter("pytest -q") == "pytest -q"
