---
title: sched schedule owner
status: todo
repo: agents-schedule
value: each schedule records which session created it and the UI view shows it
files: [src/agents_schedule/migrations/0002_schedule_owner.sql, src/agents_schedule/db/schedules.py, src/agents_schedule/api/schemas.py, src/agents_schedule/api/schedules.py, openapi.json, tests/test_migrations.py, tests/test_schedules_repo.py, tests/test_api_schedules.py]
verify: "uv run pytest tests/test_migrations.py tests/test_schedules_repo.py tests/test_api_schedules.py tests/test_readme_api.py && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# sched schedule owner

## Requirement

README Goal G3, verbatim: "A flagged session changes only the sessions, presets and schedules it created; it reads all of them, with preset secrets masked except on its own; it cannot grant more privilege than it holds (`session_orchestration` is never grantable), cannot delete itself, and cannot delete a superleader or orchestrating session."

README Goal G5, verbatim: "Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator."

Design D7, verbatim: "Migration (next free number, 0002 today) adds `owner_session_id uuid NULL` and `owner_slug text NULL`. [...] The UI API is unchanged except the schedule view gains `owner_slug` (additive); UI writes never change the owner (my call)."

Scope (agents-schedule): `src/agents_schedule/migrations/0002_schedule_owner.sql` (the next free number at build time; 0002 today), `db/schedules.py` (owner fields on create and read, owned count, owned lookup), `api/schemas.py` (`ScheduleView.owner_slug`), `api/schedules.py` (the view carries it; UI create and replace never set or clear it), `openapi.json`, `tests/test_migrations.py`, `tests/test_schedules_repo.py`, `tests/test_api_schedules.py`. The relay listener and routes are later tasks.

## Acceptance conditions

- ac1: the migration adds owner_session_id uuid NULL and owner_slug text NULL to schedules and a rerun is a no-op [evidence: test:tests/test_migrations.py::test_schedule_owner_columns]
- ac2: the repository stores and reads the owner, lists schedules owned by a session and counts them [evidence: test:tests/test_schedules_repo.py::test_owner_round_trip]
- ac3: the UI schedule view carries owner_slug, null for schedules made in the UI, and a UI replace of an owned schedule keeps its owner [evidence: test:tests/test_api_schedules.py::test_owner_slug_in_view]
- ac4: the existing UI routes are otherwise unchanged [evidence: command:uv run pytest tests/test_api_schedules.py]
- ac5: openapi.json matches the app [evidence: command:uv run pytest tests/test_readme_api.py::test_openapi_matches_app]
- ac6: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_migrations.py tests/test_schedules_repo.py tests/test_api_schedules.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agents_schedule/migrations/0002_schedule_owner.sql`
- `src/agents_schedule/db/schedules.py`
- `src/agents_schedule/api/schemas.py`
- `src/agents_schedule/api/schedules.py`
- `openapi.json`
- `tests/test_migrations.py`
- `tests/test_schedules_repo.py`
- `tests/test_api_schedules.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
