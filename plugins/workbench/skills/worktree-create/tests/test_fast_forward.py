import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from create import create, fast_forward  # noqa: E402

GIT = ["git", "-c", "user.email=t@t", "-c", "user.name=T", "-c", "commit.gpgsign=false"]


def git(repo, *args):
    return subprocess.run(GIT + list(args), cwd=repo, check=True, capture_output=True, text=True)


def commit(repo, name):
    (repo / name).write_text(name)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", name)


@pytest.fixture
def pair(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    commit(r, "base.txt")
    wt = Path(create("feat", start=r)["path"])
    return r, wt


def test_updated_when_behind_and_clean(pair):
    repo, wt = pair
    commit(repo, "new.txt")
    assert fast_forward(wt, "main") == "updated"
    assert (wt / "new.txt").exists()


def test_current_when_already_at_base(pair):
    _, wt = pair
    assert fast_forward(wt, "main") == "current"


def test_dirty_tree_untouched(pair):
    repo, wt = pair
    commit(repo, "new.txt")
    (wt / "wip.txt").write_text("x")
    assert fast_forward(wt, "main") == "dirty"
    assert not (wt / "new.txt").exists()


def test_ahead_tree_untouched(pair):
    repo, wt = pair
    commit(wt, "mine.txt")
    commit(repo, "new.txt")
    head = git(wt, "rev-parse", "HEAD").stdout
    assert fast_forward(wt, "main") == "ahead"
    assert git(wt, "rev-parse", "HEAD").stdout == head


def test_fast_forward_results(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    commit(r, "base.txt")
    trees = {n: Path(create(n, start=r)["path"]) for n in ("tree-a", "tree-b", "tree-c", "tree-d")}
    commit(r, "new.txt")
    (trees["tree-b"] / "wip.txt").write_text("x")
    commit(trees["tree-c"], "mine.txt")
    got = {n: fast_forward(p, "main") for n, p in trees.items()}
    assert got == {"tree-a": "updated", "tree-b": "dirty", "tree-c": "ahead", "tree-d": "updated"}
    assert fast_forward(trees["tree-a"], "main") == "current"
