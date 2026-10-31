"""Tests for the slug collision guard and rename: a plan's slug is its branch and tree name."""

import subprocess
import sys

import pytest
from ticket_repo_helpers import SCRIPT, git, init_repo, last_subject, meta

sys.path.insert(0, str(SCRIPT.parent))
sys.path.insert(0, str(SCRIPT.parents[3] / "scripts" / "lib"))
import workbench  # noqa: E402


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, cwd=cwd
    )


@pytest.fixture
def repo(tmp_path):
    r = init_repo(tmp_path / "wb")
    (r / "docs" / "plans").mkdir(parents=True)
    return r


def plans(repo):
    return repo / "docs" / "plans"


def new(repo, title, *extra):
    return cli("new", "--root", plans(repo), "--title", title, *extra, cwd=repo)


def mk(repo, title):
    r = new(repo, title, "--force")
    assert r.returncode == 0, r.stderr


def rename(repo, plan, title):
    return cli("rename", "--root", plans(repo), plan, title, cwd=repo)


def head(repo):
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def test_new_refuses_slug_of_an_existing_branch_naming_it(repo):
    git(repo, "branch", "taken")
    before = head(repo)
    r = new(repo, "taken", "--force")
    assert r.returncode == 1
    assert "plan slug taken collides with existing branch taken" in r.stderr
    assert not (plans(repo) / "todo" / "taken").exists()
    assert head(repo) == before


def test_new_refuses_slug_of_an_existing_tree_naming_it(repo):
    (workbench.worktrees_dir(repo) / "leftover").mkdir(parents=True)
    r = new(repo, "leftover", "--force")
    assert r.returncode == 1
    assert "plan slug leftover collides with existing tree leftover" in r.stderr
    assert not (plans(repo) / "todo" / "leftover").exists()


def test_new_refuses_slug_of_a_component_branch(tmp_path):
    wb = init_repo(tmp_path / "wb")
    (wb / ".gitmodules").write_text("")
    comp = init_repo(wb / "code" / "svc")
    git(comp, "branch", "busy")
    (wb / "docs" / "plans").mkdir(parents=True)
    r = cli("new", "--root", wb / "docs" / "plans", "--title", "busy", cwd=wb)
    assert r.returncode == 1 and "existing branch busy" in r.stderr


def test_check_title_reports_branch_collision(repo):
    git(repo, "branch", "foo-bar")
    r = cli("check", "--root", plans(repo), "--title", "foo bar", cwd=repo)
    assert r.returncode == 1
    assert "ticket.py: plan slug foo-bar collides with existing branch foo-bar" in r.stderr


def test_unrelated_names_still_create(repo):
    git(repo, "branch", "foo")
    mk(repo, "foo bar")
    assert (plans(repo) / "todo" / "foo-bar" / "plan.md").is_file()


def test_rename_in_todo_moves_dir_title_and_heading(repo):
    mk(repo, "Old name")
    r = rename(repo, "old-name", "New name")
    assert r.returncode == 0, r.stderr
    d = plans(repo) / "todo" / "new-name"
    assert r.stdout.strip() == str(d)
    assert not (plans(repo) / "todo" / "old-name").exists()
    p = d / "plan.md"
    assert meta(p)["title"] == "New name"
    assert "\n# New name\n" in p.read_text() and "# Old name" not in p.read_text()
    assert last_subject(repo) == "chore(ticket): new-name rename"
    assert git(repo, "status", "--porcelain").stdout == ""


def test_rename_same_slug_new_title_keeps_the_dir(repo):
    mk(repo, "Alpha")
    r = rename(repo, "alpha", "ALPHA")
    assert r.returncode == 0, r.stderr
    assert meta(plans(repo) / "todo" / "alpha" / "plan.md")["title"] == "ALPHA"


def test_rename_same_title_is_a_no_op(repo):
    mk(repo, "Alpha")
    before = head(repo)
    r = rename(repo, "alpha", "Alpha")
    assert r.returncode == 0 and head(repo) == before


def test_rename_refuses_colliding_slug(repo):
    mk(repo, "foo bar")
    mk(repo, "other")
    r = rename(repo, "other", "foo bar")
    assert r.returncode == 1
    assert "plan slug 'foo-bar' already exists in todo" in r.stderr
    assert (plans(repo) / "todo" / "other").is_dir()
    git(repo, "branch", "zed")
    r = rename(repo, "other", "zed")
    assert r.returncode == 1 and "collides with existing branch zed" in r.stderr
    assert (plans(repo) / "todo" / "other").is_dir()


@pytest.mark.parametrize("phase", ["in-progress", "done"])
def test_rename_frozen_after_todo(repo, phase):
    mk(repo, "Alpha")
    (plans(repo) / phase).mkdir()
    (plans(repo) / "todo" / "alpha").rename(plans(repo) / phase / "alpha")
    r = rename(repo, "alpha", "Beta")
    assert r.returncode == 1
    assert f"plan 'alpha' is in {phase}; its slug froze when it left todo" in r.stderr
