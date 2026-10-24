"""Epic close: move done checks the integration chain, then sweeps the integration trees."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import ticket
from ticket_repo_helpers import (
    branches,
    cli,
    deliver,
    git,
    init_repo,
    integration_tree,
    set_meta,
    started,
    task_path,
)

ROOT = Path(__file__).resolve().parents[3]
MERGE = ROOT / "skills" / "worktree-merge" / "scripts" / "merge.py"


@pytest.fixture
def repo(tmp_path):
    return init_repo(tmp_path / "proj")


@pytest.fixture
def root(repo):
    return repo / "docs" / "plans"


def merge_py(repo, *args):
    return subprocess.run(
        [sys.executable, str(MERGE), *map(str, args), "--no-suites"],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def to_review(repo, root, ep):
    assert cli("stage", ep, "review", "--root", root).returncode == 0
    notes = repo / "n.txt"
    notes.write_text("ok")
    r = cli("review", ep, "--verdict", "pass", "--notes-file", notes, "--root", root)
    assert r.returncode == 0, r.stderr
    notes.unlink()


def close(repo, ep):
    r = merge_py(repo, "--name", ep, "--base", "main", "--keep")
    assert r.returncode == 0, r.stdout + r.stderr


def worktree_paths(repo):
    out = git(repo, "worktree", "list", "--porcelain").stdout
    return [ln[9:] for ln in out.splitlines() if ln.startswith("worktree ")]


def delivered(repo, root, tasks=("alpha", "beta")):
    ep = started(repo, root, tasks)
    for t in tasks:
        deliver(repo, root, ep, t)
    return ep


def test_move_done_ignores_legacy_task_branch_and_worktree_keys(repo, root):
    ep = started(repo, root, ("alpha", "beta"))
    integ = integration_tree(repo, ep)
    set_meta(task_path(root, ep, "alpha"), branch="main", worktree=str(integ))
    set_meta(task_path(root, ep, "beta"), branch=ep, worktree=str(repo))
    for t in ("alpha", "beta"):
        deliver(repo, root, ep, t)
    to_review(repo, root, ep)
    close(repo, ep)
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    s = json.loads(r.stdout)
    assert s == {"removed": [str(integ)], "branches": [ep], "left": []}
    assert branches(repo) == ["main"] and repo.is_dir()


def test_move_done_refuses_epic_not_in_main(repo, root):
    ep = delivered(repo, root, ("alpha",))
    to_review(repo, root, ep)
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 1
    assert f"branch '{ep}' is not merged into 'main'" in r.stderr
    assert (root / "in-progress" / ep).is_dir()
    assert integration_tree(repo, ep).is_dir()


def test_full_meta_lifecycle_cleans_every_tree_and_branch(repo, root):
    ep = delivered(repo, root)
    to_review(repo, root, ep)
    close(repo, ep)
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    s = json.loads(r.stdout)
    assert s["left"] == []
    assert worktree_paths(repo) == [str(repo.resolve())]
    assert [b for b in branches(repo) if b.startswith(ep)] == []
    assert s["branches"] == [ep]
    assert s["removed"] == [str(integration_tree(repo, ep))]
    assert not [b for b in branches(repo) if b.endswith("-landed")]


def test_main_moved_after_fork_close_then_move_done_removes_all(repo, root):
    ep = started(repo, root)
    (repo / "later.txt").write_text("main moved\n")
    git(repo, "add", "later.txt")
    git(repo, "commit", "-m", "chore(ticket): main moves")
    for t in ("alpha", "beta"):
        deliver(repo, root, ep, t)
    to_review(repo, root, ep)
    close(repo, ep)
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["left"] == []
    assert worktree_paths(repo) == [str(repo.resolve())]
    assert [b for b in branches(repo) if b.startswith(ep)] == []


def test_sweep_leaves_dirty_integration_tree(repo, root):
    ep = delivered(repo, root)
    to_review(repo, root, ep)
    close(repo, ep)
    integ = integration_tree(repo, ep)
    (integ / "scratch.txt").write_text("wip")
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    s = json.loads(r.stdout)
    left = {Path(x["path"]).name: x["reason"] for x in s["left"]}
    assert "dirty" in left[ep]
    assert integ.is_dir() and ep in branches(repo)


def test_sweep_lists_non_equivalent_work_with_reason(repo, root):
    ep = delivered(repo, root, ("alpha",))
    to_review(repo, root, ep)
    close(repo, ep)
    integ = integration_tree(repo, ep)
    (integ / "scratch.txt").write_text("wip")  # survives move done's sweep
    assert cli("move", ep, "done", "--root", root).returncode == 0
    (integ / "scratch.txt").unlink()
    (integ / "late.py").write_text("late = 1\n")  # committed after the close, never landed
    git(integ, "add", "late.py")
    git(integ, "commit", "-m", "feat: late")
    r = cli("reap", "--epic", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    reason = json.loads(r.stdout)["left"][0]["reason"]
    assert "no equivalent" in reason and "in main" in reason
    assert integ.is_dir() and ep in branches(repo)


def test_dry_run_lists_integration_branch_once(repo, root):
    ep = delivered(repo, root)
    to_review(repo, root, ep)
    close(repo, ep)
    sweep = ticket.Sweep("main", True)
    sweep.epic(root, ticket.find_epic(ep, root))
    assert sweep.summary()["branches"] == [ep]
