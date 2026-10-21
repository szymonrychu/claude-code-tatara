#!/usr/bin/env python3
"""Heartbeat for a waiting orchestrator: one short line per beat, run under Monitor.

Each printed line is a Monitor event, which wakes the orchestrator for one turn.
That turn re-reads the cached prompt prefix, so on a 5-minute cache TTL a beat
every 270s keeps the cache warm through an idle wait. On a 1-hour TTL the cache
needs no help, so the beat only reports progress at the bounded-wait interval.

Optional: one haiku call per beat (~600 tokens) estimates % done and ETA from a
digest of a plan-execute journal.jsonl.

Usage (from Monitor, timeout_ms 1800000, re-arm on expiry):
  heartbeat.py (--run <runId> | --journal <journal.jsonl>) [--total N] [--remaining-min M]
               [--ttl auto|5m|1h] [--interval S] [--stall-beats N] [--no-eta]
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SETTINGS = [
    Path.home() / ".claude" / "settings.json",
    Path.home() / ".claude" / "settings.local.json",
]
ESTIMATE_RE = re.compile(r"\b(\d{1,3})% ETA (\d+)m\b")


def detect_ttl(env, settings_paths=SETTINGS):
    """Main-conversation prompt-cache TTL, per code.claude.com/docs/en/prompt-caching."""
    if env.get("FORCE_PROMPT_CACHING_5M") == "1":
        return "5m"
    if env.get("CLAUDE_CODE_PROMPT_CACHE_TTL") in ("5m", "1h"):
        return env["CLAUDE_CODE_PROMPT_CACHE_TTL"]
    for p in settings_paths:
        try:
            v = json.loads(Path(p).read_text()).get("promptCacheTtl")
        except (OSError, ValueError, AttributeError):
            continue
        if v in ("5m", "1h"):
            return v
    if env.get("ENABLE_PROMPT_CACHING_1H") == "1":
        return "1h"
    if env.get("ANTHROPIC_API_KEY"):
        return "5m"
    return "1h"


def default_interval(ttl, keepalive=False):
    # Keepalive is opt-in (see SKILL.md for when it pays): only then, and only on
    # a 5m TTL, beat inside the TTL with margin. Otherwise report at the
    # 10-minute bounded-wait interval the global rules already require.
    return 270 if keepalive and ttl == "5m" else 600


def projects_root(override=None):
    env = os.environ.get("CLAUDE_PROJECTS_DIR")
    return Path(override or env or Path.home() / ".claude" / "projects")


def run_paths(run_id, projects=None):
    """(run record, journal) of a workflow run under the projects root; None while absent."""
    root = projects_root(projects)
    rec = next(iter(sorted(root.glob(f"*/*/workflows/{run_id}.json"))), None)
    jr = next(iter(sorted(root.glob(f"*/*/subagents/workflows/{run_id}/journal.jsonl"))), None)
    return rec, jr


def fmt_duration(ms):
    s = round(ms / 1000)
    return f"{s}s" if s < 60 else f"{s // 60}m{s % 60:02d}s"


def end_line(record_path):
    try:
        rec = json.loads(Path(record_path).read_text())
    except (OSError, ValueError):
        rec = {}
    tasks = ((rec.get("result") or {}).get("tasks")) or []
    done = sum(
        1
        for t in tasks
        if t.get("verified") and (t.get("clean") or t.get("processOnly")) and not t.get("stopped")
    )
    dur = fmt_duration(rec.get("durationMs") or 0)
    return f"END {rec.get('status', 'unknown')} {done}/{len(tasks)} tasks {dur}"


def digest(journal):
    started, finished = {}, set()
    for line in Path(journal).read_text().splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "started":
            started[e.get("agentId")] = e.get("label") or "?"
        elif e.get("type") == "result":
            finished.add(e.get("agentId"))
    running = [
        ":".join(lbl.split(":")[1:]) or lbl for a, lbl in started.items() if a not in finished
    ]
    # latest step per task, from labels <run>:<role>:<short>[#round][+cont]
    tasks = {}
    for a, lbl in started.items():
        parts = lbl.split(":")
        if len(parts) < 3:
            continue
        m = re.match(r"([a-z0-9-]+)(.*)$", parts[2])
        short, suffix = (m.group(1), m.group(2)) if m else (parts[2], "")
        tasks[short] = f"{parts[1]}{suffix} {'done' if a in finished else 'running'}"
    return {
        "started": len(started),
        "finished": len(finished & set(started)),
        "running": running,
        "tasks": tasks,
    }


def beat_line(d, estimate=None):
    extra = len(d["running"]) - 3
    run = ", ".join(d["running"][:3]) + (f" +{extra}" if extra > 0 else "")
    parts = [estimate] if estimate else []
    parts.append(f"{d['finished']}/{d['started']} agents")
    if run:
        parts.append(f"run: {run}")
    return " | ".join(parts)[:100]


def estimate(d, total=None, env=None, elapsed_min=None, remaining_min=None):
    prompt = (
        f"Agents started {d['started']}, finished {d['finished']}, "
        f"running: {', '.join(d['running']) or 'none'}. "
        + (
            f"Remaining estimate: {remaining_min} min. "
            if remaining_min
            else (f"Plan tasks: {total}. " if total else "")
        )
        + "Latest step per task: "
        + "; ".join(f"{k}: {v}" for k, v in d.get("tasks", {}).items())
        + ". "
        + (f"Elapsed: {elapsed_min}m. " if elapsed_min is not None else "")
        + "Each task runs impl, then review unless small, sometimes fix; unlisted tasks are "
        "queued; a final audit follows. "
        "Reply with exactly: NN% ETA Nm"
    )
    cmd = [
        "claude", "-p", "--model", "haiku", "--no-session-persistence",
        "--system-prompt", "You estimate workflow progress. One line, no other text.",
        "--tools", "", "--setting-sources", "", "--strict-mcp-config",
        "--disable-slash-commands", "--output-format", "json",
    ]  # fmt: skip
    try:
        out = subprocess.run(
            cmd, input=prompt, capture_output=True, text=True, timeout=60, env=env
        ).stdout
        m = ESTIMATE_RE.search(json.loads(out).get("result", ""))
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return f"~{min(int(m.group(1)), 100)}% done/{m.group(2)}m left" if m else None


def parse(argv=None):
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--journal")
    src.add_argument("--run", help="workflow run id: waits for its journal, ends with the run")
    ap.add_argument("--projects-dir", help="projects root for --run (env CLAUDE_PROJECTS_DIR)")
    ap.add_argument("--wait-max", type=float, default=10, help="minutes to wait for --run")
    ap.add_argument("--total", type=int)
    ap.add_argument("--remaining-min", type=int, help="remaining estimate (min), epic Time section")
    ap.add_argument("--ttl", default="auto", choices=["auto", "5m", "1h"])
    ap.add_argument("--interval", type=float)
    ap.add_argument("--stall-beats", type=int, default=3)
    ap.add_argument("--beats", type=int, default=0, help="stop after N beats (0 = until killed)")
    ap.add_argument("--no-eta", action="store_true")
    ap.add_argument("--keepalive", action="store_true", help="beat every 270s on a 5m cache")
    return ap.parse_args(argv)


def resolve_interval(a):
    if a.interval is not None:
        return a.interval
    return default_interval(detect_ttl(os.environ) if a.ttl == "auto" else a.ttl, a.keepalive)


def main(argv=None):
    a = parse(argv)
    interval = resolve_interval(a)
    t0, last_size, still, n = time.time(), -1, 0, 0
    while not a.beats or n < a.beats:
        n += 1
        if a.run:
            rec, jr = run_paths(a.run, a.projects_dir)
            if rec:
                print(end_line(rec), flush=True)
                return 0
            if not jr:
                if time.time() - t0 > a.wait_max * 60:
                    print(
                        f"END run {a.run} not found under {projects_root(a.projects_dir)}: "
                        "the runtime layout may have changed",
                        flush=True,
                    )
                    return 2
                print(f"waiting for run {a.run}", flush=True)
                if not a.beats or n < a.beats:
                    time.sleep(interval)
                continue
            j = jr
        else:
            j = Path(a.journal)
            if not j.is_file():
                print("END no journal", flush=True)
                return 0
        size = j.stat().st_size
        still = still + 1 if size == last_size else 0
        last_size = size
        if still >= a.stall_beats:
            print(f"STALL {round(still * interval / 60)}m no journal change", flush=True)
        else:
            d = digest(j)
            est = (
                None
                if a.no_eta
                else estimate(
                    d,
                    a.total,
                    elapsed_min=round((time.time() - t0) / 60),
                    remaining_min=a.remaining_min,
                )
            )
            print(beat_line(d, est), flush=True)
        if not a.beats or n < a.beats:
            time.sleep(interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
