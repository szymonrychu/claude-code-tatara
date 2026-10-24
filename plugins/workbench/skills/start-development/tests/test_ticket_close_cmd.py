"""ticket.py close: land check, rebase, verify, fast-forward, verify on main, close.json."""

import json
from pathlib import Path

import pytest
from ticket_repo_helpers import (
    branches,
    cli,
    commit_all,
    deliver,
    git,
    init_repo,
    integration_tree,
    mk_epic,
    mk_task,
    set_meta,
    started,
    task_path,
    ticket,
)


@pytest.fixture(autouse=True)
def private_suite_lock(tmp_path, monkeypatch):
    # close runs --verify under suite-lock.sh; the machine lock is held by whoever runs this suite
    monkeypatch.setenv("SUITE_LOCK_DIR", str(tmp_path / "lock"))
    monkeypatch.delenv("SUITE_LOCK_SLOTS", raising=False)


def ready(repo, root, tasks=("alpha", "beta"), verdict="pass"):
    """A started epic whose tasks committed on <epic> in the integration tree, then reviewed.
    deliver() commits the ticket change to main after the fork, as a real run does."""
    ep = started(repo, root, tasks)
    for t in tasks:
        deliver(repo, root, ep, t)
    assert cli("stage", ep, "review", "--root", root).returncode == 0
    notes = root.parent / "notes.txt"
    notes.write_text("All good.")
    r = cli("review", ep, "--verdict", verdict, "--notes-file", notes, "--root", root)
    assert r.returncode == 0, r.stderr
    notes.unlink()
    return ep


def sha(repo, ref):
    return git(repo, "rev-parse", ref).stdout.strip()


def close(root, ep, verify="true", *extra):
    return cli("close", ep, "--verify", verify, "--root", root, *extra)


def close_json(root, ep) -> dict:
    return json.loads((root / "in-progress" / ep / "close.json").read_text())


def test_close_without_containment_gate(repo, root):
    ep = ready(repo, root)
    # the verified heads are not on <epic> (say a fix round rewrote them): no MERGE-line gate
    wt = integration_tree(repo, ep)
    git(wt, "checkout", "-q", "-b", "side")
    (wt / "side.py").write_text("s = 1\n")
    git(wt, "add", "side.py")
    git(wt, "commit", "-m", "side")
    off_epic = sha(wt, "HEAD")
    git(wt, "checkout", "-q", ep)
    for t in ("alpha", "beta"):
        set_meta(task_path(root, ep, t), verified_head=off_epic)
    commit_all(repo, "verified heads off the epic")
    main_before = sha(repo, "main")
    r = close(root, ep, "false")
    assert r.returncode == 4, r.stdout + r.stderr
    assert "MERGE" not in r.stdout and sha(repo, "main") == main_before
    assert not (root / "in-progress" / ep / "close.json").exists()
    r = close(root, ep)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "MERGE" not in r.stdout
    assert git(repo, "merge-base", "--is-ancestor", ep, "main", check=False).returncode == 0
    assert (wt / "alpha.py").exists() and (repo / "beta.py").exists()
    assert close_json(root, ep)["mainVerify"]["passed"] is True


def test_close_refuses_unreviewed_epic(repo, root):
    ep = ready(repo, root, verdict="fail")
    r = close(root, ep)
    assert r.returncode == 1 and "not pass" in r.stderr


def test_close_failing_verify_never_moves_main(repo, root):
    ep = ready(repo, root)
    main_before = sha(repo, "main")
    r = close(root, ep, "false")
    assert r.returncode == 4, r.stdout + r.stderr
    assert sha(repo, "main") == main_before
    assert not (root / "in-progress" / ep / "close.json").exists()


def test_close_runs_verify_on_rebased_tip_before_main_moves(repo, root, tmp_path):
    ep = ready(repo, root)
    main_before = sha(repo, "main")
    log = tmp_path / "verify.log"
    cmd = f'echo "$(pwd -P) $(git rev-parse HEAD) $(git -C {repo} rev-parse main)" >> {log}'
    r = close(root, ep, cmd)
    assert r.returncode == 0, r.stdout + r.stderr
    rows = [ln.split() for ln in log.read_text().splitlines()]
    (tree, head, main_seen), (_, _, main_after) = rows
    assert Path(tree) == integration_tree(repo, ep).resolve()
    assert main_seen == main_before  # main had not moved when the rebased tip was verified
    assert head == sha(repo, ep) and main_after != main_before


def test_close_records_main_pre_ff_sha(repo, root, tmp_path):
    ep = ready(repo, root)
    main_before = sha(repo, "main")
    log = tmp_path / "verify.log"
    r = close(root, ep, f'echo "$PWD" >> {log}')
    assert r.returncode == 0, r.stdout + r.stderr
    rec = close_json(root, ep)
    assert rec["epic"] == ep and rec["base"] == "main"
    assert rec["baseBefore"] == main_before
    assert rec["baseAfter"] != main_before
    assert rec["epicTip"] == sha(repo, ep)
    assert git(repo, "merge-base", "--is-ancestor", rec["epicTip"], "main").returncode == 0
    assert rec["integrationVerify"]["passed"] is True
    assert rec["mainVerify"]["passed"] is True and rec["mainVerify"]["command"].startswith("echo")
    assert "at" in rec
    ran = [Path(x).resolve() for x in log.read_text().splitlines()]
    assert ran == [integration_tree(repo, ep).resolve(), repo.resolve()]
    assert json.dumps(rec, indent=2) in r.stdout
    assert f"ticket.py move {ep} done" in r.stdout
    assert ticket_subject(repo) == f"chore(ticket): {ep} close"


def ticket_subject(repo):
    return git(repo, "log", "-1", "--format=%s").stdout.strip()


def test_close_failing_main_verify_writes_record_and_exits_4(repo, root, tmp_path):
    ep = ready(repo, root)
    main_before = sha(repo, "main")
    flag = tmp_path / "ran-once"
    cmd = f"if [ -e {flag} ]; then exit 1; fi; touch {flag}"
    r = close(root, ep, cmd)
    assert r.returncode == 4, r.stdout + r.stderr
    rec = close_json(root, ep)
    assert rec["mainVerify"]["passed"] is False and rec["integrationVerify"]["passed"] is True
    assert rec["baseBefore"] == main_before
    assert main_before in r.stderr + r.stdout


def test_lifecycle_main_moved_close_then_move_done_cleans_all(repo, root):
    ep = ready(repo, root)
    # main moved after the fork (the chore(ticket) commits deliver() made), so close rewrites <epic>
    assert git(repo, "merge-base", "--is-ancestor", "main", ep, check=False).returncode != 0
    r = close(root, ep)
    assert r.returncode == 0, r.stdout + r.stderr
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 0, r.stdout + r.stderr
    assert branches(repo) == ["main"]
    assert not integration_tree(repo, ep).exists()
    for t in ("alpha", "beta"):
        assert not (repo / ".claude" / "worktrees" / f"{ep}-{t}").exists()
    assert (root / "done" / ep / "close.json").is_file()


def test_close_rerun_is_idempotent(repo, root):
    ep = ready(repo, root)
    assert close(root, ep).returncode == 0
    head, count = sha(repo, "HEAD"), git(repo, "rev-list", "--count", "HEAD").stdout
    recorded = (root / "in-progress" / ep / "close.json").read_text()
    r = close(root, ep, "false")
    assert r.returncode == 0, r.stdout + r.stderr
    assert json.loads(r.stdout) == json.loads(recorded)
    assert sha(repo, "HEAD") == head
    assert git(repo, "rev-list", "--count", "HEAD").stdout == count


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
    ep = mk_epic(root)
    p = mk_task(root, ep, "alpha")
    p.write_text(p.read_text().replace("repo: proj", "repo: svc"))
    commit_all(wb)
    assert cli("move", ep, "in-progress", "--root", root, "--owner", "t").returncode == 0
    itree = ticket._mod().worktrees_dir(wb) / ep / "svc"
    (itree / "alpha.py").write_text("a = 1\n")
    git(itree, "add", "alpha.py")
    git(itree, "commit", "-m", "feat: alpha")
    head = sha(itree, "HEAD")
    tp = task_path(root, ep, "alpha")
    set_meta(tp, status="done", verified_head=head)
    commit_all(wb, "deliver")
    assert cli("stage", ep, "review", "--root", root).returncode == 0
    notes = root.parent / "notes.txt"
    notes.write_text("ok")
    assert (
        cli("review", ep, "--verdict", "pass", "--notes-file", notes, "--root", root).returncode
        == 0
    )
    svc = wb / "code" / "svc"
    before = (sha(svc, "develop"), sha(svc, ep), sha(wb, "main"))
    r = close(root, ep)
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"component mode: close through the phase 6 MR from {ep}" in r.stdout
    assert (sha(svc, "develop"), sha(svc, ep), sha(wb, "main")) == before
    assert not (root / "in-progress" / ep / "close.json").exists()


def test_close_rerun_after_failed_main_verify_refreshes_record(repo, root, tmp_path):
    ep = ready(repo, root)
    main_before = sha(repo, "main")
    flag = tmp_path / "ran-once"
    assert close(root, ep, f"if [ -e {flag} ]; then exit 1; fi; touch {flag}").returncode == 4
    first = close_json(root, ep)
    moved = sha(repo, "main")
    assert moved != main_before
    r = close(root, ep, "false")
    assert r.returncode == 4, r.stdout + r.stderr
    assert "did not move" not in r.stderr
    assert main_before in r.stderr
    rec = close_json(root, ep)
    assert rec["baseBefore"] == main_before == first["baseBefore"]
    assert rec["baseAfter"] == first["baseAfter"]
    assert rec["mainVerify"]["passed"] is False and rec["mainVerify"]["command"] == "false"
    # only the close.json commit landed on main; the epic was not rebased or re-forwarded
    assert git(repo, "merge-base", "--is-ancestor", moved, "main").returncode == 0
    assert sha(repo, ep) == first["epicTip"]


def test_close_after_main_reset_records_fresh_base_before(repo, root):
    ep = ready(repo, root)
    main_before = sha(repo, "main")
    assert close(root, ep, "false").returncode == 4  # integration verify fails, no record
    flag = root.parent / "ran-once"
    assert close(root, ep, f"if [ -e {flag} ]; then exit 1; fi; touch {flag}").returncode == 4
    assert close_json(root, ep)["baseBefore"] == main_before
    # main is reset and gains a new commit, so the next close is a real rebase and fast-forward
    record = (root / "in-progress" / ep / "close.json").read_text()
    git(repo, "reset", "--hard", main_before)
    (root / "in-progress" / ep / "close.json").write_text(record)
    (repo / "extra.txt").write_text("x\n")
    commit_all(repo, "main extra")
    fresh = sha(repo, "main")
    assert fresh != main_before
    r = close(root, ep)
    assert r.returncode == 0, r.stdout + r.stderr
    rec = close_json(root, ep)
    assert rec["baseBefore"] == fresh
    assert git(repo, "merge-base", "--is-ancestor", rec["baseAfter"], "main").returncode == 0


def test_close_rebase_conflict_exits_1_and_main_stays(repo, root):
    ep = ready(repo, root)
    # main gains a conflicting alpha.py after the fork
    (repo / "alpha.py").write_text("alpha = 'main'\n")
    git(repo, "add", "alpha.py")
    git(repo, "commit", "-m", "main alpha")
    main_before = sha(repo, "main")
    r = close(root, ep)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "conflict" in r.stderr.lower()
    assert sha(repo, "main") == main_before
    assert not (root / "in-progress" / ep / "close.json").exists()
