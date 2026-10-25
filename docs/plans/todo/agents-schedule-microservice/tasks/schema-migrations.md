---
title: schema migrations
status: todo
repo: agents-schedule
value: "the service owns its database schema, migrated forward-only before any process starts"
files: [src/agents_schedule/db/__init__.py, src/agents_schedule/db/migrations/0001_schedules.sql, src/agents_schedule/db/migrate.py, tests/conftest.py, tests/test_migrations.py]
verify: "uv run --frozen pytest tests/test_migrations.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [schedule-settings-model]
owns: [sched-schema, sched-db-fixture]
uses: [agents-common-lib, agents-schedule-settings-env]
model: ""
estimate: 6
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

# schema migrations

## Requirement

Create the schema (design D3, D9; approvals A1, A3) as forward-only SQL run by the agents-common migrator under its advisory lock (contract `agents-common-lib`, the pattern of `code/agent-orchestrator/src/agent_orchestrator/db/migrate.py:run_migrations`).

`0001_schedules.sql`, idempotent statements:
- `schedules` (writer: the api only): `id uuid pk`, `name text unique not null` (1..100 chars), `cron text not null`, `timezone text not null`, `preset_id uuid not null`, `prompt text not null` (1..16384 chars), `enabled boolean not null default true`, `armed_at timestamptz not null` (the instant from which firings count: create, enable, cron or timezone change), `created_at`, `updated_at`.
- `runs` (a queue table: the api inserts manual runs, the worker inserts scheduled runs; every status change is a status-guarded UPDATE): `id uuid pk`, `schedule_id uuid not null references schedules on delete cascade`, `trigger text check in ('scheduled','manual')`, `fire_time timestamptz not null`, `status text check in ('new','in-progress','handled','failed','ignored')`, `reason text`, `attempts int not null default 0`, `cluster_slug text`, `cluster_id uuid`, `message_id uuid`, `created_at`, `updated_at`, `started_at`, `finished_at`; `unique (schedule_id, fire_time)`; index `(status, fire_time)`.
- `agents_schedule.db.migrate:migrate(settings) -> list[str]` applies pending files and returns their names.
- `tests/conftest.py`: testcontainers Postgres with a migrated template database and a per-test database cloned from it (the agents-common fixture if it ships one, else the pattern of `code/agent-orchestrator/tests/conftest.py`).

## Acceptance conditions

- AC1: migrate applies 0001 on an empty database and is a no-op the second time [evidence: test:tests/test_migrations.py::test_migrate_idempotent]
- AC2: two concurrent migrate calls apply each file once [evidence: test:tests/test_migrations.py::test_concurrent_migrate_applies_once]
- AC3: a second run row for the same schedule and fire time is refused by the unique key [evidence: test:tests/test_migrations.py::test_runs_unique_schedule_fire_time]
- AC4: status and trigger outside their sets are refused [evidence: test:tests/test_migrations.py::test_runs_checks]
- AC5: deleting a schedule deletes its runs [evidence: test:tests/test_migrations.py::test_schedule_delete_cascades]

## Files

- `src/agents_schedule/db/__init__.py`
- `src/agents_schedule/db/migrations/0001_schedules.sql`
- `src/agents_schedule/db/migrate.py`
- `tests/conftest.py`
- `tests/test_migrations.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
