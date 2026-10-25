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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
