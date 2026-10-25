#!/usr/bin/env python3
"""SubagentStart / SubagentStop recorder: one usage record per subagent, Claude Code only.

Writes `<main checkout>/.logs/agents/<agentId>.json` (`workbench.logs_dir` from the event cwd,
so an agent working in an integration tree still records into the main checkout).

- SubagentStart (spawn and every resume) records the start time, agent id and type, the
  agent transcript path derived from `transcript_path` and `session_id`
  (`<dir>/<session_id>/subagents/agent-<agent_id>.jsonl`) and the run marker when the
  transcript is already readable. A resume keeps the first start.
- SubagentStop recomputes model, end and tokens from the whole agent transcript with
  `agent_usage.summarize` and overwrites the record, keeping the start the SubagentStart
  record holds. Stopping again (a fix round, a commit-guard refire) never double counts.

An empty `agent_type` (Claude Code's internal agents) writes nothing. The recorder makes no
decision: any error (garbled stdin, missing or garbled transcript, unwritable dir) exits 0
with no output, so it never blocks or disturbs a stop.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "lib"))

import agent_usage  # noqa: E402
import workbench  # noqa: E402


def _now() -> str:
    """UTC in the transcripts' own timestamp format, so the two compare as strings."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _text(payload: dict, key: str) -> str:
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def _existing(logs: Path, agent_id: str) -> dict:
    try:
        record = json.loads((logs / "agents" / f"{agent_id}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return record if isinstance(record, dict) else {}


def _derived_transcript(payload: dict, agent_id: str) -> str:
    main, session = _text(payload, "transcript_path"), _text(payload, "session_id")
    if not (main and session):
        return ""
    return str(Path(main).parent / session / "subagents" / f"agent-{agent_id}.jsonl")


def build_record(payload: dict, earlier: dict, now: str) -> dict | None:
    """The record to write for this event, or None when there is nothing to record."""
    agent_id, agent_type = _text(payload, "agent_id"), _text(payload, "agent_type")
    if not (agent_id and agent_type):
        return None
    stop = _text(payload, "hook_event_name") == "SubagentStop"
    transcript = (
        (_text(payload, "agent_transcript_path") if stop else "")
        or _derived_transcript(payload, agent_id)
        or earlier.get("transcript")
        or ""
    )
    readable = bool(transcript) and Path(transcript).is_file()

    record = dict(earlier)
    record.update(agentId=agent_id, agentType=agent_type, transcript=transcript, updatedAt=now)
    record.setdefault("start", None)
    for key in ("model", "epic", "task", "end"):
        record.setdefault(key, None)

    if stop:
        if not readable:
            return None
        summary = agent_usage.summarize(transcript)
        if summary["start"] is None and not summary["tokens"]["total"]:
            return None
        record.update(
            start=earlier.get("start") or summary["start"],
            end=summary["end"] or now,
            model=summary["model"] or record["model"],
            tokens=summary["tokens"],
        )
    else:
        record["start"] = earlier.get("start") or now

    marker = agent_usage.parse_marker(transcript) if readable else None
    if marker:
        record["epic"], record["task"] = marker[0], marker[1]
    record["role"] = agent_usage.role_for(marker[2] if marker else None, agent_type)
    return record


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict) or not (
            _text(payload, "agent_id") and _text(payload, "agent_type")
        ):
            return 0
        logs = workbench.logs_dir(Path(_text(payload, "cwd") or "."))
        if logs is None:
            return 0
        record = build_record(payload, _existing(logs, _text(payload, "agent_id")), _now())
        if record is not None:
            agent_usage.write_record(logs, record)
    except Exception:  # a recorder must never disturb the session
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
