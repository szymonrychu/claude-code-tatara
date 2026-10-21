import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from create import (  # noqa: E402
    WorktreeError,
    create,
    existing_names,
    validate_name,
    workbench_root,
    worktrees_dir,
)

GIT = ["git", "-c", "user.email=t@t", "-c", "user.name=T", "-c", "commit.gpgsign=false"]


def git(repo, *args, check=True):
    return subprocess.run(GIT + list(args), cwd=repo, check=check, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    (r / "README.md").write_text("base\n")
    git(r, "add", "-A")
    git(r, "commit", "-qm", "init")
    return r


def test_creates_worktree_under_claude_worktrees(repo):
    info = create("feat-a", start=repo)
    assert Path(info["path"]) == worktrees_dir(repo) / "feat-a"
    assert Path(info["path"]).is_dir()
    assert (Path(info["path"]) / "README.md").exists()
    assert info["branch"] == "feat-a"


def test_worktree_starts_from_latest_local_base(repo):
    (repo / "new.txt").write_text("later\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "second")
    info = create("feat-b", start=repo)
    assert (Path(info["path"]) / "new.txt").exists(), "worktree did not start from current main"


def test_rejects_a_name_already_in_use(repo):
    create("taken", start=repo)
    with pytest.raises(WorktreeError) as e:
        create("taken", start=repo)
    assert "already exists" in str(e.value)
    assert "taken" in str(e.value), (
        "the error should name what is in use so a new name can be picked"
    )


def test_rejects_a_name_whose_branch_already_exists(repo):
    git(repo, "branch", "reserved")
    with pytest.raises(WorktreeError) as e:
        validate_name("reserved", repo, repo)
    assert "branch" in str(e.value)


@pytest.mark.parametrize("bad", ["", "A-Caps", "has space", "-leading", "x", "sl/ash", "e" * 70])
def test_rejects_invalid_names(bad, repo):
    with pytest.raises(WorktreeError):
        validate_name(bad, repo, repo)


def test_existing_names_lists_what_is_taken(repo):
    assert existing_names(repo) == []
    create("one", start=repo)
    create("two", start=repo)
    assert existing_names(repo) == ["one", "two"]


def test_workbench_root_prefers_the_superrepo(tmp_path):
    wb = tmp_path / "wb"
    (wb / "code" / "sub").mkdir(parents=True)
    (wb / ".gitmodules").write_text("")
    git(wb, "init", "-q", "-b", "main")
    assert workbench_root(wb / "code" / "sub") == wb


def test_two_agents_get_independent_trees(repo):
    a = Path(create("agent-a", start=repo)["path"])
    b = Path(create("agent-b", start=repo)["path"])
    (a / "only-a.txt").write_text("a\n")
    assert not (b / "only-a.txt").exists(), "worktrees are not isolated from each other"
