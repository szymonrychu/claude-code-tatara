#!/usr/bin/env python3
"""PreToolUse Bash guardrail, Claude Code entry point.

Emits a JSON `permissionDecision: deny` (with a reason the model can act on)
for destructive or policy-violating commands. Unlike a settings.json `deny`
entry, this inspects each segment of a compound command, so
`foo && terraform destroy` is caught the same as a bare `terraform destroy`.

The rules live in `lib/core.py` (`decide("guard-bash", ...)`) so every harness
shares them; this script only parses Claude's stdin and renders Claude's output.

Runs alongside bash-output-filter.py. A deny from any hook wins, so the two
never conflict.

Policy sources: the plugin's own rules/terraform.md and rules/sops.md
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 9):  # noqa: UP036 - fail closed: a crash here would exit 1, which does not block
    print("guard-bash: python >= 3.9 required for hooks, denying", file=sys.stderr)
    sys.exit(2)

import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.core import decide, from_claude_payload  # noqa: E402


def _deny(reason: str) -> int:
    print(reason.replace("\n", " "), file=sys.stderr)
    return 2


def main() -> int:
    # Fail closed: exit 1 is non-blocking in Claude Code, so any parse failure or
    # unexpected exception exits 2 with a one-line stderr reason.
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            return _deny("guard-bash: payload is not a JSON object, denying")
        decision = decide("guard-bash", from_claude_payload(data, "pre-tool", default_kind="shell"))
    except Exception as exc:
        return _deny(f"guard-bash: {type(exc).__name__} while evaluating, denying")
    if decision.action != "allow":
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": decision.reason,
                    }
                }
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
