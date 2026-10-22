"""ticket.py continue: auto-accept of judgement-free findings and --launch one-shot relaunch."""

# ruff: noqa: F811
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_ticket_continue import epic, meta, repo, root, write_ret  # noqa: E402,F401
from test_ticket_run import cli, commit_all, git  # noqa: E402


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


def test_auto_accepts_process_only_not_done(repo, root, epic, tmp_path):
    # blocked keeps the status off done after apply; processOnly still qualifies
    data = _ret(repo, stopped="gate-repeat", processOnly=True)
    data["escalated"] = [{"id": "alpha", "reason": "gate-repeat"}]
    r = _go(repo, root, epic, tmp_path, data)
    status = meta(root, epic, "alpha")["status"]
    assert status == "done", r.stdout + r.stderr


def test_never_auto_accepts_unverified_or_review_shallow(repo, root, epic, tmp_path):
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


def _done_alpha(repo, root, epic, head):
    p = root / "in-progress" / epic / "tasks" / "alpha.md"
    import ticket

    doc = ticket.load(p.read_text(), p)
    doc.meta.update(status="done", verified_head=head, verify="true")
    p.write_text(ticket.dump(doc))
    commit_all(repo)


def test_launch_lands_done_task_and_prints_launch_lines(repo, root, epic, tmp_path):
    head = _alpha_commit(repo, epic)
    _done_alpha(repo, root, epic, head)
    out = tmp_path / "out"
    r = cli("continue", epic, "--root", root, "--out-dir", out, "--launch")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "MERGE" not in r.stdout
    lines = r.stdout.strip().splitlines()
    assert lines[-2].startswith("LAUNCH ") and lines[-2].endswith(f" {out / (epic + '-args.json')}")
    assert (
        lines[-1].startswith("ARM python3 ")
        and lines[-1].endswith("/skills/heartbeat/scripts/heartbeat.py --run <runId> --total 1")
        or "--run" in lines[-1]
    )
    assert git(repo / ".claude" / "worktrees" / epic, "merge-base", "--is-ancestor", head, "HEAD")
    args = json.loads((out / f"{epic}-args.json").read_text())
    assert [x["id"] for x in args["tasks"]] == ["beta"]


def test_launch_failed_landing_keeps_merge_line(repo, root, epic, tmp_path):
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


def test_without_launch_prints_no_launch_lines(repo, root, epic, tmp_path):
    r = cli("continue", epic, "--root", root, "--out-dir", tmp_path / "out")
    assert r.returncode == 0, r.stderr
    assert "LAUNCH" not in r.stdout and "ARM" not in r.stdout


def test_args_never_hold_done_task(repo, root, epic, tmp_path):
    data = _ret(repo, stopped="gate-repeat", triageRejected=True)
    _go(repo, root, epic, tmp_path, data)
    args = json.loads((tmp_path / "out" / f"{epic}-args.json").read_text())
    assert "alpha" not in [x["id"] for x in args["tasks"]]
    assert "beta" in [x["id"] for x in args["tasks"]]
