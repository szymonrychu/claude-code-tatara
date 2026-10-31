"""ticket.py move (claim and done), reap and the main-checkout guard on real git repos."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"
MERGE = ROOT / "skills" / "worktree-merge" / "scripts" / "merge.py"
sys.path.insert(0, str(SCRIPT.parent))
import ticket  # noqa: E402
from ticket_repo_helpers import (  # noqa: E402
    branches,
    cli,
    commit_all,
    deliver,
    git,
    init_repo,
    last_subject,
    meta,
    mk_plan,
    plan_tree,
    reviewed,
    set_meta,
    started,
    write_retro,
)


def summary(r):
    return json.loads(r.stdout)


def left_reasons(s):
    return {Path(x["path"]).name: x["reason"] for x in s["left"]}


# ---------------------------------------------------------------- move in-progress (claim)


def test_claim_git_mvs_sets_owner_and_commits(repo, root):
    plan = mk_plan(root)
    r = cli("move", plan, "in-progress", "--root", root, "--owner", "alice")
    assert r.returncode == 0, r.stderr
    dest = root / "in-progress" / plan
    assert r.stdout.strip().splitlines()[-1] == str(dest)
    assert not (root / "todo" / plan).exists()
    assert meta(dest / "plan.md")["owner"] == "alice"
    assert meta(dest / "plan.md")["rung"] == "3"
    assert (dest / "implementation-plan.md").is_file()
    assert last_subject(repo) == f"chore(ticket): {plan} move in-progress"
    stat = git(repo, "show", "--name-status", "--format=", "HEAD").stdout
    assert re.search(rf"R\d+\s+\S*todo/{plan}/implementation-plan.md", stat)
    assert git(repo, "status", "--porcelain", "--", "docs").stdout.strip() == ""


def test_claim_owner_defaults_to_git_user(repo, root):
    plan = mk_plan(root)
    assert cli("move", plan, "in-progress", "--root", root).returncode == 0
    assert meta(root / "in-progress" / plan / "plan.md")["owner"] == "Tess"


def test_claim_refuses_unless_in_todo(repo, root):
    plan = mk_plan(root)
    assert cli("move", plan, "in-progress", "--root", root).returncode == 0
    r = cli("move", plan, "in-progress", "--root", root)
    assert r.returncode == 1
    assert f"plan {plan!r} is in in-progress; move in-progress needs it in todo" in r.stderr


def _refused_claim(repo, root, plan, reason):
    head = git(repo, "rev-parse", "HEAD").stdout
    r = cli("move", plan, "in-progress", "--root", root)
    assert r.returncode == 1
    assert reason in r.stderr, r.stderr
    assert (root / "todo" / plan).is_dir() and not (root / "in-progress").exists()
    assert not plan_tree(repo, plan).exists()
    assert git(repo, "rev-parse", "HEAD").stdout == head


def test_claim_refuses_a_plan_without_an_agreed_rung(repo, root):
    plan = mk_plan(root, rung="")
    _refused_claim(repo, root, plan, f"plan {plan!r} has no agreed rung (plan.md rung is empty)")


def test_claim_refuses_a_plan_without_implementation_plan(repo, root):
    plan = mk_plan(root, impl=False)
    _refused_claim(repo, root, plan, f"plan {plan!r} has no implementation-plan.md")


def test_claim_names_every_refusal(repo, root):
    plan = mk_plan(root, rung="", impl=False)
    _refused_claim(repo, root, plan, "has no agreed rung")
    _refused_claim(repo, root, plan, "has no implementation-plan.md")


def test_claim_uncommitted_gate_files_are_committed_with_the_move(repo, root):
    plan = mk_plan(root, rung="", impl=False)
    d = root / "todo" / plan
    set_meta(d / "plan.md", rung="2")
    (d / "implementation-plan.md").write_text("# x implementation plan\n")
    r = cli("move", plan, "in-progress", "--root", root)
    assert r.returncode == 0, r.stderr
    assert git(repo, "status", "--porcelain", "--", "docs").stdout.strip() == ""
    tracked = git(repo, "ls-files", "docs").stdout.split()
    assert f"docs/plans/in-progress/{plan}/implementation-plan.md" in tracked


# ---------------------------------------------------------------- move done: refusals


def test_move_done_refuses_from_todo(repo, root):
    plan = mk_plan(root)
    r = cli("move", plan, "done", "--root", root)
    assert r.returncode == 1
    assert f"plan {plan!r} is in todo; move done needs it in-progress" in r.stderr
    assert (root / "todo" / plan).is_dir()


def test_move_done_refuses_without_retro(repo, root):
    plan = reviewed(repo, root, retro=False)
    r = cli("move", plan, "done", "--root", root)
    assert r.returncode == 1
    assert f"plan {plan!r} has no retro.md; the reviewer writes it when the review passes" in (
        r.stderr
    )
    assert (root / "in-progress" / plan).is_dir() and plan_tree(repo, plan).is_dir()


def test_move_done_refuses_unmerged_plan_and_keeps_everything(repo, root):
    plan = reviewed(repo, root, merge=False)
    r = cli("move", plan, "done", "--root", root)
    assert r.returncode == 1 and f"branch {plan!r} is not merged into 'main'" in r.stderr
    assert (root / "in-progress" / plan).is_dir()
    assert plan_tree(repo, plan).is_dir() and plan in branches(repo)


def test_move_done_base_option(repo, root):
    plan = reviewed(repo, root, steps=("alpha",))
    git(repo, "branch", "release", "HEAD~3")
    r = cli("move", plan, "done", "--root", root, "--base", "release")
    assert r.returncode == 1 and "release" in r.stderr


def test_move_done_accepts_a_patch_equivalent_branch(repo, root):
    plan = reviewed(repo, root, steps=("alpha",), merge=False)
    git(repo, "cherry-pick", plan)
    r = cli("move", plan, "done", "--root", root)
    assert r.returncode == 0, r.stderr


# ---------------------------------------------------------------- move done: success and cleanup


def test_move_done_moves_commits_retro_and_cleans_the_tree(repo, root):
    plan = reviewed(repo, root)
    tree = plan_tree(repo, plan)
    r = cli("move", plan, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    dest = root / "done" / plan
    assert not (root / "in-progress" / plan).exists()
    assert (dest / "plan.md").is_file() and (dest / "retro.md").is_file()
    assert last_subject(repo) == f"chore(ticket): {plan} move done"
    tracked = git(repo, "ls-files", "docs").stdout.split()
    assert f"docs/plans/done/{plan}/retro.md" in tracked
    assert git(repo, "status", "--porcelain", "--", "docs").stdout.strip() == ""
    assert summary(r) == {"removed": [str(tree)], "branches": [plan], "left": []}
    assert not tree.exists() and plan not in branches(repo)
    assert str(tree) not in git(repo, "worktree", "list").stdout


def test_move_done_sweep_error_keeps_the_move_and_reports(repo, root, monkeypatch, capsys):
    plan = reviewed(repo, root, steps=("alpha",))

    def boom(self, root_, dest):
        raise RuntimeError("sweep exploded")

    monkeypatch.setattr(ticket.Sweep, "plan", boom)
    rc = ticket.main(["move", plan, "done", "--root", str(root)])
    err = capsys.readouterr().err
    assert rc == 1 and "sweep exploded" in err and "moved to done" in err
    assert (root / "done" / plan / "retro.md").is_file()
    assert not (root / "in-progress" / plan).exists()
    assert f"chore(ticket): {plan} move done" in git(repo, "log", "--format=%s").stdout


def test_move_done_leaves_tree_whose_head_is_unmerged(repo, root):
    plan = reviewed(repo, root, steps=("alpha",))
    wt = plan_tree(repo, plan)
    git(wt, "checkout", "-b", "side-work")
    (wt / "more.py").write_text("y = 2\n")
    git(wt, "add", "more.py")
    git(wt, "commit", "-m", "unmerged work")
    r = cli("move", plan, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    s = summary(r)
    assert s["removed"] == [] and "unmerged" in left_reasons(s)[plan]
    assert wt.is_dir() and "side-work" in branches(repo)


def test_move_done_accepts_plan_tree_already_removed(repo, root):
    plan = reviewed(repo, root, steps=("alpha",))
    git(repo, "worktree", "remove", str(plan_tree(repo, plan)))
    git(repo, "branch", "-d", plan)
    r = cli("move", plan, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    assert summary(r) == {"removed": [], "branches": [], "left": []}


def test_move_done_leaves_a_dirty_tree(repo, root):
    plan = reviewed(repo, root)
    tree = plan_tree(repo, plan)
    (tree / "scratch.txt").write_text("wip")
    r = cli("move", plan, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    assert "dirty" in left_reasons(summary(r))[plan]
    assert tree.is_dir() and plan in branches(repo)


# ---------------------------------------------------------------- component mode


def component_workbench(tmp_path):
    """A workbench with code/proj and code/other (each with an origin) and docs/plans at the top."""
    wb = tmp_path / "wb"
    wb.mkdir()
    git(wb, "init", "-b", "main")
    git(wb, "config", "user.email", "t@t")
    git(wb, "config", "user.name", "Tess")
    (wb / ".gitmodules").write_text("")
    (wb / ".gitignore").write_text("code/\n.claude/\n")
    git(wb, "add", "-A")
    git(wb, "commit", "-m", "wb")
    for name in ("proj", "other"):
        bare = tmp_path / "remotes" / f"{name}.git"
        bare.mkdir(parents=True)
        git(bare, "init", "--bare", "-b", "main")
        src = init_repo(wb / "code" / name)
        git(src, "remote", "add", "origin", str(bare))
        git(src, "push", "-u", "origin", "main")
    return wb


def component_commit(wb, plan, repo_name, merged_on_origin):
    """One commit on <plan> in the claimed tree of code/<repo_name>, pushed to origin main
    when merged_on_origin (the MR landed)."""
    wt = wb / ".claude" / "worktrees" / plan / repo_name
    (wt / "int.py").write_text("i = 1\n")
    git(wt, "add", "int.py")
    git(wt, "commit", "-m", "work")
    if merged_on_origin:
        git(wt, "push", "origin", f"{plan}:main")
    return wt


def component_plan(tmp_path):
    wb = component_workbench(tmp_path)
    root = wb / "docs" / "plans"
    plan = mk_plan(root, repos="proj,other")
    r = cli("move", plan, "in-progress", "--root", root)
    assert r.returncode == 0, r.stderr
    return wb, root, plan


def test_component_move_done_refuses_until_the_mr_landed_on_origin(tmp_path):
    wb, root, plan = component_plan(tmp_path)
    proj = component_commit(wb, plan, "proj", merged_on_origin=False)
    write_retro(root, plan)
    r = cli("move", plan, "done", "--root", root)
    assert r.returncode == 1 and f"{plan!r} is not merged into 'origin/main'" in r.stderr
    assert (root / "in-progress" / plan).is_dir() and proj.is_dir()
    git(proj, "push", "origin", f"{plan}:main")
    r = cli("move", plan, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    assert str(proj) in summary(r)["removed"] and not proj.exists()


def test_component_move_done_removes_merged_trees(tmp_path):
    wb, root, plan = component_plan(tmp_path)
    proj = component_commit(wb, plan, "proj", merged_on_origin=True)
    other = component_commit(wb, plan, "other", merged_on_origin=True)
    write_retro(root, plan)
    r = cli("move", plan, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    s = summary(r)
    assert sorted(s["removed"]) == sorted([str(proj), str(other)])
    assert not proj.exists() and not other.exists()
    assert plan not in branches(wb / "code" / "proj") and plan not in branches(
        wb / "code" / "other"
    )
    assert (root / "done" / plan / "retro.md").is_file()


# ---------------------------------------------------------------- reap


def stray_tree(repo, name, *, merged, dirty=False):
    wt = repo / ".claude" / "worktrees" / name
    wt.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", "-b", name, str(wt), "main")
    (wt / f"{name}.txt").write_text("work\n")
    git(wt, "add", ".")
    git(wt, "commit", "-m", f"work {name}")
    if merged:
        git(repo, "merge", "--no-ff", "--no-edit", name)
    if dirty:
        (wt / "dirty.txt").write_text("uncommitted")
    return wt


def done_plan(repo, root, title, steps=("alpha", "beta")):
    """A done plan whose tree survived the sweep (it was dirty), clean again."""
    plan = started(repo, root, title=title)
    for s in steps:
        deliver(repo, plan, s)
    git(repo, "merge", "--no-ff", "--no-edit", plan)
    write_retro(root, plan)
    tree = plan_tree(repo, plan)
    (tree / "scratch.txt").write_text("wip")  # a dirty tree survives the sweep of `move done`
    assert cli("move", plan, "done", "--root", root).returncode == 0
    assert tree.is_dir()
    (tree / "scratch.txt").unlink()
    return plan


def test_reap_done_leftovers_and_trees_of_plans_not_in_progress(repo, root):
    done = done_plan(repo, root, "First done")
    done_tree = plan_tree(repo, done)
    live = started(repo, root, title="Live plan")
    todo = mk_plan(root, "Waiting plan")
    todo_merged = stray_tree(repo, todo, merged=True)
    live_tree = plan_tree(repo, live)
    plain = stray_tree(repo, "plain-name", merged=True)

    dry = cli("reap", "--dry-run", "--root", root)
    assert dry.returncode == 0, dry.stderr
    d = summary(dry)
    assert d["dryRun"] is True
    assert sorted(d["removed"]) == sorted([str(done_tree), str(todo_merged)])
    for wt in (done_tree, todo_merged, live_tree, plain):
        assert wt.is_dir()

    r = cli("reap", "--root", root)
    assert r.returncode == 0, r.stderr
    s = summary(r)
    assert sorted(s["removed"]) == sorted([str(done_tree), str(todo_merged)])
    assert not done_tree.exists() and done not in branches(repo)
    assert not todo_merged.exists() and todo not in branches(repo)
    assert live_tree.is_dir() and live in branches(repo)
    assert plain.is_dir() and "plain-name" not in left_reasons(s)


def test_reap_lists_unmerged_and_dirty_trees_of_plans_not_in_progress(repo, root):
    a = mk_plan(root, "Gone a")
    b = mk_plan(root, "Gone b")
    unmerged = stray_tree(repo, a, merged=False)
    dirty = stray_tree(repo, b, merged=True, dirty=True)
    r = cli("reap", "--root", root)
    assert r.returncode == 0, r.stderr
    reasons = left_reasons(summary(r))
    assert "unmerged" in reasons[a] and unmerged.is_dir() and a in branches(repo)
    assert "dirty" in reasons[b] and (dirty / "dirty.txt").is_file()


def test_reap_plan_scopes_to_one_done_plan(repo, root):
    plan = done_plan(repo, root, "First done")
    other = done_plan(repo, root, "Second done", steps=("gamma",))
    tree, other_tree = plan_tree(repo, plan), plan_tree(repo, other)
    r = cli("reap", "--plan", plan, "--root", root)
    assert r.returncode == 0, r.stderr
    s = summary(r)
    assert s["removed"] == [str(tree)] and not tree.exists()
    assert other_tree.is_dir() and other in branches(repo)


def test_reap_plan_keeps_unmerged_tree(repo, root):
    plan = done_plan(repo, root, "Late work", steps=("alpha",))
    wt = plan_tree(repo, plan)
    (wt / "late.py").write_text("late = 1\n")
    git(wt, "add", ".")
    git(wt, "commit", "-m", "late work")
    r = cli("reap", "--plan", plan, "--root", root)
    assert r.returncode == 0, r.stderr
    s = summary(r)
    assert s["removed"] == [] and wt.is_dir()
    reason = left_reasons(s)[wt.name]
    assert "unmerged" in reason and "no equivalent" in reason and "in main" in reason


def test_reap_plan_refuses_plan_not_done(repo, root):
    todo = mk_plan(root, "Still todo")
    live = started(repo, root, title="Running")
    for plan, phase in ((todo, "todo"), (live, "in-progress")):
        r = cli("reap", "--plan", plan, "--root", root)
        assert r.returncode == 1
        assert f"reap: plan {plan} is not done (in {phase}/)" in r.stderr
    assert plan_tree(repo, live).is_dir()


def test_reap_plan_unknown_slug(repo, root):
    r = cli("reap", "--plan", "nope", "--root", root)
    assert r.returncode == 1 and "unknown plan 'nope'" in r.stderr


def test_reap_has_no_epic_or_task_option(repo, root):
    for opt in ("--epic", "--task"):
        r = cli("reap", opt, "x", "--root", root)
        assert r.returncode == 2 and opt in r.stderr


def test_reap_plan_dry_run_removes_nothing(repo, root):
    plan = done_plan(repo, root, "Dry done")
    tree = plan_tree(repo, plan)
    r = cli("reap", "--plan", plan, "--dry-run", "--root", root)
    assert r.returncode == 0, r.stderr
    s = summary(r)
    assert s["dryRun"] is True and s["removed"] == [str(tree)] and s["branches"] == [plan]
    assert tree.is_dir() and plan in branches(repo)


def test_reap_plan_refuses_old_epic_format(repo, root):
    old = root / "done" / "old-epic"
    old.mkdir(parents=True)
    (old / "README.md").write_text("---\ntitle: Old\n---\n")
    r = cli("reap", "--plan", "old-epic", "--dry-run", "--root", root)
    assert r.returncode == 1
    assert f"old epic format under {old.resolve()}; run ticket.py migrate --all" in r.stderr


def test_reap_component_trees_of_a_done_plan(tmp_path):
    wb, root, plan = component_plan(tmp_path)
    merged = component_commit(wb, plan, "proj", merged_on_origin=True)
    unmerged = component_commit(wb, plan, "other", merged_on_origin=False)
    (root / "done").mkdir(parents=True)
    git(wb, "mv", str(root / "in-progress" / plan), str(root / "done" / plan))
    commit_all(wb)
    r = cli("reap", "--root", root)
    assert r.returncode == 0, r.stderr
    s = summary(r)
    assert s["removed"] == [str(merged)] and not merged.exists()
    assert unmerged.is_dir() and "origin" in left_reasons(s)["other"]


def test_dry_run_sweep_lists_the_plan_branch_once(repo, root):
    plan = reviewed(repo, root)
    sweep = ticket.Sweep("main", True)
    sweep.plan(root, ticket.find_plan(plan, root))
    assert sweep.summary()["branches"] == [plan]


# ---------------------------------------------------------------- guard and safety


def test_mutating_subcommands_refuse_in_linked_worktree(repo, root):
    plan = mk_plan(root)
    commit_all(repo)
    side = repo.parent / "side"
    git(repo, "worktree", "add", "-b", "side", str(side))
    side_root = side / "docs" / "plans"
    for args in (
        ["new", "--title", "Other"],
        ["move", plan, "in-progress"],
        ["move", plan, "done"],
        ["rename", plan, "Other"],
        ["worktrees", plan],
        ["close", plan, "--verify", "true"],
        ["reap"],
    ):
        r = cli(*args, "--root", side_root)
        assert r.returncode == 1 and "main checkout" in r.stderr, args
    assert (root / "todo" / plan).is_dir()


def test_no_force_or_capital_d_in_ticket_or_merge_cleanup():
    # only new's own flag lines are exempt; any other --force line still trips
    own = (
        "EXIT_NEAR_DUPLICATE = 3",
        "; pass --force to create anyway",
        'sp.add_argument("--force", action="store_true"',
    )
    own_exact = ('"--force",',)  # new's formatted add_argument flag line
    src = "\n".join(
        line
        for line in SCRIPT.read_text().splitlines()
        if not any(o in line for o in own) and line.strip() not in own_exact
    )
    for bad in ("--force", "branch -D", '"-D"', "'-D'", '"-f"', "'-f'"):
        assert bad not in src, bad
    merge = MERGE.read_text()
    cleanup = merge[merge.index("def cleanup") : merge.index("def main")]
    for bad in ("--force", '"-D"', '"-f"'):
        assert bad not in cleanup, bad


def test_ticket_module_is_importable():
    assert ticket.PHASES == ("todo", "in-progress", "done")
