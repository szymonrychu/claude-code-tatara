import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import commit  # noqa: E402

GITMODULES = """[submodule "foo"]
\tpath = code/foo
\turl = https://example.com/foo.git
\tbranch = main
"""


@pytest.fixture
def workbench(tmp_path, monkeypatch):
    root = tmp_path / "workbench"
    root.mkdir()
    (root / ".gitmodules").write_text(GITMODULES)
    (root / "code" / "foo").mkdir(parents=True)

    repo_dir = root / ".worktrees" / "my-branch" / "foo"
    repo_dir.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir, check=True)
    (repo_dir / "a.txt").write_text("one\n")
    (repo_dir / "b.txt").write_text("two\n")
    subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo_dir, check=True)

    (repo_dir / "a.txt").write_text("one changed\n")
    (repo_dir / "b.txt").write_text("two changed\n")

    monkeypatch.chdir(root)
    return repo_dir


def _log_subject(repo_dir):
    result = subprocess.run(
        ["git", "log", "-1", "--format=%s"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _status(repo_dir):
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def test_collect_prints_diff(workbench, capsys):
    exit_code = commit.cmd_collect("my-branch", ["foo"], [])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "a.txt" in captured.out
    assert "one changed" in captured.out
    assert "b.txt" in captured.out
    assert "two changed" in captured.out


def test_collect_file_subset_restricts_diff(workbench, capsys):
    exit_code = commit.cmd_collect("my-branch", ["foo"], ["a.txt"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "a.txt" in captured.out
    assert "b.txt" not in captured.out


def test_collect_empty_diff_skipped(workbench, capsys):
    subprocess.run(["git", "add", "-A"], cwd=workbench, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "commit everything"], cwd=workbench, check=True)
    exit_code = commit.cmd_collect("my-branch", ["foo"], [])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "skipped" in captured.out


def test_collect_unknown_repo_fails(workbench, capsys):
    exit_code = commit.cmd_collect("my-branch", ["bar"], [])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "unknown repo" in captured.out


def test_commit_creates_commit_with_title(workbench):
    exit_code = commit.cmd_commit("my-branch", ["foo"], [], {"foo": "feat: update files"})
    assert exit_code == 0
    assert _log_subject(workbench) == "feat: update files"
    assert _status(workbench).strip() == ""


def test_commit_file_subset_only_commits_those_files(workbench):
    exit_code = commit.cmd_commit("my-branch", ["foo"], ["a.txt"], {"foo": "fix: update a"})
    assert exit_code == 0
    assert _log_subject(workbench) == "fix: update a"
    status = _status(workbench)
    assert "a.txt" not in status
    assert "b.txt" in status


def test_commit_empty_diff_skipped(workbench, capsys):
    subprocess.run(["git", "add", "-A"], cwd=workbench, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "commit everything"], cwd=workbench, check=True)
    exit_code = commit.cmd_commit("my-branch", ["foo"], [], {})
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "skipped" in captured.out


def test_commit_missing_message_for_dirty_repo_fails(workbench, capsys):
    exit_code = commit.cmd_commit("my-branch", ["foo"], [], {})
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "no commit message" in captured.out
    assert _status(workbench).strip() != ""


def test_commit_unknown_repo_fails(workbench, capsys):
    exit_code = commit.cmd_commit("my-branch", ["bar"], [], {"bar": "feat: x"})
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "unknown repo" in captured.out
