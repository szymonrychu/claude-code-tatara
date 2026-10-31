import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from create import (  # noqa: E402
    WorktreeError,
    create,
    existing_names,
    integration,
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


# ---------------------------------------------------------------- integration


def test_integration_creates_meta_tree(repo):
    info = integration("my-plan", start=repo)
    assert info["verb"] == "created" and info["branch"] == "my-plan" and info["base"] == "main"
    assert info["name"] == "my-plan"
    assert Path(info["path"]) == worktrees_dir(repo) / "my-plan"
    assert (Path(info["path"]) / "README.md").exists()
    assert git(repo, "rev-parse", "my-plan").stdout == git(repo, "rev-parse", "main").stdout


def test_integration_reuses_tree_and_branch(repo):
    first = integration("my-plan", start=repo)
    (Path(first["path"]) / "wip.txt").write_text("x")
    again = integration("my-plan", start=repo)
    assert again["verb"] == "reused" and again["path"] == first["path"]
    assert (Path(first["path"]) / "wip.txt").exists()
    git(repo, "worktree", "remove", "--force", first["path"])
    git(repo, "branch", "-f", "my-plan", "HEAD")
    again = integration("my-plan", start=repo)
    assert again["verb"] == "created"
    assert git(Path(again["path"]), "branch", "--show-current").stdout.strip() == "my-plan"


def test_integration_refuses_destination_that_is_not_the_worktree(repo):
    dest = worktrees_dir(repo) / "my-plan"
    dest.mkdir(parents=True)
    with pytest.raises(WorktreeError) as e:
        integration("my-plan", start=repo)
    assert str(dest) in str(e.value)


def test_integration_refuses_tree_on_another_branch(repo):
    other = create("my-plan", start=repo)
    git(Path(other["path"]), "checkout", "-q", "-b", "elsewhere")
    with pytest.raises(WorktreeError) as e:
        integration("my-plan", start=repo)
    assert other["path"] in str(e.value)


def test_integration_reuses_existing_branch(repo):
    git(repo, "branch", "my-plan")
    info = integration("my-plan", start=repo)
    assert info["verb"] == "created" and Path(info["path"]).is_dir()
    assert git(Path(info["path"]), "branch", "--show-current").stdout.strip() == "my-plan"


def test_integration_component_forks_tracked_branch(tmp_path):
    wb = tmp_path / "wb"
    comp = wb / "code" / "svc"
    comp.mkdir(parents=True)
    (wb / ".gitmodules").write_text("")
    git(comp, "init", "-q", "-b", "main")
    (comp / "a.txt").write_text("a")
    git(comp, "add", "-A")
    git(comp, "commit", "-qm", "init")
    local = integration("pl", repo="svc", start=wb)
    assert Path(local["path"]) == worktrees_dir(wb) / "pl" / "svc"
    assert local["base"] == "main"
    (comp / "b.txt").write_text("b")
    git(comp, "add", "-A")
    git(comp, "commit", "-qm", "second")
    git(comp, "update-ref", "refs/remotes/origin/main", "HEAD~1")
    git(comp, "update-ref", "refs/remotes/origin/dev", "HEAD~1")
    git(comp, "branch", "dev")
    got = integration("plan2", base="dev", repo="svc", start=wb)
    assert (
        git(Path(got["path"]), "rev-parse", "HEAD").stdout
        == git(comp, "rev-parse", "HEAD~1").stdout
    )


def test_integration_cli_prints_path_branch_base_and_verb(repo, monkeypatch, capsys):
    from create import main

    monkeypatch.chdir(repo)
    assert main(["--integration", "--name", "cli-plan"]) == 0
    out = capsys.readouterr().out
    assert str(worktrees_dir(repo) / "cli-plan") in out
    assert "cli-plan" in out and "main" in out and "created" in out


def test_skill_and_help_speak_of_the_plan_tree():
    import re

    text = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text()
    flat = " ".join(text.split())
    assert "**Plan tree.**" in flat
    assert "ticket.py move <plan> in-progress" in flat
    assert not re.search(r"\bepics?\b", flat, re.I)
    script = Path(__file__).resolve().parents[1] / "scripts" / "create.py"
    helptext = subprocess.run(
        [sys.executable, str(script), "--help"], capture_output=True, text=True, check=True
    ).stdout
    assert not re.search(r"\bepic", helptext, re.I)
    assert "<plan>" in helptext


def test_integration_takes_a_plan_and_speaks_of_the_plan_tree():
    import inspect

    from create import integration

    assert list(inspect.signature(integration).parameters)[0] == "plan"
    assert "plan" in integration.__doc__ and "epic" not in integration.__doc__
