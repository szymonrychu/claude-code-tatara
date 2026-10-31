"""Plan close in component mode and after a manual merge: move done checks the plan branch is
in its trunk, commits retro.md with the move, then sweeps the plan trees."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from ticket_repo_helpers import (
    branches,
    cli,
    deliver,
    git,
    init_repo,
    plan_tree,
    started,
    write_retro,
)

ROOT = Path(__file__).resolve().parents[3] / "workbench"
MERGE = ROOT / "skills" / "worktree-merge" / "scripts" / "merge.py"


@pytest.fixture
def repo(tmp_path):
    return init_repo(tmp_path / "proj")


@pytest.fixture
def root(repo):
    return repo / "docs" / "plans"


def merge_py(repo, plan):
    r = subprocess.run(
        [sys.executable, str(MERGE), "--name", plan, "--base", "main", "--keep", "--no-suites"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def worktree_paths(repo):
    out = git(repo, "worktree", "list", "--porcelain").stdout
    return [ln[9:] for ln in out.splitlines() if ln.startswith("worktree ")]


def delivered(repo, root, steps=("alpha", "beta")):
    plan = started(repo, root)
    for s in steps:
        deliver(repo, plan, s)
    write_retro(root, plan)
    return plan


def test_move_done_refuses_plan_not_in_main(repo, root):
    plan = delivered(repo, root, ("alpha",))
    r = cli("move", plan, "done", "--root", root)
    assert r.returncode == 1
    assert f"branch {plan!r} is not merged into 'main'" in r.stderr
    assert (root / "in-progress" / plan).is_dir()
    assert plan_tree(repo, plan).is_dir()


def test_rebased_merge_then_move_done_cleans_every_tree_and_branch(repo, root):
    plan = delivered(repo, root)
    merge_py(repo, plan)
    r = cli("move", plan, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    s = json.loads(r.stdout)
    assert s == {"removed": [str(plan_tree(repo, plan))], "branches": [plan], "left": []}
    assert worktree_paths(repo) == [str(repo.resolve())]
    assert branches(repo) == ["main"]


def test_main_moved_after_fork_then_move_done_removes_all(repo, root):
    plan = started(repo, root)
    (repo / "later.txt").write_text("main moved\n")
    git(repo, "add", "later.txt")
    git(repo, "commit", "-m", "chore: main moves")
    for s in ("alpha", "beta"):
        deliver(repo, plan, s)
    write_retro(root, plan)
    merge_py(repo, plan)
    r = cli("move", plan, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["left"] == []
    assert worktree_paths(repo) == [str(repo.resolve())]
    assert [b for b in branches(repo) if b.startswith(plan)] == []
