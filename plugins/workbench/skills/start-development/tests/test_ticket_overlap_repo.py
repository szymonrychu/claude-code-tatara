"""The cross-epic file overlap check compares (repo, path) pairs, not bare paths."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from test_ticket_check import check, cli, epic  # noqa: E402


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "plans"
    r.mkdir()
    return r


def new_task(root, ep, repo, files="src/x.py", title="Beta task"):
    return cli(
        "new-task", "--points", "3", "--root", root, "--epic", ep, "--title", title,
        "--repo", repo, "--value", "v", "--files", files, "--verify", "true",
    )  # fmt: skip


def open_alpha(root, repo, files="src/x.py"):
    a = epic(root, "Alpha thing", "in-progress")
    r = cli(
        "new-task", "--points", "3", "--root", root, "--epic", a, "--title", "Alpha task",
        "--repo", repo, "--value", "v", "--files", files, "--verify", "true",
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    return a


def test_overlap_same_path_different_repo_not_refused(root):
    open_alpha(root, "repo-a")
    b = epic(root, "Beta thing")
    r = new_task(root, b, "repo-b")
    assert r.returncode == 0, r.stderr
    assert check(root, "--epic", b).returncode == 0


def test_overlap_same_repo_and_path_refused_with_repo_in_message(root):
    open_alpha(root, "repo-a")
    b = epic(root, "Beta thing")
    r = new_task(root, b, "repo-a")
    assert r.returncode != 0
    assert "file 'src/x.py' in repo 'repo-a' is also in task" in r.stderr


def test_overlap_meta_tasks_compare_only_with_meta(root):
    open_alpha(root, "")
    b = epic(root, "Beta thing")
    assert new_task(root, b, "repo-b").returncode == 0
    r = new_task(root, b, "", title="Beta meta")
    assert r.returncode != 0
    assert "src/x.py" in r.stderr


def test_overlap_claim_check_uses_each_tasks_repo(root):
    open_alpha(root, "repo-a")
    b = epic(root, "Beta thing")
    assert new_task(root, b, "repo-b").returncode == 0
    assert check(root, "--epic", b).returncode == 0
    r = cli(
        "new-task", "--points", "3", "--root", root, "--epic", b, "--title", "Beta two",
        "--repo", "repo-a", "--value", "v", "--files", "src/x.py", "--verify", "true",
    )  # fmt: skip
    assert r.returncode != 0
