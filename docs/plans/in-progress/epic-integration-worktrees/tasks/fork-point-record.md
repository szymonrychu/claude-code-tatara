---
title: Fork point record
status: in-progress
repo: workbench
value: A later run diffs a landed task from the same fork point the landing recorded
files: [plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/tests/test_ticket_fork_point.py]
verify: "mise run test && mise run lint"
depends_on: [slug-collision-guard, fork-point-diffs]
owns: []
uses: [fork-point]
model: sonnet
estimate: 35
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/epic-integration-worktrees--fork-point-record
branch: epic-integration-worktrees--fork-point-record
verified_head: ""
run: ""
provides: []
---

# Fork point record

## Requirement

Persist each task's fork point across runs, so remediation and the epic-close audit in a later run still diff from it (interrogate verdict G; design D14).

- `ticket.py apply-run` writes task frontmatter `fork_point` from the return's `tasks[].forkPoint`, else from the matching `landed[].forkPoint`. When the return has neither, the recorded value is kept.
- `derive_tasks` exports `forkPoint` (from `fork_point`, `""` when absent), so `ticket.py args` and every args builder built on `derive_tasks` hand it to plan-execute.
- Applying the same return twice changes nothing the second time.

## Acceptance conditions

- AC1: apply-run records fork_point from the landed return [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_fork_point.py::test_apply_run_records_fork_point]
- AC2: a return without a fork point keeps the recorded value [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_fork_point.py::test_apply_run_keeps_fork_point_when_absent]
- AC3: ticket.py args hands forkPoint to the run [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_fork_point.py::test_args_carry_fork_point]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_fork_point.py`

## Interfaces

- Task frontmatter `fork_point` (a SHA, restricted format scalar) and `derive_tasks` field `forkPoint`; consumes the `fork-point` part from fork-point-diffs.

## Expected outcome

`ticket.py apply-run` on a return that landed a task writes its `fork_point`, and the next `ticket.py args` (or audit args) passes it back as `forkPoint`.

## Steps

- Red: write `plugins/workbench/skills/start-development/tests/test_ticket_fork_point.py` with the three AC tests; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_fork_point.py -q`; expect failures.
- Green: write `fork_point` in `cmd_apply_run` and export `forkPoint` in `derive_tasks`.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development`, then `mise run test && mise run lint` from the root.

## Notes

- `_write_task` keeps any frontmatter key; no whitelist changes.
- `ticket_cmds/args.py` builds tasks from `derive_tasks`, so it needs no change.
