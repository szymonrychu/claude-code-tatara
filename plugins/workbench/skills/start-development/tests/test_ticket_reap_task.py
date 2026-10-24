"""ticket.py reap: per-task trees are gone, so `--task` is gone; mid-epic the integration tree
stays and `reap --epic` refuses an epic that is not done."""

import json

import pytest
from ticket_repo_helpers import branches, cli, deliver, init_repo, integration_tree, started


@pytest.fixture
def repo(tmp_path):
    return init_repo(tmp_path / "proj")


@pytest.fixture
def root(repo):
    return repo / "docs" / "plans"


def test_reap_task_option_is_gone(repo, root):
    ep = started(repo, root)
    for args in (["--epic", ep, "--task", "alpha"], ["--task", "alpha"]):
        r = cli("reap", *args, "--root", root)
        assert r.returncode == 2 and "--task" in r.stderr
    assert integration_tree(repo, ep).is_dir()


def test_reap_keeps_the_live_integration_tree(repo, root):
    ep = started(repo, root)
    deliver(repo, root, ep, "alpha")
    r = cli("reap", "--root", root)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["removed"] == []
    assert integration_tree(repo, ep).is_dir() and ep in branches(repo)


def test_reap_epic_still_refuses(repo, root):
    ep = started(repo, root)
    r = cli("reap", "--epic", ep, "--root", root)
    assert r.returncode == 1 and "not done" in r.stderr
