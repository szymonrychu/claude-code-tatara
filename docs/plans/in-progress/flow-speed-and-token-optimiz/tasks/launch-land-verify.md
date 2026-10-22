---
title: Launch land verify
status: in-progress
repo: workbench
value: continue --launch never lands a task with no check
files: [plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py, plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py]
verify: "cd plugins/workbench && pytest skills/start-development/tests/test_ticket_continue_launch.py -q && ruff check skills"
depends_on: [audit-context-and-models, review-tiering, triage-one-call, flow-docs-update, cache-probe, cache-prefix-change]
owns: []
uses: []
model: sonnet
estimate: ""
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/flow-speed-and-token-optimiz--launch-land-verify
branch: flow-speed-and-token-optimiz--launch-land-verify
verified_head: ""
run: ""
provides: []
---

# Launch land verify

## Requirement

Epic review finding (2026-10-22): continue_cmd.py:157 passes `--verify`, `m.get("verify") or "true"` to merge.py, so a task with no `verify` field (allowed by D1, targeted verify) lands on the epic branch with no check.

Deliver: `ticket.py continue --launch` never passes `true` as the landing verify. A task with a `verify` field lands with it, as today. A task without one lands with the verified command recorded for it in the run return (`tasks[].verification.command`, the command plan-execute's landVerify uses). When neither exists, the task is not landed by continue: its `MERGE` line is printed for the worktree-merger, as for a failed landing.

## Acceptance conditions

- AC1: a task without verify whose run return records verification.command lands with that command [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_launch_lands_with_recorded_verification_command]
- AC2: a task with neither verify nor a recorded command is not landed and its MERGE line is printed [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_launch_without_any_verify_prints_merge]
- AC3: a task with verify still lands with its own verify [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_launch_uses_task_verify]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py`

## Interfaces

- `continue_cmd._land` takes the run return's per-task verification command into account; its output lines (`<task>: landed`, `MERGE ...`) keep their format.

## Expected outcome

Every landing that continue --launch performs runs a real verify command; tasks it cannot verify go to the worktree-merger.

## Steps

1. Write the three tests and see AC1 and AC2 fail.
2. Thread the run return's verification.command into _land; print MERGE when there is no command.
3. Run the verify command.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
