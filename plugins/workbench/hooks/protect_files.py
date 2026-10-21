#!/usr/bin/env python3
"""PreToolUse Edit|Write guardrail, Claude Code entry point.

Exit 2 blocks the tool (exit 1 does NOT block).

Blocks edits to secrets, terraform state, .git internals and encrypted secret
files. Stdin is the hook payload JSON (`tool_input.file_path`); anything
unparseable, or any internal error, is denied (exit 2); a payload without a path is
allowed. The patterns live in `lib/core.py`
(`decide("protect-files", ...)`) so every harness shares them; this script only
parses Claude's stdin and renders Claude's output.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 9):  # noqa: UP036 - fail closed: a crash here would exit 1, which does not block
    print("protect-files: python >= 3.9 required for hooks, denying", file=sys.stderr)
    sys.exit(2)

import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.core import decide, from_claude_payload  # noqa: E402


def _deny(reason: str) -> int:
    print(reason.replace("\n", " "), file=sys.stderr)
    return 2


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return _deny("protect-files: payload is not a JSON object, denying")
        event = from_claude_payload(payload, "pre-tool", default_kind="edit")
        decision = decide("protect-files", event)
    except Exception as exc:  # fail closed: exit 1 would not block
        return _deny(f"protect-files: {type(exc).__name__} while evaluating, denying")
    if decision.action == "allow":
        return 0
    print(decision.reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
