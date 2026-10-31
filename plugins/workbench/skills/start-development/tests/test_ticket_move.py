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
    cli,
    commit_all,
    git,
    last_subject,
    meta,
    mk_plan,
    plan_tree,
    set_meta,
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
