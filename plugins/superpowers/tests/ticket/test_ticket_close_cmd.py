"""ticket.py close: retro gate, rebase, verify, fast-forward, verify on main, close.json, the
move to done and the sweep, in one fixed order."""

import json
from pathlib import Path

import pytest
from ticket_repo_helpers import (
    branches,
    cli,
    deliver,
    git,
    init_repo,
    mk_plan,
    plan_tree,
    started,
    ticket,
    write_retro,
)

RECORD_KEYS = {
    "plan",
    "base",
    "baseBefore",
    "baseAfter",
    "planTip",
    "integrationVerify",
    "mainVerify",
    "at",
}


@pytest.fixture(autouse=True)
def private_suite_lock(tmp_path, monkeypatch):
    # close runs --verify under suite-lock.sh; the machine lock is held by whoever runs this suite
    monkeypatch.setenv("SUITE_LOCK_DIR", str(tmp_path / "lock"))
    monkeypatch.delenv("SUITE_LOCK_SLOTS", raising=False)


def ready(repo, root, steps=("alpha", "beta"), retro=True):
    """A started plan whose steps committed on <plan> in the plan tree, review passed (retro.md
    written, not committed). main moved after the fork (the claim commit)."""
    plan = started(repo, root)
    for s in steps:
        deliver(repo, plan, s)
    if retro:
        write_retro(root, plan)
    return plan


def sha(repo, ref):
    return git(repo, "rev-parse", ref).stdout.strip()


def close(root, plan, verify="true", *extra):
    return cli("close", plan, "--verify", verify, "--root", root, *extra)


def record(root, plan, phase="done") -> dict:
    return json.loads((root / phase / plan / "close.json").read_text())


def subject(repo):
    return git(repo, "log", "-1", "--format=%s").stdout.strip()


def test_close_refuses_without_retro(repo, root):
    plan = ready(repo, root, retro=False)
    main_before = sha(repo, "main")
    r = close(root, plan)
    assert r.returncode == 1
    assert f"plan {plan!r} has no retro.md; the reviewer writes it when the review passes" in (
        r.stderr
    )
    assert sha(repo, "main") == main_before and (root / "in-progress" / plan).is_dir()


def test_close_refuses_a_plan_not_in_progress(repo, root):
    plan = mk_plan(root)
    r = close(root, plan)
    assert r.returncode == 1
    assert f"plan {plan!r} is in todo; close needs it in-progress" in r.stderr


def test_close_failing_verify_never_moves_main_or_the_plan(repo, root):
    plan = ready(repo, root)
    main_before = sha(repo, "main")
    r = close(root, plan, "false")
    assert r.returncode == 4, r.stdout + r.stderr
    assert f"verify failed on the rebased {plan!r} tip" in r.stderr
    assert sha(repo, "main") == main_before
    assert (root / "in-progress" / plan / "retro.md").is_file()
    assert not (root / "in-progress" / plan / "close.json").exists()
    assert plan_tree(repo, plan).is_dir()


def test_close_runs_verify_on_rebased_tip_before_main_moves(repo, root, tmp_path):
    plan = ready(repo, root)
    main_before = sha(repo, "main")
    log = tmp_path / "verify.log"
    cmd = f'echo "$(pwd -P) $(git rev-parse HEAD) $(git -C {repo} rev-parse main)" >> {log}'
    r = close(root, plan, cmd)
    assert r.returncode == 0, r.stdout + r.stderr
    rows = [ln.split() for ln in log.read_text().splitlines()]
    (tree, head, main_seen), (main_tree, _, main_after) = rows
    assert Path(tree) == plan_tree(repo, plan).resolve()
    assert Path(main_tree) == repo.resolve()
    assert main_seen == main_before  # main had not moved when the rebased tip was verified
    assert head == record(root, plan)["planTip"] and main_after != main_before


def test_close_records_moves_to_done_commits_and_sweeps(repo, root):
    plan = ready(repo, root)
    main_before = sha(repo, "main")
    r = close(root, plan)
    assert r.returncode == 0, r.stdout + r.stderr
    rec = record(root, plan)
    assert set(rec) == RECORD_KEYS
    assert rec["plan"] == plan and rec["base"] == "main"
    assert rec["baseBefore"] == main_before and rec["baseAfter"] != main_before
    assert git(repo, "merge-base", "--is-ancestor", rec["planTip"], "main").returncode == 0
    assert rec["integrationVerify"] == {"command": "true", "passed": True}
    assert rec["mainVerify"]["passed"] is True and rec["mainVerify"]["command"] == "true"
    assert json.dumps(rec, indent=2) in r.stdout
    # one commit: close.json, retro.md and the move to done
    assert subject(repo) == f"chore(ticket): {plan} close"
    stat = git(repo, "show", "--name-status", "--format=", "HEAD").stdout.split("\n")
    added = sorted(ln.split("\t")[-1] for ln in stat if ln.startswith("A"))
    assert added == [f"docs/plans/done/{plan}/close.json", f"docs/plans/done/{plan}/retro.md"]
    assert any(ln.startswith("R") and ln.endswith(f"done/{plan}/plan.md") for ln in stat)
    assert not (root / "in-progress" / plan).exists()
    assert git(repo, "status", "--porcelain").stdout.strip() == ""
    # then the sweep: tree and branch gone
    assert not plan_tree(repo, plan).exists() and branches(repo) == ["main"]
    assert (repo / "alpha.py").is_file() and (repo / "beta.py").is_file()


def test_close_failing_main_verify_records_and_exits_4_without_moving(repo, root, tmp_path):
    plan = ready(repo, root)
    main_before = sha(repo, "main")
    flag = tmp_path / "ran-once"
    r = close(root, plan, f"if [ -e {flag} ]; then exit 1; fi; touch {flag}")
    assert r.returncode == 4, r.stdout + r.stderr
    rec = record(root, plan, "in-progress")
    assert rec["mainVerify"]["passed"] is False and rec["integrationVerify"]["passed"] is True
    assert rec["baseBefore"] == main_before and main_before in r.stderr
    assert (root / "in-progress" / plan / "retro.md").is_file()
    assert not (root / "done").exists()
    assert subject(repo) == f"chore(ticket): {plan} close verify failed"
    assert plan_tree(repo, plan).is_dir()


def test_close_rerun_after_failed_main_verify_keeps_base_before_then_closes(repo, root, tmp_path):
    plan = ready(repo, root)
    main_before = sha(repo, "main")
    flag = tmp_path / "ran-once"
    assert close(root, plan, f"if [ -e {flag} ]; then exit 1; fi; touch {flag}").returncode == 4
    first = record(root, plan, "in-progress")
    r = close(root, plan, "false")
    assert r.returncode == 4, r.stdout + r.stderr
    assert "did not move" not in r.stderr and main_before in r.stderr
    again = record(root, plan, "in-progress")
    assert again["baseBefore"] == main_before == first["baseBefore"]
    assert again["baseAfter"] == first["baseAfter"]
    assert again["mainVerify"]["command"] == "false"
    r = close(root, plan)
    assert r.returncode == 0, r.stdout + r.stderr
    rec = record(root, plan)
    assert rec["baseBefore"] == main_before and rec["mainVerify"]["passed"] is True
    assert rec["planTip"] == first["planTip"]
    assert subject(repo) == f"chore(ticket): {plan} close"
    assert not plan_tree(repo, plan).exists()


def test_close_rerun_after_success_is_a_no_op(repo, root):
    plan = ready(repo, root)
    assert close(root, plan).returncode == 0
    head = sha(repo, "HEAD")
    recorded = (root / "done" / plan / "close.json").read_text()
    r = close(root, plan, "false")
    assert r.returncode == 0, r.stdout + r.stderr
    assert json.loads(r.stdout) == json.loads(recorded)
    assert sha(repo, "HEAD") == head


def test_close_rebase_conflict_exits_1_and_main_stays(repo, root):
    plan = ready(repo, root)
    (repo / "alpha.py").write_text("alpha = 'main'\n")
    git(repo, "add", "alpha.py")
    git(repo, "commit", "-m", "main alpha")
    main_before = sha(repo, "main")
    r = close(root, plan)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "conflict" in r.stderr.lower()
    assert sha(repo, "main") == main_before
    assert not (root / "in-progress" / plan / "close.json").exists()


def test_close_refuses_a_meta_plan_without_its_branch(repo, root):
    plan = ready(repo, root)
    git(repo, "worktree", "remove", str(plan_tree(repo, plan)))
    git(repo, "branch", "-D", plan)
    r = close(root, plan)
    assert r.returncode == 1 and f"plan {plan!r} has no branch {plan!r} to close" in r.stderr


# ---------------------------------------------------------------- component mode


@pytest.fixture
def wb(tmp_path):
    w = init_repo(tmp_path / "wb")
    c = init_repo(w / "code" / "svc")
    git(c, "branch", "develop")
    (w / ".gitmodules").write_text(
        '[submodule "svc"]\n\tpath = code/svc\n\turl = x\n\tbranch = develop\n'
    )
    (w / ".gitignore").write_text("code/\n.claude/\n")
    git(w, "add", ".gitmodules", ".gitignore")
    git(w, "commit", "-m", "mods")
    return w


def test_close_component_mode_moves_nothing(wb):
    root = wb / "docs" / "plans"
    plan = mk_plan(root, repos="svc")
    assert cli("move", plan, "in-progress", "--root", root, "--owner", "t").returncode == 0
    tree = ticket._mod().worktrees_dir(wb) / plan / "svc"
    (tree / "alpha.py").write_text("a = 1\n")
    git(tree, "add", "alpha.py")
    git(tree, "commit", "-m", "feat: alpha")
    svc = wb / "code" / "svc"
    r = close(root, plan)
    assert r.returncode == 1 and "has no retro.md" in r.stderr
    write_retro(root, plan)
    before = (sha(svc, "develop"), sha(svc, plan), sha(wb, "main"))
    r = close(root, plan)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (
        f"component mode: {plan} closes through its MR; then run ticket.py move {plan} done"
        in r.stdout
    )
    assert (sha(svc, "develop"), sha(svc, plan), sha(wb, "main")) == before
    assert (root / "in-progress" / plan).is_dir()
    assert not (root / "in-progress" / plan / "close.json").exists()
