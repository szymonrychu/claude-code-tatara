"""ticket.py integration trees: created at the claim, reused on a second claim, mode by repo."""

import pytest
from ticket_repo_helpers import (
    branches,
    cli,
    commit_all,
    git,
    init_repo,
    mk_epic,
    mk_task,
    ticket,
)


def tree_of(repo, ep):
    return ticket._mod().worktrees_dir(repo) / ep


def test_integration_branch_is_the_epic_slug():
    assert ticket.integration_branch("big-epic") == "big-epic"


def test_claim_creates_meta_integration_tree_from_main(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "alpha")
    commit_all(repo)
    r = cli("move", ep, "in-progress", "--root", root)
    assert r.returncode == 0, r.stderr
    wt = tree_of(repo, ep)
    assert f"integration {wt} (created)" in r.stdout.splitlines()
    assert git(wt, "branch", "--show-current").stdout.strip() == ep
    assert git(wt, "rev-parse", "HEAD").stdout == git(repo, "rev-parse", "main~1").stdout
    assert ticket.integration_trees(root, root / "in-progress" / ep) == {"": wt}


def test_second_claim_reuses_the_trees(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "alpha")
    commit_all(repo)
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0
    got = ticket.ensure_integration_trees(root, root / "in-progress" / ep)
    assert [g["verb"] for g in got] == ["reused"]
    assert got[0]["path"] == str(tree_of(repo, ep))


def test_creation_failure_exits_1_leaves_epic_in_todo_and_commits_nothing(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "alpha")
    commit_all(repo)
    blocker = tree_of(repo, ep)
    blocker.mkdir(parents=True)
    head = git(repo, "rev-parse", "HEAD").stdout
    r = cli("move", ep, "in-progress", "--root", root)
    assert r.returncode == 1 and str(blocker) in r.stderr
    assert (root / "todo" / ep).is_dir() and not (root / "in-progress" / ep).exists()
    assert git(repo, "rev-parse", "HEAD").stdout == head
    assert ep not in branches(repo)
    blocker.rmdir()
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0


def test_claim_outside_git_makes_no_tree(tmp_path):
    root = tmp_path / "plain" / "docs" / "plans"
    ep = mk_epic(root)
    mk_task(root, ep, "alpha")
    r = cli("move", ep, "in-progress", "--root", root)
    assert r.returncode == 0, r.stderr
    assert "integration " not in r.stdout
    assert not (tmp_path / "plain" / ".claude").exists()


# ---------------------------------------------------------------- component mode


@pytest.fixture
def wb(tmp_path):
    w = init_repo(tmp_path / "wb")
    for name, branch in (("svc", "develop"), ("lib", "main")):
        c = init_repo(w / "code" / name)
        if branch != "main":
            git(c, "branch", branch)
    (w / ".gitmodules").write_text(
        '[submodule "svc"]\n\tpath = code/svc\n\turl = x\n\tbranch = develop\n'
        '[submodule "lib"]\n\tpath = code/lib\n\turl = x\n'
    )
    (w / ".gitignore").write_text("code/\n.claude/\n")
    git(w, "add", ".gitmodules", ".gitignore")
    git(w, "commit", "-m", "mods")
    return w


def comp_task(root, ep, title, repo):
    p = mk_task(root, ep, title)
    text = p.read_text().replace("repo: proj", f"repo: {repo}")
    assert f"repo: {repo}" in text
    p.write_text(text)


def test_component_mode_one_tree_per_repo_from_tracked_branch(wb):
    root = wb / "docs" / "plans"
    ep = mk_epic(root)
    comp_task(root, ep, "alpha", "svc")
    comp_task(root, ep, "beta", "lib")
    commit_all(wb)
    r = cli("move", ep, "in-progress", "--root", root)
    assert r.returncode == 0, r.stderr
    base = ticket._mod().worktrees_dir(wb) / ep
    assert f"integration {base / 'svc'} (created)" in r.stdout
    assert f"integration {base / 'lib'} (created)" in r.stdout
    assert git(base / "svc", "branch", "--show-current").stdout.strip() == ep
    trees = ticket.integration_trees(root, root / "in-progress" / ep)
    assert trees == {"svc": base / "svc", "lib": base / "lib"}
    got = {
        g["path"]: g["base"]
        for g in ticket.ensure_integration_trees(root, root / "in-progress" / ep)
    }
    assert got == {str(base / "svc"): "develop", str(base / "lib"): "main"}


def test_mixed_meta_and_component_tasks_refused(wb):
    root = wb / "docs" / "plans"
    ep = mk_epic(root)
    comp_task(root, ep, "alpha", "svc")
    mk_task(root, ep, "beta")
    commit_all(wb)
    r = cli("move", ep, "in-progress", "--root", root)
    assert r.returncode == 1
    assert f"epic {ep} mixes meta and component tasks; split it into two epics" in r.stderr
    assert (root / "todo" / ep).is_dir()
    assert not (ticket._mod().worktrees_dir(wb) / ep).exists()
