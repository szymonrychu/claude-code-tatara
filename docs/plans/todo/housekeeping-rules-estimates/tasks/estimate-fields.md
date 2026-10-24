---
title: Estimate fields
status: todo
repo: workbench
value: Every task carries storypoints plus expected minutes and tokens for the price of one number
files: [plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/templates/task.md, plugins/workbench/skills/start-development/tests/test_ticket_files.py, plugins/workbench/skills/start-development/tests/test_ticket_lint.py, plugins/workbench/skills/start-development/references/tickets.md]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [calibration-lib]
model: opus
review: ""
verified_head: ""
---

# Estimate fields

## Requirement

User requirement (U2, verbatim): "each task consists also of: complexity estimate in storypoints; expected time; expected tokens"

User requirement (U4, verbatim, the seamless part): "It must be seamless for the agent (taking over most of the estimation from agent's reasoning)."

Design D7: task frontmatter appends, after `verified_head`, in this order: `points`, `expected_minutes`, `expected_tokens`, `points_actual`, `actual_minutes`, `actual_tokens`, `actual_roles`, `actual_role_tokens` (templates/task.md and the LEAN_KEYS pin change together). `ticket.py new-task --points N` takes Fibonacci storypoints (1, 2, 3, 5, 8, 13; anything else exits 1 naming the allowed values) and fills `expected_minutes` and `expected_tokens` from `calibration.expected(points, rows)`, where ticket.py collects the rows from every done task with integer `points`, `actual_minutes` and `actual_tokens`; the actual fields start empty. `ticket.py lint` checks, for tasks of todo and in-progress epics, that `points` and `points_actual` are Fibonacci and `expected_minutes`, `expected_tokens`, `actual_minutes` and `actual_tokens` are non-negative integers when set (values load as strings), and that `actual_roles` and `actual_role_tokens` match `impl N, review N` when set. `ticket.py tasks` JSON carries `points`, `expected_minutes` and `expected_tokens`. references/tickets.md documents the fields. No key or subcommand is named `estimate` (retirement pin). In this task `--points` is optional at the CLI (points-required makes it required with its callers).

## Acceptance conditions

- AC1: `new-task --points 5` with no history writes `points: 5` and the seed minutes and tokens for 5 [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_new_task_points_fill_expected]
- AC2: with 3 done tasks of 3 points carrying actuals, `new-task --points 3` writes their median minutes and tokens [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_new_task_expected_from_history]
- AC3: `--points 4` exits 1 naming the Fibonacci values and writes nothing [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_new_task_rejects_non_fibonacci_points]
- AC4: LEAN_KEYS is the ten old keys plus the eight new ones in order, for new-task output and templates/task.md [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_task_frontmatter_is_lean]
- AC5: lint reports a non-integer `expected_minutes`, a negative `actual_tokens`, a non-Fibonacci `points_actual` and a malformed `actual_roles` on an in-progress epic, and ignores a done epic [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_lint.py::test_lint_numeric_estimate_fields]
- AC6: `ticket.py tasks <epic>` JSON carries points, expected_minutes and expected_tokens per task [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_tasks_json_carries_estimates]
- AC7: references/tickets.md lists the eight new keys [evidence: command:grep -n "expected_tokens" plugins/workbench/skills/start-development/references/tickets.md]
- AC8: start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/templates/task.md`
- `plugins/workbench/skills/start-development/tests/test_ticket_files.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_lint.py`
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
