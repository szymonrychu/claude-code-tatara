"""ticket.py reap --epic E --task T: removes one merged, clean task worktree mid-epic."""

import json

import pytest
from ticket_repo_helpers import branches, cli, deliver, init_repo, started


@pytest.fixture
def repo(tmp_path):
    return init_repo(tmp_path / "proj")


@pytest.fixture
def root(repo):
    return repo / "docs" / "plans"


def wt_of(repo, ep, t):
    return repo / ".claude" / "worktrees" / f"{ep}-{t}"


def test_reap_task_mid_epic(repo, root):
    ep = started(repo, root)
    deliver(repo, root, ep, "alpha")
    r = cli("reap", "--epic", ep, "--task", "alpha", "--root", root)
    assert r.returncode == 0, r.stderr
    assert not wt_of(repo, ep, "alpha").exists()
    assert f"{ep}-alpha" not in branches(repo)
    assert str(wt_of(repo, ep, "alpha")) in json.loads(r.stdout)["removed"]
    assert wt_of(repo, ep, "beta").is_dir()


def test_reap_task_refuses_unmerged_or_dirty(repo, root):
    ep = started(repo, root)
    deliver(repo, root, ep, "alpha", merge=False)
    r = cli("reap", "--epic", ep, "--task", "alpha", "--root", root)
    assert r.returncode == 1
    assert "unmerged" in r.stderr and len(r.stderr.strip().splitlines()) == 1
    assert wt_of(repo, ep, "alpha").is_dir()
    wt = deliver(repo, root, ep, "beta")
    (wt / "scratch.txt").write_text("wip")
    r = cli("reap", "--epic", ep, "--task", "beta", "--root", root)
    assert r.returncode == 1 and "dirty" in r.stderr
    assert wt.is_dir()


def test_reap_task_without_epic_is_usage_error(repo, root):
    started(repo, root)
    r = cli("reap", "--task", "alpha", "--root", root)
    assert r.returncode != 0 and "--task" in r.stderr


def test_reap_epic_still_refuses(repo, root):
    ep = started(repo, root)
    r = cli("reap", "--epic", ep, "--root", root)
    assert r.returncode == 1 and "not done" in r.stderr


def test_reap_task_unknown_task_errors(repo, root):
    ep = started(repo, root)
    r = cli("reap", "--epic", ep, "--task", "nope", "--root", root)
    assert r.returncode == 1 and "nope" in r.stderr
