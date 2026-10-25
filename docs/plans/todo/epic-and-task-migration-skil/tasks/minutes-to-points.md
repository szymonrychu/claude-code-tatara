---
title: Minutes to points
status: todo
repo: workbench
value: "Old tasks' minute estimates map to storypoints by one tested rule"
files: [plugins/workbench/scripts/lib/calibration.py, plugins/workbench/scripts/tests/test_calibration.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 11
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Minutes to points

## Requirement

User request (verbatim, 2026-10-25): "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered."

User decision (verbatim): "Q2 Points for old tasks: nearest calibration.SEED bucket to the legacy `estimate` minutes (ties go to the smaller bucket); a task without a numeric legacy estimate gets no points and stays out of calibration."

Design D3: Points and expected values (Q2, Q3, Q4 amended) (verbatim):

- A task with a whole-number legacy `estimate` (minutes): `points` is
  `calibration.points_for_minutes(estimate)`, the SEED bucket whose minutes are nearest, ties to the
  smaller bucket (17 minutes is 1 point; 45 is 3; 46 is 5); `expected_minutes` keeps the legacy estimate
  (the planner's real estimate); `expected_tokens` is the SEED tokens of that bucket.
- A task without a legacy estimate but with a Notes line `Estimate: N points` (`retro.NOTES_POINTS`; all
  24 bootstrap tasks): `points` is N, `expected_minutes` and `expected_tokens` are `calibration.SEED[N]`;
  `points_actual` and the existing actuals stay as recorded (one task keeps points 5 against
  points_actual 3).
- Neither: `points`, `expected_minutes` and `expected_tokens` stay empty and the task stays out of
  calibration.
- A task that already has `points` keeps it and its expected values.
The same mapping applies in every phase (my call: Q3's reason, the planner's real estimate, holds for a
todo task too).

Reuse brief idea (verbatim): "noted: no minutes-to-bucket inverse exists; tie rule needed (nearest SEED minutes)"

## Acceptance conditions

- AC1: `calibration.points_for_minutes(m)` returns the SEED bucket whose minutes are nearest m, ties to the smaller bucket: 0, 5, 6, 11 and 17 give 1; 23 gives 2; 45 gives 3; 46 and 57 give 5; 90 gives 8; 120 and 500 give 13 [evidence: test:plugins/workbench/scripts/tests/test_calibration.py::test_points_for_minutes_nearest_seed]
- AC2: a negative number, a bool or a non-int raises ValueError [evidence: test:plugins/workbench/scripts/tests/test_calibration.py::test_points_for_minutes_rejects]
- AC3: the scripts suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

## Files

- `plugins/workbench/scripts/lib/calibration.py`
- `plugins/workbench/scripts/tests/test_calibration.py`

## Interfaces

- `calibration.points_for_minutes(minutes: int) -> int`, one of `calibration.POINTS` (plugins/workbench/scripts/lib/calibration.py); stdlib, Python 3.9 safe.

## Expected outcome

One tested function maps a legacy minutes estimate to its storypoints bucket; migrate (task migrate-dry-run) uses it.

## Steps

1. Read calibration.py and test_calibration.py. Write the two tests; run `cd plugins/workbench && pytest scripts/tests/test_calibration.py -q`: they fail (no function).
2. Implement over `SEED` and `POINTS`; run the verify once: `bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint`.
3. `git add`, commit, rerun the verify and quote its summary lines.

## Notes

- Estimate: 1 point: one pure function and a table test.
- Reuse (reuse brief): calibration.SEED and POINTS (calibration.py:19,14).
- The name must not contain `estimate`: the retirement pin in test_ticket_retired_run_loop.py forbids the `estimate` subcommand and any `estimator` file.
