---
title: park and unpark an in-progress epic
status: todo
repo: ""
value: Lets a reprioritised epic run ahead of a parked one
files: [plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/tests/test_ticket_park.py, plugins/workbench/skills/start-development/references/tickets.md]
verify: pytest plugins/workbench/skills/start-development/tests/test_ticket_park.py plugins/workbench/skills/start-development/tests/test_ticket_check.py plugins/workbench/skills/start-development/tests/test_ticket_lint.py -q
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 940114
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# park and unpark an in-progress epic

## Requirement

An in-progress epic can be parked and unparked: `ticket.py stage <epic> parked` sets the README `stage` to `parked` (allowed only from `build`), and `ticket.py stage <epic> build` unparks it. While an epic is parked, the cross-epic file overlap check (`run_check`, used by `new-task`, `check` and `move <epic> in-progress`) does not count that epic's tasks against other epics, because a parked epic is not building and will rebuild its unmerged work on top of main when it resumes. A parked epic keeps its integration branch and worktrees untouched (parking deletes and moves nothing). `stage <epic> review` refuses on a parked epic; lint accepts `parked` as a stage. Docs in references/tickets.md describe parking. Reason: 2026-10-27 the user reprioritised the session-loss incident and Matrix ahead of the parked slash-commands-from-chat epic, whose 18 unbuilt tasks block every overlapping new task.

## Acceptance conditions

- `ticket.py stage <epic> parked` on an in-progress epic at stage build writes `stage: parked` and commits `chore(ticket): <epic> stage parked`; from `review` it refuses. test: plugins/workbench/skills/start-development/tests/test_ticket_park.py
- `ticket.py stage <epic> build` on a parked epic writes `stage: build`. test: test_ticket_park.py
- A new task sharing a file with a non-done task of a parked in-progress epic is created (no overlap failure); the same overlap against an unparked in-progress epic still fails. test: test_ticket_park.py
- Parking leaves the epic's integration worktree and branch in place. test: test_ticket_park.py
- `ticket.py lint` accepts `stage: parked`, and `stage <epic> review` refuses on a parked epic. test: test_ticket_park.py
- references/tickets.md documents `parked` in the stage command line and the epic lifecycle paragraph. command: grep -n parked plugins/workbench/skills/start-development/references/tickets.md
- The whole plugin suite and lint stay green. command: mise run test:plugin && mise run lint

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_park.py`
- `plugins/workbench/skills/start-development/references/tickets.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
