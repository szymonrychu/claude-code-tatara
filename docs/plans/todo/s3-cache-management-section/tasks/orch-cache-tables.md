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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
