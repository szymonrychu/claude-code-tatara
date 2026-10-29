---
title: sched schedule owner
status: todo
repo: agents-schedule
value: each schedule records which session created it and the UI view shows it
files: [src/agents_schedule/migrations/0002_schedule_owner.sql, src/agents_schedule/db/schedules.py, src/agents_schedule/api/schemas.py, src/agents_schedule/api/schedules.py, openapi.json, tests/test_migrations.py, tests/test_schedules_repo.py, tests/test_api_schedules.py]
verify: "uv run pytest tests/test_migrations.py tests/test_schedules_repo.py tests/test_api_schedules.py tests/test_readme_api.py && mise run lint"
depends_on: [baseline-facts]
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

Design D7, verbatim: "Migration 0002 (the next free agents-schedule number; only `0001_schedules.sql` exists and no other epic claims one) adds `owner_session_id uuid NULL` and `owner_slug text NULL`. [...] The UI API is unchanged except the schedule view gains `owner_slug` (additive); UI writes never change the owner (my call)."

Scope (agents-schedule): `src/agents_schedule/migrations/0002_schedule_owner.sql` (the number baseline-facts confirmed), `db/schedules.py` (owner fields on create and read, owned count, owned lookup), `api/schemas.py` (`ScheduleView.owner_slug`), `api/schedules.py` (the view carries it; UI create and replace never set or clear it), `openapi.json`, `tests/test_migrations.py`, `tests/test_schedules_repo.py`, `tests/test_api_schedules.py`. The relay listener and routes are later tasks.

User settlement B6 (2026-10-27), verbatim: "the build starts only after all three blockers have merged. The first task reads the real migration number, plugins version and tool counts from main and amends the dependent tasks. No assumed numbers in ACs." The migration number is 0002, as baseline-facts confirmed; on a mismatch the orchestrator session amends it.

User settlement B3 (2026-10-27), verbatim: "agent-created schedules may be created enabled. Orphans after the owner's deletion are managed from the UI." The UI routes therefore treat a schedule whose owner session no longer exists like any other: the owner columns are never validated against a live session.


Tests no longer accurate (named): `tests/test_migrations.py::test_migrate_idempotent` and `::test_concurrent_migrate_applies_once` assert the applied list `== ["0001_schedules.sql"]`; with the new migration each asserts `["0001_schedules.sql", "0002_schedule_owner.sql"]`, nothing else changes.

## Acceptance conditions

- ac1: the migration 0002_schedule_owner.sql adds owner_session_id uuid NULL and owner_slug text NULL to schedules and a rerun is a no-op [evidence: test:tests/test_migrations.py::test_schedule_owner_columns]
- ac2: the repository stores and reads the owner, lists schedules owned by a session and counts them [evidence: test:tests/test_schedules_repo.py::test_owner_round_trip]
- ac3: the UI schedule view carries owner_slug, null for schedules made in the UI, and a UI replace of an owned schedule keeps its owner, and a UI replace and a UI delete of an owned schedule succeed when its owner session no longer exists [evidence: test:tests/test_api_schedules.py::test_owner_slug_in_view]
- ac4: the existing UI routes are otherwise unchanged [evidence: command:uv run pytest tests/test_api_schedules.py]
- ac5: openapi.json matches the app [evidence: command:uv run pytest tests/test_readme_api.py::test_openapi_matches_app]
- ac6: a fresh migrate and a concurrent migrate apply exactly 0001_schedules.sql and 0002_schedule_owner.sql (updated) [evidence: test:tests/test_migrations.py::test_migrate_idempotent]
- ac7: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_migrations.py tests/test_schedules_repo.py tests/test_api_schedules.py tests/test_readme_api.py && mise run lint]

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

- `db/schedules.py:Schedule.owner_session_id: uuid.UUID | None`, `owner_slug: str | None`; `create(conn, data, *, owner_session_id=None, owner_slug=None)`; `count_owned(conn, owner_session_id) -> int`; `get_owned(conn, schedule_id, owner_session_id) -> Schedule | None`.
- `api/schemas.py:ScheduleView.owner_slug: str | None`.

## Expected outcome

Each schedule records which session created it, and the UI can show it.

## Steps

- Read `ls src/agents_schedule/migrations/` and take the next free number.
- Red: add the three tests; run `uv run pytest tests/test_migrations.py tests/test_schedules_repo.py tests/test_api_schedules.py`: fail.
- Green: migration, repo, view, `openapi.json` (the repo's generator, as in README); run the task's verify. Quote the summary line.

## Notes

- No Docker in agent pods: the DB tests run in CI.
- `tests/test_api_schedules.py::test_crud` may compare whole views; if `owner_slug` makes such an assertion no longer accurate, name it and why.

- 2026-10-27 amended: builder check B6 and B3: migration number from baseline-facts, orphaned owned schedules stay manageable from the UI

- 2026-10-29 amended: staleness refresh: migration 0002 confirmed; named test_migrate_idempotent and test_concurrent_migrate_applies_once
