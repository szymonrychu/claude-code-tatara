"""ticket.py plan trees: created at the claim, reused on a second claim, mode by plan.md repos."""

import pytest
from ticket_repo_helpers import branches, cli, git, init_repo, mk_plan, set_meta, ticket


def tree_of(repo, plan):
    return ticket._mod().worktrees_dir(repo) / plan


def test_plan_branch_is_the_plan_slug():
    assert ticket.plan_branch("big-plan") == "big-plan"


def test_claim_creates_meta_plan_tree(repo, root):
    plan = mk_plan(root)
    r = cli("move", plan, "in-progress", "--root", root)
    assert r.returncode == 0, r.stderr
    wt = tree_of(repo, plan)
    assert f"tree {wt} (created)" in r.stdout.splitlines()
    assert git(wt, "branch", "--show-current").stdout.strip() == plan
    assert git(wt, "rev-parse", "HEAD").stdout == git(repo, "rev-parse", "main~1").stdout
    assert ticket.plan_trees(root, root / "in-progress" / plan) == {"": wt}


def test_meta_plan_naming_repos_outside_code_is_meta(repo, root):
    plan = mk_plan(root, repos="proj,docs")
    r = cli("move", plan, "in-progress", "--root", root)
    assert r.returncode == 0, r.stderr
    assert ticket.plan_trees(root, root / "in-progress" / plan) == {"": tree_of(repo, plan)}


def test_second_claim_reuses_the_trees(repo, root):
    plan = mk_plan(root)
    assert cli("move", plan, "in-progress", "--root", root).returncode == 0
    got = ticket.ensure_plan_trees(root, root / "in-progress" / plan)
    assert [g["verb"] for g in got] == ["reused"]
    assert got[0]["path"] == str(tree_of(repo, plan))


def test_claim_failure_moves_nothing_and_retry_reuses(repo, root):
    plan = mk_plan(root)
    blocker = tree_of(repo, plan)
    blocker.mkdir(parents=True)
    head = git(repo, "rev-parse", "HEAD").stdout
    r = cli("move", plan, "in-progress", "--root", root)
    assert r.returncode == 1 and str(blocker) in r.stderr
    assert (root / "todo" / plan).is_dir() and not (root / "in-progress" / plan).exists()
    assert git(repo, "rev-parse", "HEAD").stdout == head
    assert plan not in branches(repo)
    blocker.rmdir()
    assert cli("move", plan, "in-progress", "--root", root).returncode == 0


def test_claim_outside_git_makes_no_tree(tmp_path):
    root = tmp_path / "plain" / "docs" / "plans"
    root.mkdir(parents=True)
    plan = mk_plan(root)
    r = cli("move", plan, "in-progress", "--root", root)
    assert r.returncode == 0, r.stderr
    assert "tree " not in r.stdout
    assert (root / "in-progress" / plan / "plan.md").is_file()
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


def test_claim_creates_one_tree_per_component_repo(wb):
    root = wb / "docs" / "plans"
    plan = mk_plan(root, repos="svc,lib")
    r = cli("move", plan, "in-progress", "--root", root)
    assert r.returncode == 0, r.stderr
    base = ticket._mod().worktrees_dir(wb) / plan
    assert f"tree {base / 'svc'} (created)" in r.stdout
    assert f"tree {base / 'lib'} (created)" in r.stdout
    assert git(base / "svc", "branch", "--show-current").stdout.strip() == plan
    trees = ticket.plan_trees(root, root / "in-progress" / plan)
    assert trees == {"svc": base / "svc", "lib": base / "lib"}
    got = {
        g["path"]: g["base"] for g in ticket.ensure_plan_trees(root, root / "in-progress" / plan)
    }
    assert got == {str(base / "svc"): "develop", str(base / "lib"): "main"}
    svc_develop = git(wb / "code" / "svc", "rev-parse", "develop").stdout
    assert git(base / "svc", "rev-parse", "HEAD").stdout == svc_develop


def test_claim_refuses_a_plan_mixing_meta_and_component_repos(wb):
    root = wb / "docs" / "plans"
    plan = mk_plan(root, repos="svc,docs")
    r = cli("move", plan, "in-progress", "--root", root)
    assert r.returncode == 1
    assert (
        f"plan {plan} mixes meta and component repos (docs; svc); split it into two plans"
        in r.stderr
    )
    assert (root / "todo" / plan).is_dir()
    assert not (ticket._mod().worktrees_dir(wb) / plan).exists()


def test_component_mode_reads_repos_from_plan_md_only(wb):
    root = wb / "docs" / "plans"
    plan = mk_plan(root)
    set_meta(root / "todo" / plan / "plan.md", repos=["lib"])
    git(wb, "commit", "-am", "repos")
    r = cli("move", plan, "in-progress", "--root", root)
    assert r.returncode == 0, r.stderr
    base = ticket._mod().worktrees_dir(wb) / plan
    assert ticket.plan_trees(root, root / "in-progress" / plan) == {"lib": base / "lib"}
