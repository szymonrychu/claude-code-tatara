"""agent_usage.py: per-agent time and tokens read from Claude subagent transcripts."""

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS / "lib"))
import agent_usage  # noqa: E402


def usage(inp, create, read, out):
    return {
        "input_tokens": inp,
        "cache_creation_input_tokens": create,
        "cache_read_input_tokens": read,
        "output_tokens": out,
        "service_tier": "standard",
    }


def assistant(ts, usage_, msg_id=None, request_id=None, model="claude-sonnet-5-5"):
    message = {"model": model, "role": "assistant", "content": [], "usage": usage_}
    if msg_id:
        message["id"] = msg_id
    line = {"type": "assistant", "timestamp": ts, "agentId": "a1", "message": message}
    if request_id:
        line["requestId"] = request_id
    return json.dumps(line)


def user(ts, content):
    return json.dumps(
        {
            "type": "user",
            "timestamp": ts,
            "agentId": "a1",
            "message": {"role": "user", "content": content},
        }
    )


def write(path: Path, lines) -> Path:
    path.write_text("".join(line + "\n" for line in lines))
    return path


def test_tokens_summed_once_per_message_id(tmp_path):
    lines = [
        user("2026-10-24T10:00:00.000Z", "[wb ep/t1/impl]\nDo it."),
        # One message split over three lines with identical usage: counted once.
        assistant("2026-10-24T10:00:01.000Z", usage(2, 100, 1000, 10), "msg_1", "req_1"),
        assistant("2026-10-24T10:00:02.000Z", usage(2, 100, 1000, 10), "msg_1", "req_1"),
        assistant("2026-10-24T10:00:03.000Z", usage(2, 100, 1000, 10), "msg_1", "req_1"),
        assistant("2026-10-24T10:00:04.000Z", usage(3, 200, 2000, 20), "msg_2", "req_2"),
        # No message.id: requestId is the key, so these two count once.
        assistant("2026-10-24T10:00:05.000Z", usage(1, 0, 500, 5), None, "req_3"),
        assistant("2026-10-24T10:00:06.000Z", usage(1, 0, 500, 5), None, "req_3"),
        # Neither id: each line stands alone.
        assistant("2026-10-24T10:00:07.000Z", usage(1, 1, 1, 1)),
        assistant("2026-10-24T10:00:08.000Z", usage(1, 1, 1, 1)),
    ]
    summary = agent_usage.summarize(write(tmp_path / "agent-a1.jsonl", lines))
    assert summary["tokens"] == {
        "input": 2 + 3 + 1 + 1 + 1,
        "cache_creation": 100 + 200 + 0 + 1 + 1,
        "cache_read": 1000 + 2000 + 500 + 1 + 1,
        "output": 10 + 20 + 5 + 1 + 1,
        "total": 3849,
    }
    assert summary["tokens"]["total"] == sum(
        summary["tokens"][k] for k in ("input", "cache_creation", "cache_read", "output")
    )


def test_summarize_tolerates_garbage(tmp_path):
    lines = [
        user("2026-10-24T10:00:00.000Z", "[wb ep/t1/impl]\nDo it."),
        "{not json",
        "",
        "[1, 2, 3]",
        json.dumps({"type": "attachment", "timestamp": "2026-10-24T10:00:00.500Z"}),
        json.dumps({"type": "api-request", "message": {"usage": usage(9, 9, 9, 9)}}),
        json.dumps({"type": "assistant", "timestamp": "2026-10-24T10:00:00.700Z", "message": "x"}),
        assistant("2026-10-24T10:00:01.000Z", usage(1, 2, 3, 4), "msg_1", model="claude-opus-5-5"),
        json.dumps({"type": "assistant", "message": {"id": "msg_2", "usage": "bad"}}),
        assistant("2026-10-24T10:05:00.000Z", usage(1, 2, 3, 4), "msg_3"),
        user("2026-10-24T10:06:00.000Z", [{"type": "tool_result", "content": "ok"}]),
    ]
    path = write(tmp_path / "agent-a1.jsonl", lines)
    with path.open("ab") as fh:
        fh.write(b'{"type": "assistant", \xff\xfe garbled tail\n')
    objects = list(agent_usage.transcript_lines(path))
    assert all(isinstance(o, dict) for o in objects)
    assert len(objects) == 8

    summary = agent_usage.summarize(path)
    assert summary["start"] == "2026-10-24T10:00:00.000Z"
    assert summary["end"] == "2026-10-24T10:06:00.000Z"
    assert summary["model"] == "claude-sonnet-5-5"
    assert summary["tokens"] == {
        "input": 2,
        "cache_creation": 4,
        "cache_read": 6,
        "output": 8,
        "total": 20,
    }

    missing = agent_usage.summarize(tmp_path / "nope.jsonl")
    assert missing["start"] is None and missing["end"] is None and missing["model"] is None
    assert missing["tokens"]["total"] == 0


def test_marker_and_role(tmp_path):
    marked = write(
        tmp_path / "m.jsonl",
        [
            json.dumps({"type": "attachment", "timestamp": "2026-10-24T10:00:00.000Z"}),
            user(
                "2026-10-24T10:00:00.000Z",
                "[wb housekeeping-rules-estimates/agent-usage-lib/review]\nReview.",
            ),
            user("2026-10-24T10:00:01.000Z", "[wb other/x/impl]"),
        ],
    )
    assert agent_usage.parse_marker(marked) == (
        "housekeeping-rules-estimates",
        "agent-usage-lib",
        "review",
    )
    listed = write(
        tmp_path / "l.jsonl",
        [user("2026-10-24T10:00:00.000Z", [{"type": "text", "text": "  [wb ep/t2/impl]\nGo"}])],
    )
    assert agent_usage.parse_marker(listed) == ("ep", "t2", "impl")
    # The marker must be on the first line of the first user message.
    later = write(
        tmp_path / "s.jsonl",
        [
            user("2026-10-24T10:00:00.000Z", "Implement this.\n[wb ep/t1/impl]"),
            user("2026-10-24T10:00:01.000Z", "[wb ep/t1/impl]"),
        ],
    )
    assert agent_usage.parse_marker(later) is None
    bad_role = write(tmp_path / "b.jsonl", [user("2026-10-24T10:00:00.000Z", "[wb ep/t1/fix]")])
    assert agent_usage.parse_marker(bad_role) is None
    assert agent_usage.parse_marker(tmp_path / "missing.jsonl") is None
    assert agent_usage.MARKER.match("[wb ep/t1/impl]")

    assert agent_usage.role_for("review", "workbench:implementer") == "review"
    assert agent_usage.role_for(None, "workbench:implementer") == "impl"
    assert agent_usage.role_for("", "workbench:reviewer") == "review"
    assert agent_usage.role_for(None, "general-purpose") == ""


def record(agent_id, epic="ep", task="t1", role="impl", transcript="", total=10, **extra):
    return {
        "agentId": agent_id,
        "agentType": "workbench:implementer",
        "model": "claude-sonnet-5-5",
        "epic": epic,
        "task": task,
        "role": role,
        "transcript": transcript,
        "start": "2026-10-24T09:00:00.000Z",
        "end": "2026-10-24T09:30:00.000Z",
        "tokens": {
            "input": total,
            "cache_creation": 0,
            "cache_read": 0,
            "output": 0,
            "total": total,
        },
        "updatedAt": "2026-10-24T09:30:00Z",
        **extra,
    }


def test_write_record_overwrites(tmp_path):
    logs = tmp_path / ".logs"
    first = agent_usage.write_record(logs, record("a1", total=10))
    second = agent_usage.write_record(logs, record("a1", total=99))
    assert first == second == logs / "agents" / "a1.json"
    assert sorted(p.name for p in (logs / "agents").iterdir()) == ["a1.json"]
    stored = json.loads(second.read_text())
    assert stored["tokens"]["total"] == 99
    assert stored == record("a1", total=99)


def test_read_records_resummarises(tmp_path):
    logs = tmp_path / ".logs"
    transcript = write(
        tmp_path / "agent-a1.jsonl",
        [
            user("2026-10-24T10:00:00.000Z", "[wb ep/t1/impl]\nGo"),
            assistant("2026-10-24T10:00:01.000Z", usage(1, 2, 3, 4), "msg_1"),
            assistant("2026-10-24T10:00:02.000Z", usage(1, 2, 3, 4), "msg_1"),
            assistant(
                "2026-10-24T10:20:00.000Z", usage(1, 1, 1, 1), "msg_2", model="claude-opus-5-5"
            ),
        ],
    )
    agent_usage.write_record(logs, record("a1", transcript=str(transcript), total=7))
    agent_usage.write_record(
        logs, record("a2", role="review", transcript=str(tmp_path / "gone.jsonl"), total=500)
    )
    agent_usage.write_record(logs, record("a3", task="t2", total=1))
    agent_usage.write_record(logs, record("a4", epic="other", total=1))
    (logs / "agents" / "garbled.json").write_text("{nope")
    (logs / "agents" / "notes.txt").write_text("ignored")

    rows = {r["agentId"]: r for r in agent_usage.read_records(logs, epic="ep", task="t1")}
    assert sorted(rows) == ["a1", "a2"]
    fresh = rows["a1"]
    assert fresh["start"] == "2026-10-24T10:00:00.000Z"
    assert fresh["end"] == "2026-10-24T10:20:00.000Z"
    assert fresh["model"] == "claude-opus-5-5"
    assert fresh["tokens"] == {
        "input": 2,
        "cache_creation": 3,
        "cache_read": 4,
        "output": 5,
        "total": 14,
    }
    kept = rows["a2"]
    assert kept["tokens"]["total"] == 500
    assert kept["start"] == "2026-10-24T09:00:00.000Z"
    assert kept["role"] == "review"

    assert sorted(r["agentId"] for r in agent_usage.read_records(logs, epic="ep")) == [
        "a1",
        "a2",
        "a3",
    ]
    assert len(agent_usage.read_records(logs)) == 4
    assert agent_usage.read_records(tmp_path / "no-logs") == []


def test_aggregate():
    def span(agent_id, start, end, total, role="impl", **extra):
        return record(agent_id, role=role, total=total, start=start, end=end, **extra)

    records = [
        # impl continued in a fix round: one agent, one record, 10:00:00 to 10:20:30 (1230 s).
        span("a1", "2026-10-24T10:00:00.000Z", "2026-10-24T10:20:30.000Z", 100),
        span("a2", "2026-10-24T10:21:00.000Z", "2026-10-24T10:30:10.000Z", 200, role="review"),
        # A second implementer, 541 s: impl minutes are the ceiling of the summed spans.
        span("a3", "2026-10-24T10:31:00.000Z", "2026-10-24T10:40:01.000Z", 50),
        # No marker role: the agent type decides.
        span(
            "a4",
            "2026-10-24T10:35:00.000Z",
            "2026-10-24T10:36:00.000Z",
            7,
            role="",
            agentType="workbench:reviewer",
        ),
        # No timestamps: its tokens count, its time cannot.
        span("a5", None, None, 3),
    ]
    assert agent_usage.aggregate(records) == {
        "minutes": 41,
        "tokens": 360,
        "roles": {"impl": (30, 153), "review": (11, 207)},
    }
    assert agent_usage.aggregate([]) == {"minutes": None, "tokens": 0, "roles": {}}


def backfill_fixture(tmp_path):
    """A transcripts dir shaped like the harness's: one marked agent, one unmarked."""
    sub = tmp_path / "projects" / "-p" / "sess1" / "subagents"
    sub.mkdir(parents=True)
    write(
        sub / "agent-m1.jsonl",
        [
            user("2026-10-24T10:00:00.000Z", "[wb ep/t1/impl]\nDo it."),
            assistant("2026-10-24T10:00:01.000Z", usage(2, 100, 1000, 10), "msg_1"),
            assistant("2026-10-24T10:00:02.000Z", usage(2, 100, 1000, 10), "msg_1"),
            assistant("2026-10-24T10:05:30.000Z", usage(3, 200, 2000, 20), "msg_2"),
        ],
    )
    (sub / "agent-m1.meta.json").write_text(json.dumps({"agentType": "workbench:implementer"}))
    write(
        sub / "agent-u1.jsonl",
        [
            user("2026-10-24T10:00:00.000Z", "No marker here."),
            assistant("2026-10-24T10:00:01.000Z", usage(1, 1, 1, 1), "msg_9"),
        ],
    )
    # Unmarked implementer naming a task file: only written when `names` is given.
    write(
        sub / "agent-u2.jsonl",
        [
            user("2026-10-24T11:00:00.000Z", "Work on /r/docs/plans/done/ep/tasks/t2.md now."),
            assistant("2026-10-24T11:00:01.000Z", usage(1, 1, 1, 1), "msg_8"),
        ],
    )
    (sub / "agent-u2.meta.json").write_text(json.dumps({"agentType": "workbench:implementer"}))
    return tmp_path / "projects" / "-p", tmp_path / "logs"


def test_backfill_writes_marked_only(tmp_path):
    transcripts, logs = backfill_fixture(tmp_path)
    written = agent_usage.backfill(transcripts, logs)
    assert [r["agentId"] for r in written] == ["m1"]
    assert sorted(p.name for p in (logs / "agents").glob("*.json")) == ["m1.json"]
    # with names, the unmarked implementer naming a task file is written too
    assert [r["agentId"] for r in agent_usage.backfill(transcripts, logs, names=NAMES)] == ["u2"]
    saved = json.loads((logs / "agents" / "m1.json").read_text())
    assert saved == written[0]
    assert (saved["epic"], saved["task"], saved["role"]) == ("ep", "t1", "impl")
    assert saved["agentType"] == "workbench:implementer"
    assert saved["model"] == "claude-sonnet-5-5"
    assert saved["start"] == "2026-10-24T10:00:00.000Z"
    assert saved["end"] == "2026-10-24T10:05:30.000Z"
    assert saved["transcript"].endswith("agent-m1.jsonl")
    assert saved["tokens"] == {
        "input": 5,
        "cache_creation": 300,
        "cache_read": 3000,
        "output": 30,
        "total": 3335,
    }


NAMES = {
    "ep/tasks/t1.md": ("ep", "t1"),
    "ep/tasks/t2.md": ("ep", "t2"),
    "ep--t1": ("ep", "t1"),
    "ep-t2": ("ep", "t2"),
    "ep": ("ep", None),
    "other/tasks/o1.md": ("other", "o1"),
}


def test_legacy_task_matches_one_task(tmp_path):
    def match(text):
        path = write(tmp_path / "x.jsonl", [user("2026-10-24T10:00:00.000Z", text)])
        return agent_usage.legacy_task(path, NAMES)

    assert match("Do /r/docs/plans/done/ep/tasks/t1.md") == ("ep", "t1")
    # a task file path wins over another task's tree name
    assert match("See ep/tasks/t1.md in .claude/worktrees/ep-t2") == ("ep", "t1")
    assert match("Tree /r/.claude/worktrees/ep--t1.") == ("ep", "t1")
    assert match("Branch ep-t2, tree ep-t2") == ("ep", "t2")
    # two task files, or two tree names, are ambiguous
    assert match("ep/tasks/t1.md and ep/tasks/t2.md") is None
    assert match("ep--t1 and ep-t2") is None
    # epic only, nothing, or a name embedded in a longer token
    assert match("worktrees/ep only") is None
    assert match("nothing here") is None
    assert match("ep--t1x and xep-t2") is None
    # only the first user prompt counts
    path = write(
        tmp_path / "y.jsonl",
        [user("2026-10-24T10:00:00.000Z", "hello"), user("2026-10-24T10:00:01.000Z", "ep--t1")],
    )
    assert agent_usage.legacy_task(path, NAMES) is None


def legacy_dir(tmp_path, nested=False):
    sub = tmp_path / "projects" / "-p" / "sess" / "subagents"
    if nested:
        sub = sub / "workflows" / "wf_1"
    sub.mkdir(parents=True)
    return sub


def legacy_agent(sub, agent_id, prompt, agent_type):
    write(
        sub / f"agent-{agent_id}.jsonl",
        [
            user("2026-10-24T10:00:00.000Z", prompt),
            assistant("2026-10-24T10:02:00.000Z", usage(1, 1, 1, 1), f"msg_{agent_id}"),
        ],
    )
    if agent_type is not None:
        (sub / f"agent-{agent_id}.meta.json").write_text(json.dumps({"agentType": agent_type}))


def test_backfill_matches_legacy_transcripts(tmp_path):
    sub = legacy_dir(tmp_path)
    legacy_agent(sub, "i1", "ep/tasks/t1.md", "workbench:implementer")
    legacy_agent(sub, "r1", "ep/tasks/t1.md", "workbench:reviewer")
    legacy_agent(sub, "v1", "ep-t2", "workbench:verifier")
    legacy_agent(sub, "o1", "other/tasks/o1.md", "workbench:implementer")
    transcripts, logs = tmp_path / "projects" / "-p", tmp_path / "logs"
    written = agent_usage.backfill(transcripts, logs, epic="ep", names=NAMES)
    got = {r["agentId"]: (r["epic"], r["task"], r["role"]) for r in written}
    assert got == {
        "i1": ("ep", "t1", "impl"),
        "r1": ("ep", "t1", "review"),
        "v1": ("ep", "t2", "review"),
    }
    saved = json.loads((logs / "agents" / "i1.json").read_text())
    assert saved["agentType"] == "workbench:implementer"
    assert saved["tokens"]["total"] == 4
    assert saved["start"] == "2026-10-24T10:00:00.000Z"
    assert not (logs / "agents" / "o1.json").exists()
    every = agent_usage.backfill(transcripts, tmp_path / "logs2", names=NAMES)
    assert sorted(r["agentId"] for r in every) == ["i1", "o1", "r1", "v1"]


def test_backfill_skips_unmatched_and_other_types(tmp_path):
    sub = legacy_dir(tmp_path)
    legacy_agent(sub, "n1", "no task named", "workbench:implementer")
    legacy_agent(sub, "n2", "ep/tasks/t1.md and ep/tasks/t2.md", "workbench:implementer")
    legacy_agent(sub, "n3", "only the epic ep", "workbench:reviewer")
    for i, kind in enumerate(
        ["workbench:worktree-merger", "general-purpose", "workbench:planner",
         "workbench:scope-auditor", "workbench:record-writer"]
    ):
        legacy_agent(sub, f"t{i}", "ep/tasks/t1.md", kind)
    legacy_agent(sub, "nm", "ep/tasks/t1.md", None)
    written = agent_usage.backfill(tmp_path / "projects" / "-p", tmp_path / "logs", names=NAMES)
    assert written == []
    assert not (tmp_path / "logs" / "agents").exists()


def test_backfill_reaches_workflow_transcripts(tmp_path):
    sub = legacy_dir(tmp_path, nested=True)
    legacy_agent(sub, "w1", "ep/tasks/t2.md", "workbench:reviewer")
    written = agent_usage.backfill(tmp_path / "projects" / "-p", tmp_path / "logs", names=NAMES)
    assert [(r["agentId"], r["task"], r["role"]) for r in written] == [("w1", "t2", "review")]
    assert written[0]["transcript"].endswith("wf_1/agent-w1.jsonl")


def test_backfill_marker_wins_over_names(tmp_path):
    sub = legacy_dir(tmp_path)
    legacy_agent(sub, "m9", "[wb ep/t1/impl]\nAlso see ep/tasks/t2.md", "workbench:reviewer")
    written = agent_usage.backfill(tmp_path / "projects" / "-p", tmp_path / "logs", names=NAMES)
    assert [(r["epic"], r["task"], r["role"]) for r in written] == [("ep", "t1", "impl")]


def test_backfill_is_idempotent(tmp_path):
    transcripts, logs = backfill_fixture(tmp_path)
    hook = {"agentId": "m1", "epic": "ep", "task": "t1", "role": "impl", "tokens": {"total": 1}}
    agent_usage.write_record(logs, hook)
    assert agent_usage.backfill(transcripts, logs) == []
    assert json.loads((logs / "agents" / "m1.json").read_text()) == hook
    (logs / "agents" / "m1.json").unlink()
    assert len(agent_usage.backfill(transcripts, logs)) == 1
    assert agent_usage.backfill(transcripts, logs) == []


def test_backfill_refresh_overwrites(tmp_path):
    transcripts, logs = backfill_fixture(tmp_path)
    agent_usage.write_record(
        logs, {"agentId": "m1", "epic": "ep", "task": "t1", "role": "impl", "tokens": {"total": 1}}
    )
    written = agent_usage.backfill(transcripts, logs, refresh=True)
    assert [r["agentId"] for r in written] == ["m1"]
    saved = json.loads((logs / "agents" / "m1.json").read_text())
    assert saved["tokens"]["total"] == 3335


def test_default_transcripts_dir(tmp_path):
    root = Path("/srv/proj/work bench/.git")
    want = tmp_path / ".claude" / "projects" / "-srv-proj-work-bench--git"
    assert agent_usage.default_transcripts_dir(root, home=tmp_path) == want


def test_records_for_backfills_only_when_empty(tmp_path):
    transcripts, logs = backfill_fixture(tmp_path)
    got = agent_usage.records_for("ep", "t1", logs, transcripts)
    assert [r["agentId"] for r in got] == ["m1"]
    assert (logs / "agents" / "m1.json").is_file()


def test_records_for_without_backfill_or_transcripts(tmp_path):
    transcripts, logs = backfill_fixture(tmp_path)
    assert agent_usage.records_for("ep", "t1", logs, transcripts, backfill=False) == []
    assert agent_usage.records_for("ep", "t1", logs, None) == []
    assert not logs.exists()


def test_records_for_keeps_existing_and_filters(tmp_path):
    transcripts, logs = backfill_fixture(tmp_path)
    hook = {"agentId": "h1", "epic": "ep", "task": "t1", "role": "impl", "tokens": {"total": 1}}
    agent_usage.write_record(logs, hook)
    assert agent_usage.records_for("ep", "t1", logs, transcripts) == [hook]
    assert not (logs / "agents" / "m1.json").exists()
    assert agent_usage.records_for("ep", "other", logs, transcripts, backfill=False) == []
    assert [r["agentId"] for r in agent_usage.records_for("ep", None, logs, None)] == ["h1"]
