"""ticket.py worktrees: create or reuse an in-progress plan's trees, --refresh fast-forwards."""

from ticket_repo_helpers import cli, git, mk_plan, plan_tree, started


def trees(repo):
    d = repo / ".claude" / "worktrees"
    return sorted(x.name for x in d.iterdir()) if d.is_dir() else []


def test_worktrees_needs_an_in_progress_plan(repo, root):
    plan = mk_plan(root, "Still todo")
    r = cli("worktrees", plan, "--root", root)
    assert r.returncode == 1
    assert f"plan {plan!r} is in todo; worktrees needs it in-progress" in r.stderr
    assert trees(repo) == []


def test_worktrees_recreates_then_reuses_the_plan_tree(repo, root):
    help_text = cli("worktrees", "--help").stdout
    assert "--integration" not in help_text and "--refresh" in help_text
    plan = started(repo, root)
    git(repo, "worktree", "remove", str(plan_tree(repo, plan)))
    head = git(repo, "rev-parse", "HEAD").stdout
    r = cli("worktrees", plan, "--root", root)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [f"tree {plan_tree(repo, plan)} (created)"]
    assert trees(repo) == [plan]
    assert git(plan_tree(repo, plan), "branch", "--show-current").stdout.strip() == plan
    branches = git(repo, "branch", "--format=%(refname:short)").stdout.split()
    assert sorted(branches) == sorted(["main", plan])
    assert git(repo, "rev-parse", "HEAD").stdout == head  # nothing to record, no commit
    r = cli("worktrees", plan, "--root", root)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [f"tree {plan_tree(repo, plan)} (reused)"]
    r = cli("worktrees", plan, "--root", root, "--integration")
    assert r.returncode == 2 and "--integration" in r.stderr


def test_refresh_fast_forwards_the_plan_tree(repo, root):
    plan = started(repo, root)
    wt = plan_tree(repo, plan)
    (repo / "new.txt").write_text("n")
    git(repo, "add", "new.txt")
    git(repo, "commit", "-m", "main moves")
    r = cli("worktrees", plan, "--root", root, "--refresh")
    assert r.returncode == 0, r.stderr
    assert f"refresh {wt} updated" in r.stdout.splitlines()
    assert (wt / "new.txt").exists()
    r = cli("worktrees", plan, "--root", root, "--refresh")
    assert f"refresh {wt} current" in r.stdout.splitlines()
    (wt / "step.py").write_text("t = 1\n")
    git(wt, "add", "step.py")
    git(wt, "commit", "-m", "feat: step work on the plan")
    (repo / "newer.txt").write_text("n")
    git(repo, "add", "newer.txt")
    git(repo, "commit", "-m", "main moves again")
    r = cli("worktrees", plan, "--root", root, "--refresh")
    assert f"refresh {wt} ahead" in r.stdout.splitlines()
    assert not (wt / "newer.txt").exists()
    (wt / "wip.txt").write_text("x")
    r = cli("worktrees", plan, "--root", root, "--refresh")
    assert f"refresh {wt} dirty" in r.stdout.splitlines()


def test_refresh_base_option(repo, root):
    plan = started(repo, root)
    wt = plan_tree(repo, plan)
    git(repo, "branch", "other")
    git(repo, "checkout", "-q", "other")
    (repo / "o.txt").write_text("o")
    git(repo, "add", "o.txt")
    git(repo, "commit", "-m", "other moves")
    git(repo, "checkout", "-q", "main")
    r = cli("worktrees", plan, "--root", root, "--refresh", "--base", "other")
    assert f"refresh {wt} updated" in r.stdout.splitlines()
    assert (wt / "o.txt").exists()
