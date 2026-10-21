"""Epic close: move done checks the integration chain, then sweeps every tree and branch."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import ticket
from ticket_repo_helpers import (
    branches,
    cli,
    commit_all,
    git,
    init_repo,
    integration_tree,
    meta,
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


def land(repo, root, ep, task, commit=True):
    """Work in the task tree, land it on <epic> with merge.py --keep, mark the task done."""
    p = task_path(root, ep, task)
    m = meta(p)
    wt = Path(m["worktree"])
    if commit:
        (wt / f"{task}.py").write_text(f"{task} = 1\n")
        git(wt, "add", f"{task}.py")
        git(wt, "commit", "-m", f"feat: {task}")
    head = git(wt, "rev-parse", "HEAD").stdout.strip()
    r = merge_py(repo, "--name", m["branch"], "--base", ep, "--keep")
    assert r.returncode == 0, r.stdout + r.stderr
    set_meta(p, status="done", verified_head=head)
    commit_all(repo, f"deliver {task}")
    return wt


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


def test_move_done_refuses_task_not_in_epic(repo, root):
    ep = started(repo, root, ("alpha",))
    land(repo, root, ep, "alpha", commit=True)
    p = task_path(root, ep, "alpha")
    wt = Path(meta(p)["worktree"])
    (wt / "extra.py").write_text("x = 2\n")
    git(wt, "add", "extra.py")
    git(wt, "commit", "-m", "feat: unlanded")
    to_review(repo, root, ep)
    close(repo, ep)
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 1
    assert f"branch '{ep}-alpha' is not merged into '{ep}'" in r.stderr
    assert (root / "in-progress" / ep).is_dir()


def test_move_done_refuses_epic_not_in_main(repo, root):
    ep = started(repo, root, ("alpha",))
    land(repo, root, ep, "alpha")
    to_review(repo, root, ep)
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 1
    assert f"branch '{ep}' is not merged into 'main'" in r.stderr
    assert (root / "in-progress" / ep).is_dir()
    assert integration_tree(repo, ep).is_dir()


def test_full_meta_lifecycle_cleans_every_tree_and_branch(repo, root):
    ep = started(repo, root)
    for t in ("alpha", "beta"):
        land(repo, root, ep, t)
    to_review(repo, root, ep)
    close(repo, ep)
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    s = json.loads(r.stdout)
    assert s["left"] == []
    assert worktree_paths(repo) == [str(repo.resolve())]
    assert [b for b in branches(repo) if b.startswith(ep)] == []
    assert set(s["branches"]) == {ep, f"{ep}-alpha", f"{ep}-beta"}
    assert len(s["removed"]) == 3
    assert not [b for b in branches(repo) if b.endswith("-landed")]


def test_main_moved_after_fork_close_then_move_done_removes_all(repo, root):
    ep = started(repo, root)
    (repo / "later.txt").write_text("main moved\n")
    git(repo, "add", "later.txt")
    git(repo, "commit", "-m", "chore(ticket): main moves")
    for t in ("alpha", "beta"):
        land(repo, root, ep, t)
    to_review(repo, root, ep)
    close(repo, ep)
    # the close rebased <epic>: no task branch is an ancestor of it any more
    anc = git(repo, "merge-base", "--is-ancestor", f"{ep}-alpha", ep, check=False)
    assert anc.returncode != 0
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["left"] == []
    assert worktree_paths(repo) == [str(repo.resolve())]
    assert [b for b in branches(repo) if b.startswith(ep)] == []


def test_sweep_leaves_dirty_or_unmerged_trees(repo, root):
    ep = started(repo, root)
    wt_a = land(repo, root, ep, "alpha")
    wt_b = land(repo, root, ep, "beta")
    to_review(repo, root, ep)
    close(repo, ep)
    (wt_a / "scratch.txt").write_text("wip")
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    s = json.loads(r.stdout)
    left = {Path(x["path"]).name: x["reason"] for x in s["left"]}
    assert "dirty" in left[wt_a.name]
    assert wt_a.is_dir() and f"{ep}-alpha" in branches(repo)
    assert not wt_b.exists() and f"{ep}-beta" not in branches(repo)


def test_sweep_lists_non_equivalent_branch_with_reason(repo, root):
    ep = started(repo, root, ("alpha",))
    wt = land(repo, root, ep, "alpha")
    (wt / "late.py").write_text("late = 1\n")  # committed after landing, never landed
    git(wt, "add", "late.py")
    git(wt, "commit", "-m", "feat: late")
    r = cli("reap", "--epic", ep, "--task", "alpha", "--root", root)
    assert r.returncode == 1
    s = json.loads(r.stdout)
    reason = s["left"][0]["reason"]
    assert "no equivalent" in reason and f"in {ep}" in reason
    assert wt.is_dir() and f"{ep}-alpha" in branches(repo)


def test_dry_run_lists_integration_branch_once(repo, root):
    ep = started(repo, root)
    for t in ("alpha", "beta"):
        land(repo, root, ep, t)
    to_review(repo, root, ep)
    close(repo, ep)
    sweep = ticket.Sweep("main", True)
    sweep.epic(root, ticket.find_epic(ep, root))
    got = sweep.summary()["branches"]
    assert sorted(got) == sorted({ep, f"{ep}-alpha", f"{ep}-beta"})
