"""ticket.py continue: auto-accept of judgement-free findings and --launch one-shot relaunch."""

# ruff: noqa: F811
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_ticket_continue import epic, meta, repo, root, write_ret  # noqa: E402,F401
from test_ticket_run import cli, commit_all, git  # noqa: E402


@pytest.fixture(autouse=True)
def private_suite_lock(tmp_path, monkeypatch):
    # --launch lands via merge.py --verify under suite-lock.sh; the runner holds the machine lock
    monkeypatch.setenv("SUITE_LOCK_DIR", str(tmp_path / "lock"))
    monkeypatch.delenv("SUITE_LOCK_SLOTS", raising=False)


def _head(repo):
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def _ret(repo, **alpha):
    a = {"id": "alpha", "branch": "b-alpha", "verified": True, "clean": False,
         "verification": {"head": _head(repo)}}  # fmt: skip
    a.update(alpha)
    beta = {"id": "beta", "branch": "b-beta", "verified": False, "clean": False}
    return {"run": "r1", "tasks": [a, beta], "escalated": []}


def _go(repo, root, epic, tmp_path, data, *extra):
    return cli("continue", epic, "--root", root, "--out-dir", tmp_path / "out",
               "--return", write_ret(repo, data), *extra)  # fmt: skip


def _rulings(root, epic):
    p = root / "in-progress" / epic / "rulings.json"
    return json.loads(p.read_text()) if p.is_file() else []


def test_auto_accepts_triage_rejected(repo, root, epic, tmp_path):
    data = _ret(repo, stopped="gate-repeat", triageRejected=True)
    r = _go(repo, root, epic, tmp_path, data)
    assert "alpha: auto-accepted (triageRejected)" in r.stdout.splitlines(), r.stdout + r.stderr
    assert meta(root, epic, "alpha")["status"] == "done"
    rs = [x for x in _rulings(root, epic) if x["task"] == "alpha"]
    assert len(rs) == 1 and rs[0]["reason"] == "auto-accepted: triageRejected"


def test_continue_auto_accepts_process_only(repo, root, epic, tmp_path):
    # a blocked stop keeps the status off done after apply; processOnly still qualifies
    data = _ret(repo, stopped="blocked", processOnly=True)
    r = _go(repo, root, epic, tmp_path, data)
    assert "alpha: auto-accepted (processOnly)" in r.stdout.splitlines(), r.stdout + r.stderr
    assert meta(root, epic, "alpha")["status"] == "done"
    rs = [x for x in _rulings(root, epic) if x["task"] == "alpha"]
    assert len(rs) == 1 and rs[0]["reason"] == "auto-accepted: processOnly"
    r2 = _go(repo, root, epic, tmp_path, data)
    assert "alpha: auto-accepted" not in r2.stdout
    assert len([x for x in _rulings(root, epic) if x["task"] == "alpha"]) == 1


def test_continue_auto_accepts_triage_rejected_only_when_verified(repo, root, epic, tmp_path):
    data = _ret(repo, triageRejected=True, verified=False)
    data["tasks"][0].pop("verification")
    r = _go(repo, root, epic, tmp_path, data)
    assert "auto-accepted" not in r.stdout
    assert meta(root, epic, "alpha")["status"] != "done"
    data = _ret(repo, processOnly=True, stopped="review-shallow")
    r = _go(repo, root, epic, tmp_path, data)
    assert "auto-accepted" not in r.stdout
    assert meta(root, epic, "alpha")["status"] != "done"


def test_auto_accept_rerun_records_nothing_twice(repo, root, epic, tmp_path):
    data = _ret(repo, stopped="gate-repeat", triageRejected=True)
    _go(repo, root, epic, tmp_path, data)
    _go(repo, root, epic, tmp_path, data)
    assert meta(root, epic, "alpha")["status"] == "done"
    assert len([x for x in _rulings(root, epic) if x["task"] == "alpha"]) == 1


def _alpha_commit(repo, epic):
    assert cli("worktrees", epic, "--root", repo / "docs" / "plans").returncode == 0
    wt = repo / ".claude" / "worktrees" / f"{epic}-alpha"
    (wt / "mine.txt").write_text("m")
    git(wt, "add", "-A")
    git(wt, "commit", "-m", "alpha work")
    return git(wt, "rev-parse", "HEAD").stdout.strip()


def _done_alpha(repo, root, epic, head, verify="true"):
    p = root / "in-progress" / epic / "tasks" / "alpha.md"
    import ticket

    doc = ticket.load(p.read_text(), p)
    doc.meta.update(status="done", verified_head=head)
    if verify is None:
        doc.meta.pop("verify", None)
    else:
        doc.meta["verify"] = verify
    p.write_text(ticket.dump(doc))
    commit_all(repo)


def test_launch_uses_task_verify(repo, root, epic, tmp_path):
    head = _alpha_commit(repo, epic)
    _done_alpha(repo, root, epic, head)
    out = tmp_path / "out"
    r = cli("continue", epic, "--root", root, "--out-dir", out, "--launch")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "MERGE" not in r.stdout
    lines = r.stdout.strip().splitlines()
    assert lines[-2].startswith("LAUNCH ") and lines[-2].endswith(f" {out / (epic + '-args.json')}")
    assert lines[-1].startswith("ARM python3 ")
    assert lines[-1].endswith("/skills/heartbeat/scripts/heartbeat.py --run <runId> --total 1")
    assert git(repo / ".claude" / "worktrees" / epic, "merge-base", "--is-ancestor", head, "HEAD")
    args = json.loads((out / f"{epic}-args.json").read_text())
    assert [x["id"] for x in args["tasks"]] == ["beta"]


def test_launch_keeps_merge_line_on_failure(repo, root, epic, tmp_path):
    head = _alpha_commit(repo, epic)
    _done_alpha(repo, root, epic, head)
    p = root / "in-progress" / epic / "tasks" / "alpha.md"
    import ticket

    doc = ticket.load(p.read_text(), p)
    doc.meta.update(verify="false")
    p.write_text(ticket.dump(doc))
    commit_all(repo)
    r = cli("continue", epic, "--root", root, "--out-dir", tmp_path / "out", "--launch")
    assert r.returncode == 2, r.stdout + r.stderr
    assert f"MERGE alpha --name {epic}-alpha --base {epic} --repo proj" in r.stdout.splitlines()
    assert "LAUNCH" not in r.stdout
    assert (repo / ".claude" / "worktrees" / f"{epic}-alpha").is_dir()


def _ret_with_command(head, command):
    verification = {"head": head, **({"command": command} if command else {})}
    return {
        "tasks": [{"id": "alpha", "verified": True, "clean": True, "verification": verification}]
    }


def test_launch_without_verify_uses_returned_verification_command(repo, root, epic, tmp_path):
    head = _alpha_commit(repo, epic)
    _done_alpha(repo, root, epic, head, verify=None)
    rj = write_ret(repo, _ret_with_command(head, "false"))
    out = tmp_path / "o"
    r = cli("continue", epic, "--root", root, "--out-dir", out, "--launch", "--return", rj)
    assert r.returncode == 2, r.stdout + r.stderr
    assert f"MERGE alpha --name {epic}-alpha" in r.stdout


def test_launch_lands_with_recorded_verification_command(repo, root, epic, tmp_path):
    head = _alpha_commit(repo, epic)
    _done_alpha(repo, root, epic, head, verify=None)
    rj = write_ret(repo, _ret_with_command(head, "true"))
    out = tmp_path / "o"
    r = cli("continue", epic, "--root", root, "--out-dir", out, "--launch", "--return", rj)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "alpha: landed" in r.stdout


def test_launch_without_any_verify_prints_merge(repo, root, epic, tmp_path):
    head = _alpha_commit(repo, epic)
    _done_alpha(repo, root, epic, head, verify=None)
    r = cli("continue", epic, "--root", root, "--out-dir", tmp_path / "o", "--launch")
    assert r.returncode == 2, r.stdout + r.stderr
    assert f"MERGE alpha --name {epic}-alpha --base {epic}" in r.stdout
    assert "landed" not in r.stdout
    tree = repo / ".claude" / "worktrees" / epic
    assert subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=tree).returncode


def test_without_launch_prints_no_launch_lines(repo, root, epic, tmp_path):
    r = cli("continue", epic, "--root", root, "--out-dir", tmp_path / "out")
    assert r.returncode == 0, r.stderr
    assert "LAUNCH" not in r.stdout and "ARM" not in r.stdout


def test_relaunch_args_hold_only_open_tasks(repo, root, epic, tmp_path):
    data = _ret(repo, stopped="gate-repeat", triageRejected=True)
    _go(repo, root, epic, tmp_path, data)
    args = json.loads((tmp_path / "out" / f"{epic}-args.json").read_text())
    assert "alpha" not in [x["id"] for x in args["tasks"]]
    assert "beta" in [x["id"] for x in args["tasks"]]


def test_launch_prints_launch_and_arm_lines(repo, root, epic, tmp_path):
    head = _alpha_commit(repo, epic)
    _done_alpha(repo, root, epic, head)
    out = tmp_path / "out"
    r = cli("continue", epic, "--root", root, "--out-dir", out, "--launch")
    assert r.returncode == 0, r.stdout + r.stderr
    lines = r.stdout.strip().splitlines()
    assert [x.split()[0] for x in lines if x.startswith(("LAUNCH", "ARM"))] == ["LAUNCH", "ARM"]
    assert lines[-2].startswith("LAUNCH ") and lines[-1].startswith("ARM python3 ")
