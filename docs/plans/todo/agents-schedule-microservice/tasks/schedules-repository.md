---
title: schedules repository
status: todo
repo: agents-schedule
value: the api reads and writes schedules through one module that keeps armed_at right
files: [src/agents_schedule/db/schedules.py, tests/test_schedules_repo.py]
verify: "uv run --frozen pytest tests/test_schedules_repo.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [schema-migrations]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
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

- `agents_schedule.db.schedules`: `Schedule` (dataclass of the row), `create(conn, *, name, cron, timezone, preset_id, prompt, enabled) -> Schedule`, `get(conn, id) -> Schedule | None`, `list_all(conn)`, `list_enabled(conn)`, `update(conn, id, **fields) -> Schedule`, `delete(conn, id) -> None`, `ScheduleConflict`, `ScheduleNotFound` (part `sched-schedules-repo`).

## Expected outcome

Schedules are stored and edited with armed_at semantics the scheduler relies on.

## Steps

- Write tests/test_schedules_repo.py; run: fails.
- Write schedules.py; `uv run --frozen pytest tests/test_schedules_repo.py -q`: `4 passed`.
- Lint clean.

## Notes

- Only the api process calls the write functions (one writer per table).
