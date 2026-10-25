---
title: schedules repository
status: todo
repo: agents-schedule
value: the api reads and writes schedules through one module that keeps armed_at right
files: [src/agents_schedule/db/schedules.py, tests/test_schedules_repo.py]
verify: "uv run --frozen pytest tests/test_schedules_repo.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [schema-migrations]
owns: [sched-schedules-repo]
uses: [sched-schema, sched-db-fixture]
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# schedules repository

## Requirement

Add `agents_schedule.db.schedules` (design D3; approval A2): `create`, `get`, `list_all` (by name), `list_enabled`, `update` (full replace of name, cron, timezone, preset_id, prompt, enabled), `delete`. `armed_at` is set to now on create, and on update when `enabled` goes false to true or when `cron` or `timezone` changes; otherwise it is unchanged, so editing the prompt never triggers a catch-up run. A duplicate name raises `ScheduleConflict`; a missing id returns None (get) or raises `ScheduleNotFound` (update, delete). Values arrive validated (the api calls `sched-cron`); the repository does not parse cron.

## Acceptance conditions

- AC1: create, get, list and delete round-trip a schedule [evidence: test:tests/test_schedules_repo.py::test_crud_round_trip]
- AC2: a duplicate name raises ScheduleConflict [evidence: test:tests/test_schedules_repo.py::test_duplicate_name_conflicts]
- AC3: armed_at moves on enable and on cron or timezone change, and stays on a prompt edit [evidence: test:tests/test_schedules_repo.py::test_armed_at_rules]
- AC4: update or delete of a missing id raises ScheduleNotFound [evidence: test:tests/test_schedules_repo.py::test_missing_id]

## Files

- `src/agents_schedule/db/schedules.py`
- `tests/test_schedules_repo.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
