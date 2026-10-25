---
title: schema migrations
status: in-progress
repo: agents-schedule
value: "the service owns its database schema, migrated forward-only before any process starts"
files: [src/agents_schedule/db/__init__.py, src/agents_schedule/migrations/__init__.py, src/agents_schedule/migrations/0001_schedules.sql, src/agents_schedule/db/migrate.py, tests/conftest.py, tests/test_migrations.py]
verify: "uv run --frozen pytest tests/test_migrations.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [schedule-settings-model]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# schema migrations

## Requirement

Create the schema (design D3, D9; approvals A1, A3) as forward-only SQL in the package `agents_schedule.migrations`, run by agents-common `run_migrations(url, "agents_schedule.migrations")` under its advisory lock (contract `agents-common-lib`).

`0001_schedules.sql`, idempotent statements:
- `schedules` (writer: the api only): `id uuid pk`, `name text unique not null` (1..100 chars), `cron text not null`, `timezone text not null`, `preset_id uuid not null`, `prompt text not null` (1..16384 chars), `enabled boolean not null default true`, `armed_at timestamptz not null` (the instant from which firings count: create, enable, cron or timezone change), `created_at`, `updated_at`.
- `runs` (a queue table: the api inserts manual runs, the worker inserts scheduled runs; every status change is a status-guarded UPDATE): `id uuid pk`, `schedule_id uuid not null references schedules on delete cascade`, `trigger text check in ('scheduled','manual')`, `fire_time timestamptz not null`, `status text check in ('new','in-progress','handled','failed','ignored')`, `reason text`, `attempts int not null default 0`, `session_slug text` (the run's deterministic slug, set at claim), `session_id uuid`, `message_id text` (the RunRef carries it as a string), `reuse text check in ('delivered','fallback')` (null until the reuse decision of design D15: `delivered` = the prompt goes to the schedule's earlier running session, `fallback` = reuse did not work out and a new session is created), `created_at`, `updated_at`, `started_at`, `finished_at`; `unique (schedule_id, fire_time)`; index `(status, fire_time)`. Add any column the agents-common `RunStore` protocol requires (contract `preset-mapping-model`).
- `agents_schedule.db.migrate:migrate(settings) -> list[str]` applies pending files and returns their names.
- `tests/conftest.py`: the migrated template database and per-test clone from the `agents_common.testing` pytest plugin (`pg_url`, `migrated_db`), pointed at `agents_schedule.migrations`.

## Acceptance conditions

- AC1: migrate applies 0001 on an empty database and is a no-op the second time [evidence: test:tests/test_migrations.py::test_migrate_idempotent]
- AC2: two concurrent migrate calls apply each file once [evidence: test:tests/test_migrations.py::test_concurrent_migrate_applies_once]
- AC3: a second run row for the same schedule and fire time is refused by the unique key [evidence: test:tests/test_migrations.py::test_runs_unique_schedule_fire_time]
- AC4: status and trigger outside their sets are refused [evidence: test:tests/test_migrations.py::test_runs_checks]
- AC5: deleting a schedule deletes its runs [evidence: test:tests/test_migrations.py::test_schedule_delete_cascades]
- AC6: reuse outside null, delivered and fallback is refused [evidence: test:tests/test_migrations.py::test_runs_reuse_check]

## Files

- `src/agents_schedule/db/__init__.py`
- `src/agents_schedule/migrations/__init__.py`
- `src/agents_schedule/migrations/0001_schedules.sql`
- `src/agents_schedule/db/migrate.py`
- `tests/conftest.py`
- `tests/test_migrations.py`

## Interfaces

- Tables `schedules`, `runs` (part `sched-schema`, file `src/agents_schedule/migrations/0001_schedules.sql`); later schema changes are 0002+.
- `agents_schedule.db.migrate:migrate(settings: Settings) -> list[str]`.
- Fixtures `db_url`, `conn` in tests/conftest.py (part `sched-db-fixture`).

## Expected outcome

`migrate` creates both tables once, concurrently safe, and every DB test gets a fresh migrated database.

## Steps

- Write tests/test_migrations.py and conftest.py; run: fails (no migration).
- Write 0001_schedules.sql and migrate.py; `uv run --frozen pytest tests/test_migrations.py -q`: `6 passed`.
- Lint clean.

## Notes

- The last-fired stamp is not a column on `schedules`: it is the latest `runs.fire_time` with `trigger = 'scheduled'`, else `schedules.armed_at`, so `schedules` keeps one writer (the api) (design D3).
- Tests need Docker for testcontainers; in a cloud session start dockerd first (superrepo MEMORY 2026-10-23).
- do-not-build: a DB layer; agents-common provides pool, migrate, transition and claim.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule
