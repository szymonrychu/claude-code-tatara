"""Per-agent time and tokens, read from Claude Code subagent transcripts.

A subagent transcript is JSONL at `<project>/<session>/subagents/agent-<id>.jsonl` under
the harness's projects dir (the path arrives in the hook payload). `assistant` lines
carry `timestamp`, `message.model` and `message.usage`; one message often spans several
lines with the same `message.id` and identical usage, so usage is counted once per id
(then `requestId`, then the line).

Records live at `<logs>/agents/<agentId>.json`, one per agent, overwritten whole on
every write by the agent-usage-recorder hook, which is the only user of this module besides
the hooks' transcript walker. Stdlib only, Python 3.9 safe: the hooks import it.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

# Token components: record key -> usage key. Tokens are their sum (hooks brief finding 4).
TOKEN_KEYS = {
    "input": "input_tokens",
    "cache_creation": "cache_creation_input_tokens",
    "cache_read": "cache_read_input_tokens",
    "output": "output_tokens",
}

_AGENT_ID = re.compile(r"^[A-Za-z0-9_.-]+$")


def transcript_lines(path: str | os.PathLike) -> Iterator[dict]:
    """Each JSON object of a transcript; unreadable files and garbled lines are skipped."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if isinstance(obj, dict):
                    yield obj
    except OSError:
        return


def _message(obj: dict) -> dict:
    message = obj.get("message")
    return message if isinstance(message, dict) else {}


def _count(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else 0


def summarize(path: str | os.PathLike) -> dict:
    """First and last timestamp, last assistant model, and tokens once per message."""
    start = end = model = None
    usages: dict[Any, dict] = {}
    for index, obj in enumerate(transcript_lines(path)):
        stamp = obj.get("timestamp")
        if isinstance(stamp, str) and stamp:
            start = start or stamp
            end = stamp
        if obj.get("type") != "assistant":
            continue
        message = _message(obj)
        if isinstance(message.get("model"), str) and message["model"]:
            model = message["model"]
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        key = message.get("id") or obj.get("requestId") or ("line", index)
        usages[key] = usage
    tokens = {
        name: sum(_count(usage.get(field)) for usage in usages.values())
        for name, field in TOKEN_KEYS.items()
    }
    tokens["total"] = sum(tokens.values())
    return {"start": start, "end": end, "model": model, "tokens": tokens}


def write_record(logs_dir: str | os.PathLike, record: dict) -> Path:
    """Write `<logs>/agents/<agentId>.json` as an atomic overwrite."""
    agent_id = record.get("agentId")
    if not isinstance(agent_id, str) or not _AGENT_ID.match(agent_id) or agent_id in {".", ".."}:
        raise ValueError(f"agent_usage: unusable agentId {agent_id!r}")
    folder = Path(logs_dir) / "agents"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{agent_id}.json"
    fd, tmp = tempfile.mkstemp(prefix=f".{agent_id}.", suffix=".tmp", dir=str(folder))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, target)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return target
