"""ticket.py task <epic> <task> --status: how the orchestrator records a task's outcome."""

import datetime
import json
import sys
from pathlib import Path

from ticket_repo_helpers import (
    cli,
    commit_all,
    git,
    last_subject,
    meta,
    mk_epic,
    mk_task,
    set_meta,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "lib"))
import agent_usage  # noqa: E402

TODAY = datetime.date.today().isoformat()
ACTUALS = ("actual_minutes", "actual_tokens", "actual_roles", "actual_role_tokens")


def usage_record(agent_id, epic, task, role, start, end, total, transcript=""):
    return {
        "agentId": agent_id,
        "agentType": f"workbench:{'implementer' if role == 'impl' else 'reviewer'}",
        "model": "claude-sonnet-5-5",
        "epic": epic,
        "task": task,
        "role": role,
        "transcript": transcript,
        "start": start,
        "end": end,
        "tokens": {
            "input": total,
            "cache_creation": 0,
            "cache_read": 0,
            "output": 0,
            "total": total,
        },
    }


def transcript_line(kind, ts, text=None, msg_id=None, tokens=0):
    if kind == "user":
        return json.dumps({"type": "user", "timestamp": ts, "message": {"content": text}})
    usage = {"input_tokens": tokens, "output_tokens": 0}
    message = {"id": msg_id, "model": "claude-opus-5-5", "usage": usage}
    return json.dumps({"type": "assistant", "timestamp": ts, "message": message})


def test_task_status_sets_fields_and_commits(repo, root):
    ep = mk_epic(root)
    p = mk_task(root, ep, "alpha")
    set_meta(p, owns=["legacy-part"], estimate="6")  # an old task file keeps its legacy keys
    commit_all(repo)
    (repo / "unrelated.txt").write_text("not mine")
    r = cli(
        "task",
        ep,
        "alpha",
        "--status",
        "done",
        "--verified-head",
        "abc123",
        "--note",
        "review clean",
        "--points-actual",
        "3",
        "--logs",
        repo.parent / "logs",
        "--root",
        root,
    )
    assert r.returncode == 0, r.stderr
    m = meta(p)
    assert m["status"] == "done" and m["verified_head"] == "abc123"
    assert m["owns"] == ["legacy-part"] and m["estimate"] == "6"
    notes = p.read_text().split("## Notes", 1)[1]
    assert f"- {TODAY} done: review clean" in notes
    assert last_subject(repo) == f"chore(ticket): {ep} task alpha done"
    files = git(repo, "show", "--name-only", "--format=").stdout.split()
    assert files == [str(p.relative_to(repo))]
    assert git(repo, "status", "--porcelain").stdout.strip() == "?? unrelated.txt"

    r = cli("task", ep, "alpha", "--status", "escalated", "--root", root)
    assert r.returncode == 0, r.stderr
    m = meta(p)
    assert m["status"] == "escalated" and m["verified_head"] == "abc123"
    assert f"- {TODAY} escalated" in p.read_text().split("## Notes", 1)[1]
    assert last_subject(repo) == f"chore(ticket): {ep} task alpha escalated"

    head = git(repo, "rev-parse", "HEAD").stdout
    r = cli("task", ep, "alpha", "--status", "finished", "--root", root)
    assert r.returncode == 1 and "finished" in r.stderr
    r = cli("task", ep, "ghost", "--status", "done", "--root", root)
    assert r.returncode == 1 and "ghost" in r.stderr
    assert git(repo, "rev-parse", "HEAD").stdout == head
    assert meta(p)["status"] == "escalated"


def test_done_stamps_actuals(repo, root, tmp_path):
    ep = mk_epic(root)
    p = mk_task(root, ep, "alpha")
    commit_all(repo)
    logs = tmp_path / "logs"
    # The implementer's transcript still exists, so its record is re-summarised: the stale
    # numbers in the record lose to the transcript. A fix round is a second user turn.
    transcript = tmp_path / "agent-impl.jsonl"
    transcript.write_text(
        "\n".join(
            [
                transcript_line("user", "2026-10-24T10:00:00.000Z", f"[wb {ep}/alpha/impl]\nGo"),
                transcript_line("assistant", "2026-10-24T10:05:00.000Z", msg_id="m1", tokens=100),
                transcript_line("user", "2026-10-24T10:20:00.000Z", "Fix the findings."),
                transcript_line("assistant", "2026-10-24T10:30:30.000Z", msg_id="m2", tokens=10),
            ]
        )
        + "\n"
    )
    stale = usage_record("impl1", ep, "alpha", "impl", "2026-10-24T09:00:00.000Z", None, 9)
    agent_usage.write_record(logs, dict(stale, transcript=str(transcript)))
    # The reviewer, continued after the fix round, spans 10:06:00 to 10:41:10.
    agent_usage.write_record(
        logs,
        usage_record(
            "rev1",
            ep,
            "alpha",
            "review",
            "2026-10-24T10:06:00.000Z",
            "2026-10-24T10:41:10.000Z",
            400,
        ),
    )
    r = cli(
        "task", ep, "alpha", "--status", "done", "--verified-head", "abc123",
        "--points-actual", "5", "--logs", logs, "--root", root,
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    m = meta(p)
    assert m["status"] == "done" and m["points_actual"] == "5"
    assert m["actual_minutes"] == "42"  # 10:00:00 to 10:41:10, ceiling minutes
    assert m["actual_tokens"] == "510"
    assert m["actual_roles"] == "impl 31, review 36"
    assert m["actual_role_tokens"] == "impl 110, review 400"
    assert "no agent records" not in p.read_text()
    assert last_subject(repo) == f"chore(ticket): {ep} task alpha done"
    files = git(repo, "show", "--name-only", "--format=").stdout.split()
    assert files == [str(p.relative_to(repo))]
    assert git(repo, "status", "--porcelain").stdout.strip() == ""


def test_done_requires_points_actual(repo, root, tmp_path):
    ep = mk_epic(root)
    p = mk_task(root, ep, "alpha")
    commit_all(repo)
    before, head = p.read_text(), git(repo, "rev-parse", "HEAD").stdout
    logs = tmp_path / "logs"
    for extra in ([], ["--points-actual", "4"], ["--points-actual", "x"], ["--points-actual", ""]):
        r = cli("task", ep, "alpha", "--status", "done", *extra, "--logs", logs, "--root", root)
        assert r.returncode != 0, extra
        assert "points-actual" in r.stderr or "points_actual" in r.stderr, r.stderr
        assert p.read_text() == before
        assert git(repo, "rev-parse", "HEAD").stdout == head
    assert not logs.exists()


def test_done_without_records_notes_it(repo, root, tmp_path):
    ep = mk_epic(root)
    p = mk_task(root, ep, "alpha")
    commit_all(repo)
    r = cli(
        "task", ep, "alpha", "--status", "done", "--points-actual", "2",
        "--logs", tmp_path / "empty-logs", "--root", root,
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    m = meta(p)
    assert m["status"] == "done" and m["points_actual"] == "2"
    for key in ACTUALS:
        assert m.get(key) in (None, ""), key
    notes = p.read_text().split("## Notes", 1)[1]
    assert f"- {TODAY} done" in notes
    assert f"- {TODAY} actuals: no agent records" in notes
    assert last_subject(repo) == f"chore(ticket): {ep} task alpha done"


def test_stamp_reads_only_its_task(repo, root, tmp_path):
    ep = mk_epic(root)
    alpha = mk_task(root, ep, "alpha")
    beta = mk_task(root, ep, "beta")
    commit_all(repo)
    logs = tmp_path / "logs"
    start, end = "2026-10-24T10:00:00.000Z", "2026-10-24T10:10:00.000Z"
    agent_usage.write_record(logs, usage_record("mine", ep, "alpha", "impl", start, end, 70))
    late = "2026-10-24T12:00:00.000Z"
    agent_usage.write_record(logs, usage_record("sib", ep, "beta", "impl", start, late, 900))
    far = usage_record("far", "other-epic", "alpha", "review", start, late, 800)
    agent_usage.write_record(logs, far)

    r = cli("task", ep, "beta", "--status", "escalated", "--logs", logs, "--root", root)
    assert r.returncode == 0, r.stderr
    m = meta(beta)
    assert m["status"] == "escalated"
    for key in ACTUALS + ("points_actual",):
        assert m.get(key) in (None, ""), key
    assert "no agent records" not in beta.read_text()
    head = git(repo, "rev-parse", "HEAD").stdout
    r = cli(
        "task", ep, "beta", "--status", "escalated", "--points-actual", "3",
        "--logs", logs, "--root", root,
    )  # fmt: skip
    assert r.returncode != 0 and "points-actual" in r.stderr
    assert git(repo, "rev-parse", "HEAD").stdout == head

    r = cli(
        "task", ep, "alpha", "--status", "done", "--points-actual", "3",
        "--logs", logs, "--root", root,
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    m = meta(alpha)
    assert m["actual_minutes"] == "10" and m["actual_tokens"] == "70"
    assert m["actual_roles"] == "impl 10" and m["actual_role_tokens"] == "impl 70"


def marked_transcripts(tmp_path, ep, task="alpha"):
    sub = tmp_path / "projects" / "-p" / "sess" / "subagents"
    sub.mkdir(parents=True)
    (sub / "agent-b1.jsonl").write_text(
        "\n".join(
            [
                transcript_line("user", "2026-10-24T10:00:00.000Z", f"[wb {ep}/{task}/impl]\nGo"),
                transcript_line("assistant", "2026-10-24T10:09:30.000Z", msg_id="m1", tokens=70),
            ]
        )
        + "\n"
    )
    return tmp_path / "projects" / "-p"


def test_done_backfills_before_stamping(repo, root, tmp_path):
    ep = mk_epic(root)
    p = mk_task(root, ep, "alpha")
    commit_all(repo)
    transcripts, logs = marked_transcripts(tmp_path, ep), tmp_path / "logs"
    r = cli(
        "task", ep, "alpha", "--status", "done", "--points-actual", "3",
        "--transcripts", transcripts, "--logs", logs, "--root", root,
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    m = meta(p)
    assert m["actual_minutes"] == "10" and m["actual_tokens"] == "70"
    assert m["actual_roles"] == "impl 10"
    assert "no agent records" not in p.read_text()
    assert (logs / "agents" / "b1.json").is_file()


def test_actuals_backfill_command(repo, root, tmp_path):
    ep = mk_epic(root)
    commit_all(repo)
    transcripts, logs = marked_transcripts(tmp_path, ep), tmp_path / "logs"
    args = ("actuals", ep, "--backfill", "--transcripts", transcripts, "--logs", logs)
    r = cli(*args, "--root", root)
    assert r.returncode == 0, r.stderr
    lines = r.stdout.strip().splitlines()
    assert lines == [f"b1 {ep}/alpha/impl 10 70"]
    again = cli(*args, "--root", root)
    assert again.returncode == 0 and again.stdout.strip() == ""
    assert cli(*args, "--refresh", "--root", root).stdout.strip() == lines[0]
    assert cli("actuals", ep, "--root", root).returncode != 0
