---
title: ignored runs finished at
status: todo
repo: agents-schedule
value: "every terminal run records when it ended, including runs ignored at insert"
files: [src/agents_schedule/db/runs.py, tests/test_runs_repo.py]
verify: "uv run --frozen pytest tests/test_runs_repo.py tests/test_scheduler.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [scheduler-loop]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 673202
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# ignored runs finished at

## Requirement

A run inserted directly as `ignored` (the scheduler's overlap path, reason `previous_running`, through `agents_schedule.db.runs.insert_scheduled`) gets `finished_at` set at insert, the same as a run the dispatcher moves to `ignored` (`schedule_disabled`), so every terminal run (handled, failed, ignored) carries `finished_at` and the runs API and UI can show when it ended. Discovered by task scheduler-loop.

- `insert_scheduled` (and `insert_manual` if it can insert a terminal status) sets `finished_at = now()` whenever the inserted status is `ignored`.
- No change to the partial unique index or the ON CONFLICT target.

## Acceptance conditions

- AC1: a scheduled run inserted as ignored has finished_at set [evidence: test:tests/test_runs_repo.py::test_ignored_insert_sets_finished_at]
- AC2: a scheduled run inserted as new has no finished_at [evidence: test:tests/test_runs_repo.py::test_new_insert_has_no_finished_at]

## Files

- `src/agents_schedule/db/runs.py`
- `tests/test_runs_repo.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
