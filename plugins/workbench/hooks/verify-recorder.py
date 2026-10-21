#!/usr/bin/env python3
"""PostToolUse / PostToolUseFailure recorder: remember the last verification run.

When an agent in a worktree runs a test or lint command, write what ran, on
which HEAD, whether the tree was dirty and whether it passed, to
`<git dir>/workbench-verify.json`. The SubagentStop guard reads that record and
refuses to let the agent stop on a stale or failed verification. Never prints,
never blocks, always exits 0.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.core import decide, from_claude_payload, write_verify_record  # noqa: E402


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if isinstance(payload, dict):
            write_verify_record(
                decide("verify-recorder", from_claude_payload(payload, "post-tool")).data
            )
    except Exception:  # a recorder must never disturb the session
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
