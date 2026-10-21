import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "worktree-create" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from create import WorktreeError, create, worktrees_dir  # noqa: E402
from merge import assess, merge_back  # noqa: E402

GIT = ["git", "-c", "user.email=t@t", "-c", "user.name=T", "-c", "commit.gpgsign=false"]


def git(repo, *args, check=True):
    return subprocess.run(GIT + list(args), cwd=repo, check=check, capture_output=True, text=True)


def commit(repo, name, body="x\n"):
    (repo / name).write_text(body)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", f"add {name}")


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    commit(r, "README.md", "base\n")
    return r


def test_merges_work_back_and_removes_the_worktree(repo):
    wt = Path(create("feat", start=repo)["path"])
    commit(wt, "feature.py", "print(1)\n")
    info = merge_back("feat", start=repo)
    assert info["merged"] == 1
    assert info["cleaned"] is True
    assert (repo / "feature.py").exists(), "work did not land on main"
    assert not wt.exists(), "worktree was not cleaned up after a verified merge"


def test_keep_leaves_the_worktree_in_place(repo):
    wt = Path(create("feat", start=repo)["path"])
    commit(wt, "feature.py")
    info = merge_back("feat", keep=True, start=repo)
    assert info["cleaned"] is False
    assert wt.exists()
    assert (repo / "feature.py").exists()


def test_refuses_to_merge_a_dirty_worktree(repo):
    wt = Path(create("feat", start=repo)["path"])
    commit(wt, "feature.py")
    (wt / "scratch.txt").write_text("uncommitted\n")
    with pytest.raises(WorktreeError) as e:
        merge_back("feat", start=repo)
    assert "uncommitted" in str(e.value)
    assert wt.exists(), "a dirty worktree must survive so the work can be recovered"


def test_rebases_onto_a_base_that_moved(repo):
    wt = Path(create("feat", start=repo)["path"])
    commit(wt, "feature.py")
    commit(repo, "hotfix.py")  # base moves while the agent worked
    info = merge_back("feat", start=repo)
    assert info["merged"] == 1
    assert (repo / "feature.py").exists()
    assert (repo / "hotfix.py").exists()
    log = git(repo, "log", "--oneline").stdout
    assert "add feature.py" in log and "add hotfix.py" in log


def test_conflicting_rebase_aborts_and_keeps_the_worktree(repo):
    wt = Path(create("feat", start=repo)["path"])
    commit(wt, "shared.txt", "from the agent\n")
    commit(repo, "shared.txt", "from main\n")
    with pytest.raises(WorktreeError) as e:
        merge_back("feat", start=repo)
    assert "conflict" in str(e.value).lower()
    assert wt.exists(), "a conflicted worktree must be kept for resolution"
    assert (wt / "shared.txt").read_text() == "from the agent\n", "agent work was lost"


def test_nothing_to_merge_still_cleans_up(repo):
    wt = Path(create("feat", start=repo)["path"])
    info = merge_back("feat", start=repo)
    assert info["merged"] == 0
    assert not wt.exists()


def test_missing_worktree_is_an_error(repo):
    with pytest.raises(WorktreeError):
        merge_back("never-made", start=repo)


def test_cleanup_frees_the_name_for_reuse(repo):
    wt = Path(create("cycle", start=repo)["path"])
    commit(wt, "a.py")
    merge_back("cycle", start=repo)
    again = create("cycle", start=repo)
    assert Path(again["path"]) == worktrees_dir(repo) / "cycle"


def test_assess_recommends_sonnet_for_a_routine_merge(repo):
    wt = Path(create("small", start=repo)["path"])
    commit(wt, "one.py")
    a = assess("small", start=repo)
    assert a["commits"] == 1 and a["files"] == 1
    assert a["conflictPredicted"] is False
    assert a["model"] == "sonnet", a


def test_assess_escalates_to_opus_when_git_predicts_a_conflict(repo):
    wt = Path(create("clash", start=repo)["path"])
    commit(wt, "shared.txt", "agent side\n")
    commit(repo, "shared.txt", "main side\n")
    a = assess("clash", start=repo)
    assert a["conflictPredicted"] is True
    assert a["model"] == "opus", a


def test_assess_keeps_sonnet_when_the_worktree_is_dirty(repo):
    wt = Path(create("messy", start=repo)["path"])
    commit(wt, "one.py")
    (wt / "uncommitted.txt").write_text("x\n")
    a = assess("messy", start=repo)
    assert a["dirty"] is True
    assert a["model"] == "sonnet"


def test_assess_keeps_sonnet_on_a_large_change(repo):
    wt = Path(create("wide", start=repo)["path"])
    for i in range(25):
        (wt / f"f{i}.py").write_text(f"# {i}\n")
    git(wt, "add", "-A")
    git(wt, "commit", "-qm", "wide change")
    a = assess("wide", start=repo)
    assert a["files"] == 25
    assert a["model"] == "sonnet"


def test_assess_never_returns_a_diff(repo):
    """The orchestrator must be able to size the merge without reading changes."""
    wt = Path(create("quiet", start=repo)["path"])
    commit(wt, "secret.py", "a very long body\n" * 200)
    a = assess("quiet", start=repo)
    assert set(a) == {"name", "commits", "files", "conflictPredicted", "dirty", "model", "why"}
    assert "very long body" not in str(a)


@pytest.fixture
def repo_with_remote(tmp_path):
    """A clone whose local main is ahead of origin/main - the common real state."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    r = tmp_path / "proj"
    subprocess.run(["git", "clone", "-q", str(origin), str(r)], check=True)
    commit(r, "README.md", "base\n")
    git(r, "push", "-q", "-u", "origin", "main")
    # seven local commits that were never pushed
    for i in range(7):
        commit(r, f"local{i}.py", f"# {i}\n")
    return r


def test_rebases_onto_local_base_not_origin(repo_with_remote):
    """Local main ahead of origin/main must not have its commits rewritten."""
    repo = repo_with_remote
    before = git(repo, "rev-parse", "main").stdout.strip()
    ahead = git(repo, "rev-list", "--count", "origin/main..main").stdout.strip()
    assert ahead == "7", "fixture should have 7 unpushed commits"

    wt = Path(create("feat", start=repo)["path"])
    commit(wt, "feature.py")

    info = merge_back("feat", start=repo)

    assert info["merged"] == 1
    assert (repo / "feature.py").exists(), "work did not land"
    for i in range(7):
        assert (repo / f"local{i}.py").exists(), f"local commit local{i}.py was lost"
    assert git(repo, "merge-base", "--is-ancestor", before, "main", check=False).returncode == 0, (
        "local main was rewritten instead of fast-forwarded"
    )


def test_still_lands_when_origin_is_ahead(repo_with_remote):
    """Origin moving forward must not strand the work either."""
    repo = repo_with_remote
    git(repo, "push", "-q", "origin", "main")
    other = repo.parent / "other"
    subprocess.run(["git", "clone", "-q", str(repo.parent / "origin.git"), str(other)], check=True)
    commit(other, "remote-side.py")
    git(other, "push", "-q", "origin", "main")

    wt = Path(create("feat", start=repo)["path"])
    commit(wt, "feature.py")
    info = merge_back("feat", start=repo)

    # 2, not 1: worktree-create merged origin/main into the tree, so the branch
    # legitimately carries the remote commit as well as the agent's own.
    assert info["merged"] == 2
    assert (repo / "feature.py").exists()
    assert (repo / "remote-side.py").exists()


def test_lands_when_local_and_origin_have_diverged(repo_with_remote):
    """The case that actually breaks: both sides moved independently.

    Rebasing onto origin/<base> here rewrites the unpushed local commits, and the
    fast-forward into local <base> then fails as diverging branches.
    """
    repo = repo_with_remote  # local main already 7 ahead, unpushed
    other = repo.parent / "other"
    subprocess.run(["git", "clone", "-q", str(repo.parent / "origin.git"), str(other)], check=True)
    commit(other, "remote-side.py")
    git(other, "push", "-q", "origin", "main")

    before = git(repo, "rev-parse", "main").stdout.strip()
    wt = Path(create("feat", start=repo)["path"])
    commit(wt, "feature.py")

    info = merge_back("feat", start=repo)

    assert (repo / "feature.py").exists(), "agent work did not land"
    for i in range(7):
        assert (repo / f"local{i}.py").exists(), f"unpushed commit local{i}.py was lost"
    assert git(repo, "merge-base", "--is-ancestor", before, "main", check=False).returncode == 0, (
        "local main was rewritten rather than advanced"
    )
    assert info["merged"] >= 1
