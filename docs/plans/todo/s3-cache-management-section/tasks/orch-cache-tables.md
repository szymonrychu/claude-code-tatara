---
title: orch cache tables
status: todo
repo: agents-orchestrator
value: The orchestrator database can hold the bucket inventory and the queued delete and refresh requests
files: [src/agents_orchestrator/db/migrations, tests/test_migrations.py, README.md]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_migrations.py && mise run lint  # DB-backed tests need Docker: CI only here"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch cache tables

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

Design D1 (Reconciler-owned inventory table), verbatim: "`cache_objects` (key, kind, size, etag, last_modified, generation), written only by the reconciler: a full `list_objects_v2` pass every `ORCH_CACHE_INVENTORY_INTERVAL_SECONDS` (default 900) or at once on a refresh request, in its own asyncio task off the session pass (`asyncio.to_thread`, botocore paginator); a pass writes a new generation and drops the old one in one transaction. Alternatives: on-demand listing per view (up to 100 S3 calls per page view, no history); a credentialed component (forbidden). User Q3."

Design D2 (Delete and refresh requests through a guarded queue), the table part, verbatim: "`cache_requests` (id, kind `delete|refresh`, object, etag, size, status `queued|running|done|refused|failed`, reason, timestamps): the api inserts `queued` rows and notifies a new channel `cache_requested` [...]"

Design constraint, verbatim: "One SQL migration, numbered `<MIGRATION>` = next free at build time (0010, 0012 and decouple's are claimed)."

User decision, verbatim: "Builds after both blockers land on main; the SQL migration number is the placeholder <MIGRATION>, resolved at build time exactly as /workdir/workdir/docs/plans/in-progress/hive-decoupling does".

This task delivers the schema of D1 and D2 in agents-orchestrator: one new SQL migration `src/agents_orchestrator/db/migrations/<MIGRATION>_cache_section.sql`, additive and idempotent like the earlier migrations, creating:

- `cache_listings` (my call: the listing state `GET /api/v1/cache` reports): `generation` bigserial primary key, `state` text NOT NULL CHECK in (`running`, `done`, `failed`), `reason` text, `objects` bigint, `bytes` bigint, `started_at` timestamptz NOT NULL DEFAULT now(), `finished_at` timestamptz. Written only by the reconciler.
- `cache_objects`: `generation` bigint NOT NULL REFERENCES `cache_listings` ON DELETE CASCADE, `key` text NOT NULL (the object name without `cache_s3_prefix`), `kind` text NOT NULL CHECK in (`workspace`, `transcripts`), `size` bigint NOT NULL CHECK >= 0, `etag` text NOT NULL, `last_modified` timestamptz NOT NULL, primary key (`generation`, `key`). Written only by the reconciler.
- `cache_requests`: `id` bigserial primary key, `kind` text NOT NULL CHECK in (`delete`, `refresh`), `object` text, `etag` text, `size` bigint, `status` text NOT NULL DEFAULT `queued` CHECK in (`queued`, `running`, `done`, `refused`, `failed`), `reason` text, `created_at` timestamptz NOT NULL DEFAULT now(), `started_at` timestamptz, `finished_at` timestamptz, and a CHECK that a `delete` row has `object` and `etag` and a `refresh` row has neither. The api inserts; the reconciler changes rows only through status-guarded updates.

README `## Data model` lists the three tables with their writers.

`<MIGRATION>` is a placeholder: before this task starts, the orchestrator session reads the highest migration number on agents-orchestrator main (after both blockers landed) and amends this task with the next free number through `ticket.py amend`, as hive-decoupling did. The migration test is named without the number.

Tests no longer accurate because they pin the applied migration list and a new migration exists; each gains the new version: tests/test_migrations.py::test_fresh_database_gets_all_tables (also gains the three tables), ::test_presets_migration_on_existing_sessions, ::test_concurrent_migrate_serialises and ::test_0005_renames_clusters_to_sessions.

## Acceptance conditions

- AC1: the migration `<MIGRATION>_cache_section.sql` creates cache_listings, cache_objects and cache_requests with the columns, defaults and keys of the Requirement [evidence: test:tests/test_migrations.py::test_cache_section_migration]
- AC2: the constraints refuse a delete request without object or etag, a refresh request with an object, an unknown status or kind, an unknown object kind and a negative size, and deleting a listing cascades to its objects [evidence: test:tests/test_migrations.py::test_cache_section_constraints]
- AC3: running the migration SQL again changes nothing [evidence: test:tests/test_migrations.py::test_cache_section_migration_idempotent]
- AC4: a fresh database gets every migration including the new one and the three tables [evidence: test:tests/test_migrations.py::test_fresh_database_gets_all_tables]
- AC5: README Data model lists the three tables [evidence: command:grep -q '`cache_listings`' README.md && grep -q '`cache_objects`' README.md && grep -q '`cache_requests`' README.md]
- AC6: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/db/migrations`
- `tests/test_migrations.py`
- `README.md`

## Interfaces

- `src/agents_orchestrator/db/migrations/<MIGRATION>_cache_section.sql` (new; `<MIGRATION>` amended to the next free number on main before the task starts).
- Tables and columns exactly as the Requirement; index choices are the builder's (a partial index on `cache_requests (kind, id) WHERE status IN ('queued', 'running')` suits the claims).
- Writers (README Data model): `cache_listings` and `cache_objects` the reconciler only; `cache_requests` inserted by the api, status changed only by the reconciler through `WHERE status = ...` updates.

## Expected outcome

`orch migrate` on a database at the blockers' schema adds the three tables; a second run changes nothing; the following tasks have their schema.

## Steps

- Read `db/migrate.py`, the newest migrations on main (including the blockers'), `db/migrations/0001_init.sql` (the `checks` table, the queue pattern) and `tests/test_migrations.py` (`run_migrations`, `empty_dsn`, the tmp_path copy pattern of `test_drop_feed_cursor_migration`) in one pass; confirm `<MIGRATION>` was amended to a number and is still the next free one.
- Red: add the three new tests named in the acceptance conditions and the new version (and tables) to the four list-pinning tests named in the Requirement; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_migrations.py`; expect failures on the missing migration (DB tests: on CI or a local Postgres).
- Green: write the SQL file and the README Data model rows; rerun; expect passed.
- `mise run lint`; expect exit 0.

## Notes

- If `<MIGRATION>` still reads as a placeholder when the task starts, stop and return it as a question; never pick a number yourself.
- The migration only creates tables: no data, no S3, nothing irreversible.
- Builds after decouple-s3-session-cache-fr and live-session-transcript-back landed on main (README blockers). Use their names as landed: `cache/naming.py` (`render_cache_name`, `DEFAULT_CACHE_NAME_TEMPLATE`), `cache/copy.py`, `reconciler/cache_migration.py`, and `status.cache` `key`, `object`, `sessions_object`, `restore`, `save`, `sessions_restore`, `sessions_save`, `sessions_backup`, `migration`. Read the landed code first; where a landed name differs from this task's text, use the landed name and say so in the task Notes, never guess.
- Tree state: `mise run lint` green. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers; agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. Pure and moto-only tests run locally. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
