---
title: Estimate fields
status: done
repo: workbench
value: Every task carries storypoints plus expected minutes and tokens for the price of one number
files: [plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/templates/task.md, plugins/workbench/skills/start-development/tests/test_ticket_files.py, plugins/workbench/skills/start-development/tests/test_ticket_lint.py, plugins/workbench/skills/start-development/references/tickets.md]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [calibration-lib]
model: opus
review: ""
verified_head: fb13db0
points_actual: 5
actual_minutes: 15
actual_tokens: 2032100
actual_roles: "impl 11, review 4"
actual_role_tokens: "impl 1914934, review 117166"
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

- `ticket.py:cmd_new_task` - new `--points` option; `ticket.py` new helper collecting calibration rows from done tasks (through `scan`), and a numeric field validator (restored `_minutes` from 7b187e8).
- `ticket.py:lint_problems` / `_task_problems` - numeric checks for non-done epics.
- `ticket.py:derive_tasks` - three more keys in each task dict.
- `calibration.expected`, `calibration.POINTS` from calibration-lib.

## Expected outcome

A planner passes one number; every new task file carries points plus expected minutes and tokens from history or the seed table.

## Steps

1. List the files under Files plus calibration.py, read them in one pass; write AC1-AC6 tests and run `pytest skills/start-development/tests/test_ticket_files.py skills/start-development/tests/test_ticket_lint.py -q` from plugins/workbench: they fail.
2. Implement; update the template and tickets.md; run the verify once.
3. Commit; leave the tree clean.

## Notes

- Estimate: 5 points.
- Reuse (brief): ticket.py:load/dump/_write_task (values are strings: digits dump bare and load back as "3"), `scan` (444) and `_tasks_of` (933) for history, `_template` (332). Do-not-build: a new frontmatter parser or writer.
- Restore (brief): the removed `_minutes` whole-minute validator and `_parse_roles`/`_format_roles` from `git show 7b187e8 -- plugins/workbench/skills/start-development/scripts/ticket.py`.
- Fix-as-ac (brief): LEAN_KEYS (test_ticket_files.py:161-172) is exact and asserted on new-task output (:194) and templates/task.md (:252); append together with cmd_new_task (ticket.py:400-410) and the CLI flags (ticket.py:1591-1595).
- Fix-as-ac (brief): lint cannot validate numbers today; lint_problems (1453) checks them; done-epic task problems stay skipped (:1489).
- Retirement pins: no `estimate` subcommand or key; the legacy `estimate` key of done tasks stays readable and is never written.

- 2026-10-24 done

- 2026-10-25 done
