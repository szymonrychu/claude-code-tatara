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
        user("2026-10-24T10:00:00.000Z", "Do it."),
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
        user("2026-10-24T10:00:00.000Z", "Do it."),
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


def test_no_role_concept():
    assert not hasattr(agent_usage, "role_for")
    assert not hasattr(agent_usage, "AGENT_ROLES")
    assert not hasattr(agent_usage, "parse_marker")
