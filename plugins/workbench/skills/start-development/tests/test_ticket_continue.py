"""ticket.py continue: apply the last return, record rulings, gate merges, refresh, write args."""

import json
import sys
from pathlib import Path

import pytest

SD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(SD / "scripts"))
import ticket  # noqa: E402
from test_ticket_run import cli, commit_all, git, mk_epic, mk_task  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@t")
    git(r, "config", "user.name", "t")
    (r / "a.py").write_text("x = 1\n")
    git(r, "add", ".")
    git(r, "commit", "-m", "init")
    return r


@pytest.fixture
def root(repo):
    return repo / "docs" / "plans"


@pytest.fixture
def epic(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "Alpha")
    mk_task(root, ep, "Beta", extra=("--depends-on", "alpha"))
    commit_all(repo)
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0
    # the epic branch carries the ticket move
    git(repo / ".claude" / "worktrees" / ep, "merge", "--ff-only", "main")
    return ep


def meta(root, ep, slug):
    p = root / "in-progress" / ep / "tasks" / f"{slug}.md"
    return ticket.load(p.read_text(), p).meta


def ret(repo, alpha_head=True):
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    alpha = {
        "id": "alpha",
        "branch": "b-alpha",
        "verified": alpha_head,
        "clean": False,
        "stopped": "gate-repeat",
    }
    if alpha_head:
        alpha["verification"] = {"head": head}
    beta = {"id": "beta", "branch": "big-epic-beta", "verified": False, "clean": False}
    return {
        "run": "r1",
        "tasks": [alpha, beta],
        "escalated": [{"id": "alpha", "reason": "gate-repeat"}],
    }


def write_ret(repo, data):
    p = repo / "return.json"
    p.write_text(json.dumps(data))
    return p


def test_accept_unverified_fails(repo, root, epic, tmp_path):
    rj = write_ret(repo, ret(repo, alpha_head=False))
    head = git(repo, "rev-parse", "HEAD").stdout
    r = cli(
        "continue",
        epic,
        "--root",
        root,
        "--out-dir",
        tmp_path / "o",
        "--accept",
        "alpha",
        "--reason",
        "x",
        "--return",
        rj,
    )
    assert r.returncode == 1 and "alpha" in r.stderr and "unverified" in r.stderr
    assert not (root / "in-progress" / epic / "rulings.json").exists()
    assert meta(root, epic, "alpha")["status"] == "in-progress"
    assert git(repo, "rev-parse", "HEAD").stdout == head
    assert not (tmp_path / "o").exists()


def test_accept_needs_reason(repo, root, epic, tmp_path):
    r = cli("continue", epic, "--root", root, "--out-dir", tmp_path / "o", "--accept", "alpha")
    assert r.returncode == 1 and "reason" in r.stderr


def _task_branch(repo, root, epic, name):
    """A done alpha whose recorded branch is `name` and carries one commit."""
    tree = repo / ".claude" / "worktrees" / f"{epic}-alpha-tmp"
    git(repo, "worktree", "add", "-q", "-b", name, str(tree), "main")
    (tree / "mine.txt").write_text("m")
    git(tree, "add", "-A")
    git(tree, "commit", "-m", "alpha work")
    head = git(tree, "rev-parse", "HEAD").stdout.strip()
    git(repo, "worktree", "remove", "--force", str(tree))
    return head


def _continue(repo, root, epic, tmp_path, head, branch):
    data = ret(repo)
    data["tasks"][0]["branch"] = branch
    data["tasks"][0]["verification"] = {"head": head}
    return cli(
        "continue", epic, "--root", root, "--out-dir", tmp_path / "out",
        "--accept", "alpha", "--reason", "ok", "--return", write_ret(repo, data),
    )  # fmt: skip


def test_merge_line_names_legacy_double_hyphen_branch(repo, root, epic, tmp_path):
    head = _task_branch(repo, root, epic, f"{epic}--alpha")
    r = _continue(repo, root, epic, tmp_path, head, f"{epic}--alpha")
    assert r.returncode == 2, r.stderr
    assert f"MERGE alpha --name {epic}--alpha --base {epic} --repo proj" in r.stdout.splitlines()
