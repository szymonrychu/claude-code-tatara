---
title: webhook schema settings
status: todo
repo: agents-webhook
value: the service has its own database schema for the event queue and mappings and validated settings
files: [src/agents_webhook/migrations/__init__.py, src/agents_webhook/migrations/0001_init.sql, src/agents_webhook/settings.py, tests/conftest.py, tests/test_schema_settings.py]
verify: "uv run pytest tests/test_schema_settings.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-scaffold]
owns: [webhook-events-schema, webhook-settings-env]
uses: [agents-common-db, agents-common-settings-runtime]
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

# webhook schema settings

## Requirement

Schema and settings of agents-webhook (design D3, D5, D6, D7). Paths are in code/agents-webhook.

- `migrations/0001_init.sql`:
  - `mappings(id bigserial pk, source text check in (github,gitlab,grafana), kind text check in (mr,issue,comment,alert), repo text null, labels jsonb not null default '{}', preset_id text not null, prompt_template text null, created_at timestamptz default now())`. Writer: the api only.
  - `events(id bigserial pk, seq bigserial, priority smallint not null, received_at, updated_at, source, kind, action, repo, number int null, title, url, author, actor, labels jsonb, payload jsonb not null, dedup_key text not null, status text not null check in (new,in-progress,handled,ignored,failed), reason text null, mapping_id bigint null references mappings on delete set null, preset_id text null, prompt_template text null, update_of bigint null references events, duplicate_of bigint null references events, deliveries int not null default 1, cluster_id text null, cluster_slug text null, message_id text null, started_at timestamptz null, finished_at timestamptz null)`. A queue table: ingest inserts and replaces payloads of `new` rows, the worker moves status; every status change is a status-guarded UPDATE.
  - Partial unique index `events_live_key ON events(dedup_key) WHERE status IN ('new','in-progress') AND update_of IS NULL`; index `(status, priority, seq)`; index `(received_at desc)`.
  - A header comment names each table's writers.
- `settings.py`: `WebhookSettings(BaseServiceSettings)` with prefix `WEBHOOK_`: `github_secret`, `gitlab_token`, `grafana_token` (SecretStr, each with `_FILE`), `bot_logins: CsvList`, `allowed_authors: CsvList`, `max_in_progress=3`, `max_queue=500`, `max_body_bytes=5242880`, `run_timeout_seconds=3600`, `poll_seconds=5`, `events_retention_days=30` (only for the list default window), plus the inherited database and orchestrator fields.
- `tests/conftest.py`: `db` fixture from `agents_common.testing.migrated_db("agents_webhook.migrations")`.
- `tests/test_schema_settings.py`: migration applies; the live-key index rejects a second `new` row with the same key but allows an update message and a handled row; status check rejects unknown statuses; settings defaults, `_FILE` secrets, every bad variable named.

## Acceptance conditions

- AC1: only one live (new or in-progress) non-update message row per dedup key can exist [evidence: command:uv run pytest tests/test_schema_settings.py -q -k live_key]
- AC2: status and source values are constrained [evidence: command:uv run pytest tests/test_schema_settings.py -q -k check]
- AC3: settings defaults are 3 in progress, 500 queued, 5 MiB, 3600 s timeout, and secrets load from _FILE [evidence: command:uv run pytest tests/test_schema_settings.py -q -k settings]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/migrations/__init__.py`
- `src/agents_webhook/migrations/0001_init.sql`
- `src/agents_webhook/settings.py`
- `tests/conftest.py`
- `tests/test_schema_settings.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
