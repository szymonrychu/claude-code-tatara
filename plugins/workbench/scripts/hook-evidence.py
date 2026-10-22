#!/usr/bin/env python3
"""Count hook records and workbench block messages in Claude Code transcripts.

usage: hook-evidence.py <path>...   (.jsonl files, or directories searched recursively)
       hook-evidence.py --cache <run dir> [--json]   (prompt-cache probe verdict)
"""

import json
import sys
from collections import Counter
from pathlib import Path

USAGE = (
    "usage: hook-evidence.py <path>...  (.jsonl files or directories searched recursively)\n"
    "       hook-evidence.py --cache <run dir> [--json]"
)
CACHE_SAVING_BELOW = 5000
HOOK_NAMES = {
    "guard-bash:": "guard-bash",
    "uncommitted file": "commit-guard",
    "last verification ran on": "freshness-guard",
}


def walk(node, hooks, blocks):
    if isinstance(node, dict):
        if "hookEvent" in node:
            hooks[tuple(str(node.get(k, "-")) for k in ("type", "hookEvent", "command"))] += 1
        for v in node.values():
            walk(v, hooks, blocks)
    elif isinstance(node, list):
        for v in node:
            walk(v, hooks, blocks)
    elif isinstance(node, str):
        for marker in HOOK_NAMES:
            if marker in node:
                blocks[marker] += 1


def files_under(path):
    return sorted(path.rglob("*.jsonl")) if path.is_dir() else [path]


def agent_cache(transcript):
    """First assistant message's cache usage and the transcript cwd."""
    creation = read = cwd = None
    with open(transcript, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if cwd is None and isinstance(rec.get("cwd"), str):
                cwd = rec["cwd"]
            usage = (
                rec.get("message", {}).get("usage")
                if isinstance(rec.get("message"), dict)
                else None
            )
            if creation is None and rec.get("type") == "assistant" and isinstance(usage, dict):
                creation = usage.get("cache_creation_input_tokens", 0)
                read = usage.get("cache_read_input_tokens", 0)
            if cwd is not None and creation is not None:
                break
    return {"cacheCreation": creation, "cacheRead": read, "cwd": cwd}


def cache_report(run_dir):
    agents = []
    journal = run_dir / "journal.jsonl"
    for line in journal.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        label = rec.get("label", "")
        if rec.get("type") != "started" or not label.startswith("probe:cache:"):
            continue
        transcript = run_dir / f"agent-{rec.get('agentId')}.jsonl"
        info = (
            agent_cache(transcript)
            if transcript.exists()
            else {"cacheCreation": None, "cacheRead": None, "cwd": None}
        )
        agents.append({"label": label, **info})

    def created(kind):
        return [
            a["cacheCreation"] for a in agents if a["label"].startswith(f"probe:cache:{kind}#")
        ][1:3]

    def fmt(vals):
        return ",".join("?" if v is None else str(v) for v in vals)

    static, task = created("static"), created("task")
    saving = len(static) == 2 and all(v is not None and v < CACHE_SAVING_BELOW for v in static)
    verdict = f"CACHE {'saving' if saving else 'none'} static={fmt(static)} task={fmt(task)}"
    return agents, verdict


def cache_main(argv):
    paths = [a for a in argv if a not in ("--cache", "--json")]
    if len(paths) != 1:
        print(USAGE, file=sys.stderr)
        return 2
    run_dir = Path(paths[0])
    if not (run_dir / "journal.jsonl").is_file():
        print(f"no such path: {run_dir / 'journal.jsonl'}", file=sys.stderr)
        return 2
    agents, verdict = cache_report(run_dir)
    if "--json" in argv:
        print(json.dumps({"agents": agents, "verdict": verdict}))
        return 0
    for a in agents:
        fields = f"cacheCreation={a['cacheCreation']} cacheRead={a['cacheRead']} cwd={a['cwd']}"
        print(f"{a['label']}  {fields}")
    print(verdict)
    return 0


def main(argv):
    if "--help" in argv or "-h" in argv:
        print(USAGE)
        return 0
    if "--cache" in argv:
        return cache_main(argv)
    hooks, blocks, missing = Counter(), Counter(), False
    for arg in argv:
        path = Path(arg)
        if not path.exists():
            print(f"no such path: {arg}", file=sys.stderr)
            missing = True
            continue
        for f in files_under(path):
            with open(f, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    try:
                        walk(json.loads(line), hooks, blocks)
                    except ValueError:
                        continue
    for key, n in sorted(hooks.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"{n}  {' '.join(key)}")
    for marker, n in sorted(blocks.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"{n}  block: {marker}")
    seen = [name for marker, name in HOOK_NAMES.items() if blocks[marker]]
    print(f"workbench hooks seen: {', '.join(seen) if seen else 'none'}")
    return 2 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
