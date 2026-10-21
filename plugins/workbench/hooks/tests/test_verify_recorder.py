"""Tests for the PostToolUse verification recorder and its shared worktree lib."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
HOOK = HOOKS / "verify-recorder.py"
PLUGIN_JSON = HOOKS.parent / ".claude-plugin" / "plugin.json"

sys.path.insert(0, str(HOOKS))
from worktree_lib import leading_cd_target  # noqa: E402


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def make_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "t@example.com")
    git(path, "config", "user.name", "T")
    (path / "seed.txt").write_text("seed\n")
    git(path, "add", "seed.txt")
    git(path, "commit", "-qm", "seed")
    return path


@pytest.fixture
def worktree(tmp_path: Path) -> Path:
    return make_repo(tmp_path / "wb" / ".claude" / "worktrees" / "t1-guard")


def run_recorder(payload) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload if isinstance(payload, str) else json.dumps(payload),
        capture_output=True,
        text=True,
    )


def bash_payload(command, cwd, event="PostToolUse"):
    return {
        "hook_event_name": event,
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(cwd),
    }


def record_file(repo: Path) -> Path:
    return repo / ".git" / "workbench-verify.json"


def test_records_a_passing_run_on_a_clean_tree(worktree: Path):
    proc = run_recorder(bash_payload(f"cd {worktree} && pytest tests/", "/"))
    assert proc.returncode == 0
    assert proc.stdout == ""
    rec = json.loads(record_file(worktree).read_text())
    assert rec["passed"] is True
    assert rec["head"] == git(worktree, "rev-parse", "HEAD")
    assert rec["dirty"] is False
    assert rec["command"] == "pytest tests/"
    assert rec["at"]


def test_records_dirty_tree(worktree: Path):
    (worktree / "seed.txt").write_text("changed\n")
    run_recorder(bash_payload(f"cd {worktree} && pytest tests/", "/"))
    assert json.loads(record_file(worktree).read_text())["dirty"] is True


def test_failure_event_records_not_passed(worktree: Path):
    run_recorder(bash_payload(f"cd {worktree} && pytest", "/", event="PostToolUseFailure"))
    assert json.loads(record_file(worktree).read_text())["passed"] is False


def test_other_event_writes_nothing(worktree: Path):
    run_recorder(bash_payload("pytest", worktree, event="PreToolUse"))
    assert not record_file(worktree).exists()


def test_no_cd_uses_cwd(worktree: Path):
    run_recorder(bash_payload("mise run test", worktree))
    assert json.loads(record_file(worktree).read_text())["command"] == "mise run test"


def test_quoted_trailing_slash_semicolon(worktree: Path):
    run_recorder(bash_payload(f"cd '{worktree}/' ; bats tests/", "/"))
    rec = json.loads(record_file(worktree).read_text())
    assert rec["command"] == "bats tests/"


def test_non_verification_command_writes_nothing(worktree: Path):
    run_recorder(bash_payload(f"cd {worktree} && git status", "/"))
    assert not record_file(worktree).exists()


def test_non_worktree_repo_writes_nothing(tmp_path: Path):
    repo = make_repo(tmp_path / "plain-repo")
    run_recorder(bash_payload("pytest", repo))
    assert not record_file(repo).exists()


def test_non_bash_tool_writes_nothing(worktree: Path):
    payload = bash_payload("pytest", worktree)
    payload["tool_name"] = "Read"
    run_recorder(payload)
    assert not record_file(worktree).exists()


def test_invalid_json_is_silent():
    proc = run_recorder("not json")
    assert proc.returncode == 0
    assert proc.stdout == ""


def test_non_dict_json_is_silent():
    proc = run_recorder("[1, 2]")
    assert proc.returncode == 0
    assert proc.stdout == ""


@pytest.mark.parametrize(
    "command,expected",
    [
        ("cd /a/b && pytest", "/a/b"),
        ("cd '/a/b/' && pytest", "/a/b"),
        ('cd "/a/b" ; ls', "/a/b"),
        ("  cd /a/b  || true", "/a/b"),
        ("cd /a/b\npytest", "/a/b"),
        ("pytest", None),
        ("echo hi && cd /a/b && pytest", None),
        ("cd /a/b", None),
    ],
)
def test_leading_cd_target(command, expected):
    assert leading_cd_target(command) == expected


def test_plugin_json_registers_recorder_for_both_events():
    hooks = json.loads(PLUGIN_JSON.read_text())["hooks"]
    for event in ("PostToolUse", "PostToolUseFailure"):
        entries = [
            h
            for e in hooks[event]
            if e.get("matcher") == "Bash"
            for h in e["hooks"]
            if "verify-recorder.py" in h["command"]
        ]
        assert len(entries) == 1, event
        assert entries[0]["timeout"] == 10
