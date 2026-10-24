---
title: Calibration lib
status: todo
repo: workbench
value: "Expected minutes and tokens per storypoint come from measured history, not reasoning"
files: [plugins/workbench/scripts/lib/calibration.py, plugins/workbench/scripts/tests/test_calibration.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
---

# Calibration lib

## Requirement

User requirement (U4, verbatim): "scripting support getting deltas between complexity/time of delivery/tokens usage per task. New tools are meant to make the estimates more precise with time. Task table will be used for future estimates, retro table will be used to propose improvements for future work (also including workflow improvements). It must be seamless for the agent (taking over most of the estimation from agent's reasoning)."

Design D8: a stdlib module `plugins/workbench/scripts/lib/calibration.py` restores `_solve`, `refit` and `mdape` from `git show 7b187e8^:plugins/workbench/scripts/lib/estimator.py`, with storypoints as the regressor. `POINTS = (1, 2, 3, 5, 8, 13)`. Rows are plain dicts (`points`, `actual_minutes`, `actual_tokens`, optionally `expected_minutes`, `expected_tokens`, `points_actual`) as ints; rows missing points or either actual are ignored. `expected(points, rows) -> (minutes, tokens)`: the median of rows with that `points` when there are at least 3; else the least-squares line over all usable rows evaluated at `points` (rounded, at least 1) when there are at least 5; else the seed table. `bucket_table(rows)` returns, per points value, `minutes`, `tokens`, `n` and `source` (`history`, `refit` or `seed`). Design D15: the seed table is `SEED = {1: (11, 750000), 2: (23, 1500000), 3: (34, 2250000), 5: (57, 3750000), 8: (91, 6000000), 13: (147, 9750000)}` (probe of this machine's transcripts, a median task taken as 3 points, scaled linearly), unless the gate answer to Q2 changes it. The module name must not contain "estimator" (retirement pin).

## Acceptance conditions

- AC1: `_solve`, `refit` and `mdape` reproduce the restored behaviour: an exact line is recovered, a singular system returns None, MdAPE of known pairs matches, zero actuals are skipped [evidence: test:plugins/workbench/scripts/tests/test_calibration.py::test_refit_and_mdape]
- AC2: with 3 or more rows for a points value, `expected` returns their median minutes and tokens [evidence: test:plugins/workbench/scripts/tests/test_calibration.py::test_expected_uses_bucket_median]
- AC3: with fewer than 3 rows in the bucket and 5 or more usable rows, `expected` uses the refit line, rounded and at least 1 [evidence: test:plugins/workbench/scripts/tests/test_calibration.py::test_expected_falls_back_to_refit]
- AC4: with fewer than 5 usable rows, `expected` returns the seed values, and SEED equals the D15 table [evidence: test:plugins/workbench/scripts/tests/test_calibration.py::test_expected_falls_back_to_seed]
- AC5: `bucket_table` reports minutes, tokens, n and source for every points value; rows with missing or non-integer fields are ignored [evidence: test:plugins/workbench/scripts/tests/test_calibration.py::test_bucket_table_sources]
- AC6: no tracked file name contains "estimator" and the retirement pins hold [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py::test_run_loop_commands_retired]
- AC7: scripts and start-development suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

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
