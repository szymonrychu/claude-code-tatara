#!/usr/bin/env python3
"""Count hook records and workbench block messages in Claude Code transcripts.

usage: hook-evidence.py <path>...   (.jsonl files, or directories searched recursively)
"""

import json
import sys
from collections import Counter
from pathlib import Path

USAGE = "usage: hook-evidence.py <path>...  (.jsonl files or directories searched recursively)"
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


def main(argv):
    if "--help" in argv or "-h" in argv:
        print(USAGE)
        return 0
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
