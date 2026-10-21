import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "worktree-create" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from create import create  # noqa: E402
from merge import contained, main, merge_back, merged_into  # noqa: E402

GIT = ["git", "-c", "user.email=t@t", "-c", "user.name=T", "-c", "commit.gpgsign=false"]


def git(repo, *args, check=True):
    return subprocess.run(GIT + list(args), cwd=repo, check=check, capture_output=True, text=True)


def commit(repo, name, body="x\n"):
    (repo / name).write_text(body)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", f"add {name}")


def rev(repo, ref):
    return git(repo, "rev-parse", ref).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("SUITE_LOCK_DIR", str(tmp_path / "lock"))
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    commit(r, "README.md", "base\n")
    return r


@pytest.fixture
def rebased(repo):
    """ep-t1 lands on ep; ep is then rebased onto a moved main: t1 is no ancestor of ep."""
    ept = Path(create("ep", start=repo)["path"])
    task = Path(create("ep-t1", base="ep", start=repo)["path"])
    commit(task, "t1.py", "1\n")
    git(ept, "merge", "--ff-only", "ep-t1")
    commit(repo, "moved.txt", "m\n")
    git(ept, "rebase", "main")
    return repo, ept, task


def test_ancestor(repo):
    git(repo, "branch", "b")
    assert contained(repo, "b", "main") == (True, "ancestor")


def test_patch_equivalent_after_rebase(rebased):
    repo, ept, task = rebased
    assert git(repo, "merge-base", "--is-ancestor", "ep-t1", "ep", check=False).returncode != 0
    assert contained(repo, "ep-t1", "ep") == (True, "patch-equivalent")
    assert merged_into(repo, "ep-t1", "ep") is True


def test_not_contained_counts_commits(repo):
    git(repo, "checkout", "-qb", "b")
    commit(repo, "a.txt")
    commit(repo, "b.txt")
    git(repo, "checkout", "-q", "main")
    assert contained(repo, "b", "main") == (
        False,
        "2 commit(s) of b have no equivalent in main",
    )
    assert merged_into(repo, "b", "main") is False


def test_merge_of_target_commit_is_ignored(repo):
    git(repo, "checkout", "-qb", "b")
    commit(repo, "a.txt")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "--ff-only", "b")
    git(repo, "checkout", "-qb", "dep", "main~1")
    commit(repo, "d.txt")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--no-ff", "-m", "m", "dep")
    git(repo, "checkout", "-q", "dep")
    git(repo, "merge", "-q", "--no-ff", "-m", "merge main", "main")
    git(repo, "checkout", "-q", "main")
    assert contained(repo, "dep", "main")[0] is True


def test_nothing_to_merge_verifies_in_target(rebased):
    repo, ept, task = rebased
    before = rev(repo, "ep")
    info = merge_back("ep-t1", base="ep", start=repo, verify="pwd > ../where.txt", suites=False)
    assert info["merged"] == 0 and info["contained"] is True
    assert info["containedBy"] == "patch-equivalent"
    assert info["verification"]["passed"] is True
    assert info["verification"]["command"] == "pwd > ../where.txt"
    assert info["baseBefore"] == info["baseAfter"] == before
    assert (ept.parent / "where.txt").read_text().strip() == str(ept.resolve())


def test_nothing_to_merge_failing_verify_exits_4(rebased, capsys):
    repo, ept, task = rebased
    before = rev(repo, "ep")
    info = merge_back("ep-t1", base="ep", start=repo, verify="echo boom; false", suites=False)
    assert info["verification"]["passed"] is False
    assert "boom" in info["verification"]["tail"][-1]
    assert info["cleaned"] is False and task.exists()
    assert rev(repo, "ep") == before


def test_cli_failing_verify_exit_4(rebased, monkeypatch):
    repo, ept, task = rebased
    monkeypatch.chdir(repo)
    assert main(["--name", "ep-t1", "--base", "ep", "--verify", "false", "--no-suites"]) == 4


def test_nothing_to_merge_without_verify(repo):
    ept = Path(create("ep", start=repo)["path"])
    Path(create("ep-t1", base="ep", start=repo))
    info = merge_back("ep-t1", base="ep", start=repo, suites=False)
    assert info["merged"] == 0 and info["contained"] is True
    assert info["containedBy"] == "ancestor"
    assert info["cleaned"] is True
    assert ept.exists()
