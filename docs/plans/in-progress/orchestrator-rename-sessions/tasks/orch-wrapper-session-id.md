---
title: orch wrapper session id
status: done
repo: agents-orchestrator
value: "the wrapper's session id no longer takes the word session from the orchestrator's unit"
files: [src/agents_orchestrator/db/migrations/0004_wrapper_session_id.sql, src/agents_orchestrator/, tests/, openapi.json, README.md]
verify: "uv run pytest -q tests/test_migrations.py tests/test_events_store.py tests/test_api_streams.py tests/test_ingester.py tests/test_wrapper_session_bootstrap.py tests/test_workspace_proxy.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-chart-ci-rename]
model: opus
review: ""
verified_head: 59d20d6
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: 3
actual_minutes: 12
actual_tokens: 3761986
actual_roles: impl 12
actual_role_tokens: impl 3761986
---

# orch wrapper session id

## Requirement

The claude-code-wrapper's session id becomes `wrapper_session_id` in the orchestrator (design D3, D4; gate Q7), so "session" is free for the orchestrator's unit. Paths are in code/agents-orchestrator.

- New `src/agents_orchestrator/db/migrations/0004_wrapper_session_id.sql`: `agents.session_id` to `wrapper_session_id`, `agents.session_created_at` to `wrapper_session_created_at`, `events.session_id` to `wrapper_session_id`; the events unique constraint over `(agent_id, session_id, seq)` and any other index or constraint naming the wrapper session renamed to match. `ALTER ... RENAME` only: no row is dropped or rewritten. 0001-0003 stay byte-identical (the runner tracks versions).
- Every SQL string, row key and attribute for these columns in src/ (db/agents.py, db/events.py, ingester/loop.py, reconciler/, dispatcher/verify.py, api/workspace.py, api/streams.py and any other the builder finds with `git grep -n session_id`) uses the new names; `reconciler/sessions.py` becomes `reconciler/wrapper_sessions.py` (`git mv`) with its importers, and `tests/test_session_bootstrap.py` becomes `tests/test_wrapper_session_bootstrap.py`.
- API: `EventView.session_id` becomes `wrapper_session_id`; `openapi.json` regenerated with `uv run python -m agents_orchestrator.api.openapi > openapi.json`; README's event fields and SSE payload docs updated.
- The `wrapper/` client keeps the wrapper's own `/v1/sessions` vocabulary (its URL paths and method names mirror the wrapper API).
- Tests first: `tests/test_migrations.py::test_0004_renames_wrapper_session_columns` (apply 0001-0003 to an empty DB from a tmp migrations dir, insert a cluster, an agent with a session id and an event, run the full migrations, read the same values from the `wrapper_session_*` columns; `information_schema.columns` lists no `session_id` or `session_created_at` on agents or events); `tests/test_api_streams.py::test_event_view_wrapper_session_id` (an event row is served with `wrapper_session_id` and without `session_id`).

## Acceptance conditions

- AC1: migration 0004 keeps every row and renames the wrapper session columns, indexes and constraints [evidence: test:tests/test_migrations.py::test_0004_renames_wrapper_session_columns]
- AC2: the events API serves wrapper_session_id and no session_id [evidence: test:tests/test_api_streams.py::test_event_view_wrapper_session_id]
- AC3: no src file outside the wrapper client and migrations 0001-0003 uses a bare session_id or session_created_at [evidence: command:! git grep -n -E '\bsession_(id|created_at)\b' -- src/agents_orchestrator ':!src/agents_orchestrator/wrapper' ':!src/agents_orchestrator/db/migrations/0001_init.sql' ':!src/agents_orchestrator/db/migrations/0002_presets.sql' ':!src/agents_orchestrator/db/migrations/0003_hive.sql']
- AC4: openapi.json and README match the app [evidence: command:uv run pytest -q tests/test_readme_api.py]
- AC5: the touched suites and lint pass [evidence: command:uv run pytest -q tests/test_migrations.py tests/test_events_store.py tests/test_api_streams.py tests/test_ingester.py tests/test_wrapper_session_bootstrap.py tests/test_workspace_proxy.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/db/migrations/0004_wrapper_session_id.sql`
- `src/agents_orchestrator/`
- `tests/`
- `openapi.json`
- `README.md`

## Interfaces

- Columns `agents.wrapper_session_id`, `agents.wrapper_session_created_at`, `events.wrapper_session_id`; `EventView.wrapper_session_id`; module `reconciler/wrapper_sessions.py`.

## Expected outcome

The orchestrator never uses a bare `session_id` for the wrapper's session; migration 0004 keeps every row.

## Steps

- Red: write `test_0004_renames_wrapper_session_columns` and `test_event_view_wrapper_session_id`; run them: they fail (no 0004, field missing).
- Green: write 0004, rename SQL, row keys, attributes, the module and EventView, regenerate openapi.json, update README; the verify passes.

## Notes

- Reuse the tmp-migrations-dir pattern of `test_presets_migration_on_existing_clusters` in tests/test_migrations.py.
- The live database gets 0004 only on the imported copy (design D5); the old database is never migrated.

- 2026-10-25 done
