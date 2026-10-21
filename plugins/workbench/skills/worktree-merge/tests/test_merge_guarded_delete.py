"""merge.cleanup(..., merged_into_ref=): the explicit contained check, then git branch -D."""

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "worktree-create" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from create import create  # noqa: E402
from merge import cleanup, delete_if_merged  # noqa: E402

GIT = ["git", "-c", "user.email=t@t", "-c", "user.name=T", "-c", "commit.gpgsign=false"]


def git(repo, *args):
    return subprocess.run(GIT + list(args), cwd=repo, check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    (r / "a").write_text("a\n")
    git(r, "add", "-A")
    git(r, "commit", "-qm", "base")
    return r


def branch_list(repo):
    return git(repo, "branch", "--format=%(refname:short)").stdout.split()


def test_guarded_cleanup_deletes_merged_branch_with_force_delete(repo):
    wt = Path(create("t1", start=repo)["path"])
    (wt / "t1.py").write_text("1\n")
    git(wt, "add", "-A")
    git(wt, "commit", "-qm", "t1")
    git(repo, "branch", "side", "main")  # main's HEAD stays elsewhere than the target
    git(repo, "checkout", "-q", "side")
    git(repo, "branch", "target", "t1")
    notes = cleanup(repo, wt, "t1", merged_into_ref="target")
    assert "deleted branch t1" in notes and "t1" not in branch_list(repo)


def test_guarded_cleanup_keeps_unmerged_branch_with_reason(repo):
    wt = Path(create("t1", start=repo)["path"])
    (wt / "t1.py").write_text("1\n")
    git(wt, "add", "-A")
    git(wt, "commit", "-qm", "t1")
    notes = cleanup(repo, wt, "t1", merged_into_ref="main")
    assert any("branch t1 kept" in n and "no equivalent in main" in n for n in notes)
    assert "t1" in branch_list(repo)
    assert "kept" in delete_if_merged(repo, "t1", "main")
