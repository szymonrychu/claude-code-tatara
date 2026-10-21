"""Tests for the slug collision guard: <epic>-<task> cannot be split, so no two names may clash."""

import subprocess
import sys

import pytest
from ticket_repo_helpers import SCRIPT, git, init_repo

sys.path.insert(0, str(SCRIPT.parent))
sys.path.insert(0, str(SCRIPT.parents[3] / "scripts" / "lib"))
import workbench  # noqa: E402


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, cwd=cwd
    )


MSG = "ticket.py: epic slug foo-bar collides with the branch of task bar in epic foo"


@pytest.fixture
def repo(tmp_path):
    r = init_repo(tmp_path / "wb")
    (r / "docs" / "plans").mkdir(parents=True)
    return r


def plans(repo):
    return repo / "docs" / "plans"


def new_epic(repo, title, *extra):
    return cli("new-epic", "--root", plans(repo), "--title", title, *extra, cwd=repo)


def mk_epic(repo, title):
    r = new_epic(repo, title, "--force")
    assert r.returncode == 0, r.stderr


def new_task(repo, epic, title, *extra):
    return cli(
        "new-task", "--root", plans(repo), "--epic", epic, "--title", title,
        "--repo", "p", "--value", "v", "--files", "a.py", "--verify", "true", *extra,
        cwd=repo,
    )  # fmt: skip


def head(repo):
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def test_new_epic_refuses_slug_equal_to_task_branch(repo):
    mk_epic(repo, "foo")
    assert new_task(repo, "foo", "bar").returncode == 0
    before = head(repo)
    r = new_epic(repo, "foo bar")
    assert r.returncode == 1
    assert MSG in r.stderr
    assert not (plans(repo) / "todo" / "foo-bar").exists()
    assert head(repo) == before


def test_new_task_refuses_name_equal_to_epic_slug(repo):
    mk_epic(repo, "foo")
    mk_epic(repo, "foo bar")
    before = head(repo)
    r = new_task(repo, "foo", "bar")
    assert r.returncode == 1
    assert "foo-bar" in r.stderr and "epic" in r.stderr
    assert not (plans(repo) / "todo" / "foo" / "tasks" / "bar.md").exists()
    assert head(repo) == before


def test_new_task_refuses_name_equal_to_other_epic_task(repo):
    mk_epic(repo, "foo")
    mk_epic(repo, "foo bar")
    assert new_task(repo, "foo-bar", "baz").returncode == 0
    r = new_task(repo, "foo", "bar baz")
    assert r.returncode == 1
    assert "foo-bar-baz" in r.stderr and "task baz in epic foo-bar" in r.stderr
    assert not (plans(repo) / "todo" / "foo" / "tasks" / "bar-baz.md").exists()


def test_force_does_not_override_branch_collision(repo):
    mk_epic(repo, "foo")
    assert new_task(repo, "foo", "bar").returncode == 0
    r = new_epic(repo, "foo bar", "--force")
    assert r.returncode == 1
    assert "collides" in r.stderr
    assert not (plans(repo) / "todo" / "foo-bar").exists()


def test_rename_refuses_colliding_slug(repo):
    mk_epic(repo, "foo")
    assert new_task(repo, "foo", "bar").returncode == 0
    mk_epic(repo, "other")
    r = cli("rename", "--root", plans(repo), "other", "foo bar", cwd=repo)
    assert r.returncode == 1
    assert "foo-bar" in r.stderr and "collides" in r.stderr
    assert (plans(repo) / "todo" / "other").is_dir()
    # a rename whose task branches would clash is refused too
    mk_epic(repo, "zed")
    assert new_task(repo, "foo", "bar baz").returncode == 0
    assert new_task(repo, "zed", "baz").returncode == 0
    r = cli("rename", "--root", plans(repo), "zed", "foo bar", cwd=repo)
    assert r.returncode == 1 and "foo-bar-baz" in r.stderr
    assert (plans(repo) / "todo" / "zed").is_dir()


def test_check_title_reports_branch_collision(repo):
    mk_epic(repo, "foo")
    assert new_task(repo, "foo", "bar").returncode == 0
    r = cli("check", "--root", plans(repo), "--title", "foo bar", cwd=repo)
    assert r.returncode == 1
    assert MSG in r.stderr


def test_refuses_name_of_legacy_tree_or_branch_on_disk(repo, tmp_path):
    mk_epic(repo, "foo")
    before = head(repo)
    # a leftover branch named like a new epic
    git(repo, "branch", "taken")
    r = new_epic(repo, "taken", "--force")
    assert r.returncode == 1 and "branch taken" in r.stderr
    # a leftover tree directory named like a new task branch
    ws = workbench.worktrees_dir(repo)
    (ws / "foo-tree").mkdir(parents=True)
    r = new_task(repo, "foo", "tree")
    assert r.returncode == 1 and "foo-tree" in r.stderr
    # a legacy double-hyphen tree and branch with no ticket
    (ws / "foo--old").mkdir()
    r = new_task(repo, "foo", "old")
    assert r.returncode == 1 and "foo--old" in r.stderr
    git(repo, "branch", "foo--gone")
    r = new_task(repo, "foo", "gone")
    assert r.returncode == 1 and "foo--gone" in r.stderr
    assert not (plans(repo) / "todo" / "foo" / "tasks" / "old.md").exists()
    assert not (plans(repo) / "todo" / "foo" / "tasks" / "gone.md").exists()
    assert not (plans(repo) / "todo" / "taken").exists()
    assert head(repo) == before


def test_unrelated_names_still_create(repo):
    mk_epic(repo, "foo")
    assert new_task(repo, "foo", "bar").returncode == 0
    mk_epic(repo, "foo baz")
