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
