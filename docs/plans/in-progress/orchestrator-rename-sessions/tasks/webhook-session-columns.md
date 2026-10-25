---
title: webhook session columns
status: done
repo: agents-webhook
value: webhook runs record and show the session they started
files: [src/agents_webhook/migrations/0005_sessions.sql, src/agents_webhook/db/events.py, src/agents_webhook/api/schemas.py, src/agents_webhook/worker.py, openapi.json, README.md, tests/]
verify: "uv run pytest -q tests/test_event_store.py tests/test_api.py tests/test_worker.py tests/test_worker_reuse.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: opus
review: ""
verified_head: 7c630a9
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: 3
actual_minutes: 8
actual_tokens: 2973199
actual_roles: impl 8
actual_role_tokens: impl 2973199
---

# webhook session columns

## Requirement

Rename the webhook run's cluster columns and API fields to session (design D2, D4, D14; user decision: cluster is renamed session throughout; contract `webhook-events-session-fields`). Paths are in code/agents-webhook. Starts from main after webhook-event-filters merged (gate Q6), whose migration is 0004.

- New `src/agents_webhook/migrations/0005_sessions.sql`: `events.cluster_id` to `session_id`, `events.cluster_slug` to `session_slug`, every index or constraint naming them renamed to match; `ALTER ... RENAME` only, no row changed.
- `src/agents_webhook/db/events.py`: every SQL string, the row model fields `session_id`/`session_slug`, `set_session(run_id, session_id, *, slug=None)` (was `set_cluster`), docstrings and comments.
- `src/agents_webhook/api/schemas.py`: `EventView` and `EventDetail` fields `session_id`, `session_slug`; `openapi.json` regenerated with the repo's export (the README/openapi test names the command).
- `src/agents_webhook/worker.py`: reads the renamed row fields; it still hands them to agents-common v0.2.0 (`RunRef(cluster_id=event.session_id)`) until webhook-worker-sessions pins v0.3.0.
- `README.md`: the event fields in the API reference.
- tests/: `test_event_store.py`, `test_api.py`, `test_worker.py`, `test_worker_reuse.py` and `tests/e2e/` follow the renamed fields; tests first: `tests/test_event_store.py::test_0005_renames_cluster_columns` (seed a row with cluster_id and cluster_slug at 0004, migrate, read them back as session_id and session_slug; no column named cluster remains) and `tests/test_api.py::test_event_view_session_fields`.

## Acceptance conditions

- AC1: migration 0005 keeps every row and leaves no events column named cluster [evidence: test:tests/test_event_store.py::test_0005_renames_cluster_columns]
- AC2: the events API serves session_id and session_slug [evidence: test:tests/test_api.py::test_event_view_session_fields]
- AC3: openapi.json and the README match the app [evidence: command:uv run pytest -q tests/test_readme_api.py]
- AC4: the touched suites and lint pass [evidence: command:uv run pytest -q tests/test_event_store.py tests/test_api.py tests/test_worker.py tests/test_worker_reuse.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/migrations/0005_sessions.sql`
- `src/agents_webhook/db/events.py`
- `src/agents_webhook/api/schemas.py`
- `src/agents_webhook/worker.py`
- `openapi.json`
- `README.md`
- `tests/`

## Interfaces

- `events.session_id`, `events.session_slug`; `EventView`/`EventDetail` fields `session_id`, `session_slug` (contract `webhook-events-session-fields`, consumed by web-webhooks-session-fields).

## Expected outcome

Webhook runs store and serve their session; migration 0005 keeps every row.

## Steps

- Red: write `test_0005_renames_cluster_columns` and `test_event_view_session_fields`; run them: they fail.
- Green: 0005, events store, schemas, worker field reads, openapi.json, README fields; the verify passes.

## Notes

- 0004 belongs to webhook-event-filters (merged first, the epic's blocker); never renumber it.
- The worker still calls agents-common v0.2.0 here; keep its call shapes.

- 2026-10-25 done
