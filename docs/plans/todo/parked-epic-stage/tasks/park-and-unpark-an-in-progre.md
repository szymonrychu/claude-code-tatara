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

- ac1: `ticket.py stage <epic> parked` on an in-progress epic at stage build writes `stage: parked` and commits `chore(ticket): <epic> stage parked`; from `review` it refuses. [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_park.py]
- ac2: `ticket.py stage <epic> build` on a parked epic writes `stage: build`. [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_park.py]
- ac3: A new task sharing a file with a non-done task of a parked in-progress epic is created with no overlap failure; the same overlap against an unparked in-progress epic still fails. [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_park.py]
- ac4: Parking leaves the epic's integration worktree and branch in place. [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_park.py]
- ac5: `ticket.py lint` accepts `stage: parked`, and `stage <epic> review` refuses on a parked epic. [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_park.py]
- ac6: references/tickets.md documents `parked` in the stage command line and the epic lifecycle paragraph. [evidence: command:grep -n parked plugins/workbench/skills/start-development/references/tickets.md]
- ac7: The plugin test suite and lint stay green. [evidence: command:mise run test:plugin && mise run lint]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_park.py`
- `plugins/workbench/skills/start-development/references/tickets.md`

## Interfaces

- `ticket.py`: `EPIC_STAGES` gains `parked`; `cmd_stage` accepts `parked` (only from `build`) and `build` (from `parked` or `review`); `run_check` skips tasks of in-progress epics whose README `stage` is `parked`.

## Expected outcome

`ticket.py stage slash-commands-from-chat parked` succeeds, after which `ticket.py new-task` in another epic no longer fails on files shared with slash-commands-from-chat's unbuilt tasks.

## Steps

- Red: write tests/test_ticket_park.py covering ac1-ac5 (reuse fixtures from conftest.py and test_ticket_check.py / test_ticket_move.py); run the verify command, expect failures on the missing `parked` stage.
- Green: implement in ticket.py; run the verify command, expect all passed.
- Update references/tickets.md (stage command line and lifecycle paragraph); run `mise run test:plugin && mise run lint`, expect green.

## Notes

- Parking moves and deletes nothing (no git mv, no worktree removal). `move <epic> done` on a parked epic is out of scope (unchanged behaviour).
- No backward-compat shims. No em dashes.

- 2026-10-27 amended: AC format and filled sections
