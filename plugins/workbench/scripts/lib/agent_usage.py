"""Per-agent time and tokens, read from Claude Code subagent transcripts.

A subagent transcript is JSONL at `<project>/<session>/subagents/agent-<id>.jsonl` under
the harness's projects dir (the path arrives in the hook payload). `assistant` lines
carry `timestamp`, `message.model` and `message.usage`; one message often spans several
lines with the same `message.id` and identical usage, so usage is counted once per id
(then `requestId`, then the line).
The first `user` line opens with the run marker `[wb <epic>/<task>/<role>]`.

Records live at `<logs>/agents/<agentId>.json`, one per agent, overwritten whole on
every write; `aggregate` turns one task's records into its actual minutes and tokens.
`backfill` writes the records the hook missed from the transcripts still on disk.
Stdlib only, Python 3.9 safe: the hooks import it.
"""

from __future__ import annotations

import datetime
import functools
import json
import math
import os
import re
import tempfile
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

import workbench

MARKER = re.compile(r"^\[wb ([^\s/\]]+)/([^\s/\]]+)/(impl|review)\]")

# Token components: record key -> usage key. Tokens are their sum (hooks brief finding 4).
TOKEN_KEYS = {
    "input": "input_tokens",
    "cache_creation": "cache_creation_input_tokens",
    "cache_read": "cache_read_input_tokens",
    "output": "output_tokens",
}

AGENT_ROLES = {"workbench:implementer": "impl", "workbench:reviewer": "review"}

# Agent types whose unmarked transcripts count for a task by name; the old verifier did
# the review's verification. Planner, merger, auditor and the rest name no task.
LEGACY_ROLES = {**AGENT_ROLES, "workbench:verifier": "review"}

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


def _first_text(content: Any) -> str | None:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                return text if isinstance(text, str) else None
    return None


def parse_marker(path: str | os.PathLike) -> tuple[str, str, str] | None:
    """(epic, task, role) from the first line of the first user message, or None."""
    for obj in transcript_lines(path):
        if obj.get("type") != "user":
            continue
        text = _first_text(_message(obj).get("content"))
        if text is None:
            return None
        lines = text.strip().splitlines()
        match = MARKER.match(lines[0].strip()) if lines else None
        return (match.group(1), match.group(2), match.group(3)) if match else None
    return None


@functools.lru_cache(maxsize=8)
def _name_pattern(keys: tuple) -> re.Pattern | None:
    """One alternation of the names, each bounded by characters that cannot extend a name."""
    if not keys:
        return None
    alternation = "|".join(re.escape(k) for k in sorted(keys, key=len, reverse=True))
    return re.compile(r"(?<![A-Za-z0-9_-])(?:" + alternation + r")(?![A-Za-z0-9_-])")


def legacy_task(
    path: str | os.PathLike, names: dict[str, tuple[str, str | None]]
) -> tuple[str, str] | None:
    """(epic, task) for an unmarked transcript whose first prompt names exactly one task.

    `names` maps a name to (epic, task or None). A task file path (`<epic>/tasks/<task>.md`)
    named once wins; else one task tree or branch name; two tasks at the deciding level,
    only an epic name, or no name give None.
    """
    pattern = _name_pattern(tuple(names))
    if pattern is None:
        return None
    for obj in transcript_lines(path):
        if obj.get("type") != "user":
            continue
        text = _first_text(_message(obj).get("content")) or ""
        files: set = set()
        trees: set = set()
        for found in pattern.finditer(text):
            name = found.group(0)
            epic, task = names[name]
            if task is None:
                continue
            (files if "/tasks/" in name and name.endswith(".md") else trees).add((epic, task))
        for level in (files, trees):
            if level:
                return next(iter(level)) if len(level) == 1 else None
        return None
    return None


def role_for(marker_role: str | None, agent_type: str | None) -> str:
    """The marker's role, else the role the agent type implies, else ''."""
    if marker_role:
        return marker_role
    return AGENT_ROLES.get(agent_type or "", "")


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


def read_records(
    logs_dir: str | os.PathLike, epic: str | None = None, task: str | None = None
) -> list[dict]:
    """Records matching epic and task, re-summarised from their transcript when it exists."""
    folder = Path(logs_dir) / "agents"
    records = []
    for path in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(record, dict):
            continue
        if epic is not None and record.get("epic") != epic:
            continue
        if task is not None and record.get("task") != task:
            continue
        transcript = record.get("transcript")
        if isinstance(transcript, str) and transcript and Path(transcript).is_file():
            summary = summarize(transcript)
            for key in ("start", "end", "model"):
                if summary[key] is not None:
                    record[key] = summary[key]
            record["tokens"] = summary["tokens"]
        records.append(record)
    return records


def _instant(stamp: Any) -> datetime.datetime | None:
    """An ISO timestamp (`Z` or offset) as an aware datetime, else None."""
    if not isinstance(stamp, str) or not stamp:
        return None
    try:
        when = datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    return when if when.tzinfo else when.replace(tzinfo=datetime.timezone.utc)


def _minutes(seconds: float) -> int:
    return math.ceil(seconds / 60)


def aggregate(records: list[dict]) -> dict:
    """One task's actuals from its agents' records.

    `minutes`: first start to last end across all agents, ceiling minutes (None without a
    timed agent). `tokens`: every agent's total. `roles`: role -> (minutes, tokens), the
    minutes the ceiling of the summed spans of that role's agents.
    """
    starts, ends = [], []
    role_seconds: dict[str, float] = {}
    role_tokens: dict[str, int] = {}
    total = 0
    for record in records:
        tokens = record.get("tokens")
        count = _count(tokens.get("total")) if isinstance(tokens, dict) else 0
        total += count
        role = role_for(record.get("role"), record.get("agentType"))
        start, end = _instant(record.get("start")), _instant(record.get("end"))
        seconds = 0.0
        if start and end and end >= start:
            starts.append(start)
            ends.append(end)
            seconds = (end - start).total_seconds()
        if role:
            role_seconds[role] = role_seconds.get(role, 0.0) + seconds
            role_tokens[role] = role_tokens.get(role, 0) + count
    minutes = _minutes((max(ends) - min(starts)).total_seconds()) if starts else None
    roles = {r: (_minutes(role_seconds[r]), role_tokens[r]) for r in role_seconds}
    return {"minutes": minutes, "tokens": total, "roles": roles}


def default_transcripts_dir(root: str | os.PathLike, home: str | os.PathLike | None = None) -> Path:
    """Where the harness keeps `root`'s sessions: projects/<root, non-alphanumerics as ->."""
    base = Path(home) if home is not None else Path.home()
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(root))
    return base / workbench.HARNESS_DIRS["claude"] / "projects" / slug


def _agent_type(transcript: Path, agent_id: str) -> str:
    try:
        meta = json.loads((transcript.parent / f"agent-{agent_id}.meta.json").read_text("utf-8"))
    except (OSError, ValueError):
        return ""
    value = meta.get("agentType") if isinstance(meta, dict) else None
    return value if isinstance(value, str) else ""


def backfill(
    transcripts_dir: str | os.PathLike,
    logs_dir: str | os.PathLike,
    refresh: bool = False,
    epic: str | None = None,
    names: dict[str, tuple[str, str | None]] | None = None,
) -> list[dict]:
    """Write the records the hook did not: one per marked `agent-*.jsonl` under the dir.

    Same summariser and record shape as the hook. An existing record is kept unless
    `refresh`; unmarked transcripts and (with `epic`) other epics' are skipped. With
    `names`, an unmarked implementer, reviewer or verifier transcript that `legacy_task`
    matches is recorded too (a marker still wins). Returns the records written.
    """
    folder = Path(logs_dir) / "agents"
    written = []
    for path in sorted(Path(transcripts_dir).rglob("agent-*.jsonl")):
        agent_id = path.name[len("agent-") : -len(".jsonl")]
        agent_type = _agent_type(path, agent_id)
        marker = parse_marker(path)
        if marker is None and names is not None and agent_type in LEGACY_ROLES:
            found = legacy_task(path, names)
            marker = (found[0], found[1], LEGACY_ROLES[agent_type]) if found else None
        if marker is None or (epic is not None and marker[0] != epic):
            continue
        if not refresh and (folder / f"{agent_id}.json").exists():
            continue
        summary = summarize(path)
        record = {
            "agentId": agent_id,
            "agentType": agent_type,
            "transcript": str(path),
            "updatedAt": summary["end"],
            "start": summary["start"],
            "end": summary["end"],
            "model": summary["model"],
            "epic": marker[0],
            "task": marker[1],
            "role": role_for(marker[2], agent_type),
            "tokens": summary["tokens"],
        }
        try:
            write_record(logs_dir, record)
        except ValueError:
            continue
        written.append(record)
    return written


_backfill = backfill  # records_for's `backfill` flag shadows the function


def records_for(
    epic: str,
    task: str | None,
    logs_dir: str | os.PathLike,
    transcripts_dir: str | os.PathLike | None,
    backfill: bool = True,
) -> list[dict]:
    """Records of `epic` (and `task`), backfilled from the transcripts when there are none.

    The one read, backfill-when-empty, read-again sequence. `backfill=False` or no
    transcripts dir only reads (the read-only `deltas`).
    """
    records = read_records(logs_dir, epic, task)
    if records or not backfill or not transcripts_dir:
        return records
    _backfill(transcripts_dir, logs_dir, epic=epic)
    return read_records(logs_dir, epic, task)


def records_by_task(
    epic: str,
    logs_dir: str | os.PathLike,
    transcripts_dir: str | os.PathLike | None,
    backfill: bool = True,
    names: dict[str, tuple[str, str | None]] | None = None,
    tasks: Iterable[str] | None = None,
) -> dict[str, list[dict]]:
    """`{task: [records]}` of `epic` from one read, one backfill at most, one more read.

    The backfill (with `names` passed through) runs only when a wanted task has no record:
    `tasks`, else the tasks `names` maps to this epic, else any task at all. `backfill=False`
    or no transcripts dir only reads.
    """
    records = read_records(logs_dir, epic)
    if backfill and transcripts_dir:
        if tasks is None and names is not None:
            tasks = {task for e, task in names.values() if e == epic and task}
        have = {r.get("task") for r in records}
        if (not records) if tasks is None else any(t not in have for t in tasks):
            _backfill(transcripts_dir, logs_dir, epic=epic, names=names)
            records = read_records(logs_dir, epic)
    grouped: dict[str, list[dict]] = {}
    for record in records:
        task = record.get("task")
        if isinstance(task, str):
            grouped.setdefault(task, []).append(record)
    return grouped
