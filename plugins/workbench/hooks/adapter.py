#!/usr/bin/env python3
"""One hook entry point for every non-Claude harness.

    python3 plugins/workbench/hooks/adapter.py --harness <h> --event <e> --hook <name>

Reads the harness's hook payload on stdin, normalizes it (`lib/harness_io.py`),
runs the shared guard logic (`lib/core.py` `decide`) and prints that harness's
JSON on stdout. Exit 0 allows. On a deny or a stop block it also writes the
reason to stderr and exits 2, the one deny signal Claude, Copilot, Cursor, Codex
and Gemini all document; Antigravity's exit codes are undocumented, so its JSON
`decision` is the signal there.

Fails closed on pre-tool: an unreadable payload or an internal error denies.
Post-tool and stop fail open, so a broken payload can never wedge a session.
An unknown harness, event or hook is a usage error: exit 2, usage on stderr.

Harness configs launch this from the repo root, so the plugin is found from this
file's own location, never from the cwd. Claude Code keeps its own entry scripts
(guard-bash.py and friends) over the same `lib/core.py`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.core import ALLOW, EVENTS, HOOKS, Decision, decide, write_verify_record  # noqa: E402
from lib.harness_io import HARNESSES, normalize, render  # noqa: E402


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="adapter.py",
        description="Run a workbench guard for a non-Claude harness (payload on stdin).",
    )
    parser.add_argument("--harness", required=True, choices=HARNESSES)
    parser.add_argument("--event", required=True, choices=EVENTS)
    parser.add_argument("--hook", required=True, choices=sorted(HOOKS))
    return parser.parse_args(argv)  # exits 2 with usage on stderr when invalid


def read_payload() -> dict[str, Any] | None:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def run(harness: str, event: str, hook: str, payload: dict[str, Any] | None) -> Decision:
    """The decision for one invocation, failing closed only on pre-tool."""
    if payload is None:
        if event == "pre-tool":
            return Decision("deny", f"{hook}: unreadable hook payload from {harness}; denied")
        return ALLOW
    try:
        decision = decide(hook, normalize(harness, event, payload))
        if hook == "verify-recorder":
            write_verify_record(decision.data)
    except Exception as exc:  # a broken guard must not let a tool call through
        if event == "pre-tool":
            return Decision("deny", f"{hook}: internal error ({exc}); denied")
        return ALLOW
    return decision


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    decision = run(args.harness, args.event, args.hook, read_payload())
    json.dump(render(args.harness, args.event, decision), sys.stdout)
    sys.stdout.write("\n")
    if decision.action == "allow":
        return 0
    print(decision.reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
