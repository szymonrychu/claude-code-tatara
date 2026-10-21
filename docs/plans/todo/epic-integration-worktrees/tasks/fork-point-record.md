---
title: Fork point record
status: todo
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
worktree: ""
branch: ""
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
