#!/usr/bin/env python3
"""SubagentStop guard, Claude Code entry point (logic in `lib/core.py`).

A subagent may not end its turn holding uncommitted work.

An orchestration run had five independent subagents end their turn with a
bare "waiting on the background run, will report when it completes" while
their worktree held 11, 14 and 118 dirty files and zero commits. Every one
of them had been briefed to commit verified work and to bound any wait, and the
brief even cited two earlier agents that had lost a full run's work to a spend
limit for exactly this. The instruction lost to the "end the turn while a
background task runs" reflex five times out of five, so the rule is mechanical
now: the turn does not end while the worktree is dirty.

Scope is deliberately narrow - only worktrees an agent was given
(`<config dir>/worktrees/<name>` from worktree-create, task and integration trees
under `<config dir>/worktrees/<branch>/<repo>`; `.worktrees/<branch>/<repo>` is the
legacy layout from git-worktrees-create). The main checkout belongs to the human and is never
blocked. The guard fires once: a payload with `stop_hook_active` set means the
agent already got this message, and the turn is allowed to end so nothing can
wedge.

Policy sources: the plugin's rules/boy-scout.md ("Functional but uncommitted
work gets committed") and rules/concise-orchestrator.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.core import decide, from_claude_payload  # noqa: E402


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0

    decision = decide("subagent-commit-guard", from_claude_payload(payload, "stop"))
    if decision.action == "block":
        json.dump({"decision": "block", "reason": decision.reason}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
