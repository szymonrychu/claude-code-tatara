---
title: webhook schema settings
status: done
repo: agents-webhook
value: "the service has its own database schema for webhook endpoints and the event queue, and validated settings"
files: [src/agents_webhook/migrations/__init__.py, src/agents_webhook/migrations/0001_init.sql, src/agents_webhook/settings.py, tests/conftest.py, tests/test_schema_settings.py]
verify: "uv run pytest tests/test_schema_settings.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-scaffold]
model: ""
review: ""
verified_head: e1fd2c4
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: 1
actual_minutes: 11
actual_tokens: 629191
actual_roles: impl 11
actual_role_tokens: impl 629191
---

# webhook schema settings

## Requirement

Schema and settings of agents-webhook (design D3, D5, D6, D7, D16, D18; re-plan 2026-10-25: per-webhook endpoints replace sources and mappings). Paths are in code/agents-webhook.

- `migrations/0001_init.sql`:
  - `endpoints(id bigserial pk, suffix text not null unique check (suffix ~ '^[A-Za-z0-9._~-]{1,128}$'), type text not null check in ('grafana-alert','gitlab-issue','gitlab-mr','github-issue','github-pr'), preset_id text not null, prompt_template text null, username text not null, password_hash text not null, created_at timestamptz not null default now(), credentials_rotated_at timestamptz null)`. Writer: the api only. No plaintext password column.
  - `events(id bigserial pk, seq bigserial, priority smallint not null, received_at, updated_at, endpoint_id bigint null references endpoints on delete set null, endpoint_suffix text not null, type text not null, source text not null check in (github,gitlab,grafana), kind text not null check in (mr,issue,comment,alert), action, repo, number int null, title, url, author, actor, labels jsonb, payload jsonb not null, delivery_id text null, dedup_key text not null, status text not null check in (new,in-progress,handled,ignored,failed), reason text null, preset_id text null, prompt_template text null, update_of bigint null references events, duplicate_of bigint null references events, deliveries int not null default 1, cluster_id text null, cluster_slug text null, message_id text null, started_at timestamptz null, finished_at timestamptz null)`. A queue table: ingest inserts and replaces payloads of `new` rows, the worker moves status; every status change is a status-guarded UPDATE.
  - Partial unique index `events_new_key ON events(endpoint_id, dedup_key) WHERE status = 'new'`; index `(endpoint_id, delivery_id)`; index `(endpoint_id, dedup_key, id desc)` (latest run per key); index `(status, priority, seq)`; index `(received_at desc)`.
  - A header comment names each table's writers.
- `settings.py`: `WebhookSettings(BaseServiceSettings)` with prefix `WEBHOOK_`: `public_base_url` (default `https://lab.szymonrichert.pl`, no trailing slash), `bot_logins: CsvList`, `allowed_authors: CsvList`, `max_in_progress=3`, `max_in_progress_per_endpoint=1`, `max_queue=500`, `max_body_bytes=5242880`, `run_timeout_seconds=3600`, `poll_seconds=5`, `events_retention_days=30` (only for the list default window), `auth_failures_per_minute=10`, `trusted_proxies: CsvList` of CIDRs (default empty; each validated), `min_password_length=16`, plus the inherited database and orchestrator fields. No per-source secret settings.
- `tests/conftest.py`: `db` fixture from `agents_common.testing.migrated_db("agents_webhook.migrations")`.
- `tests/test_schema_settings.py`: migration applies; the new-key index rejects a second `new` row with the same endpoint and key but allows it for another endpoint and alongside an `in-progress` or `handled` row; status, type and suffix checks reject bad values; settings defaults, a bad CIDR in `WEBHOOK_TRUSTED_PROXIES` named, every bad variable named.

## Acceptance conditions

- AC1: only one new row per endpoint and dedup key can exist, and other endpoints or in-progress rows do not collide [evidence: command:uv run pytest tests/test_schema_settings.py -q -k new_key]
- AC2: status, type, source and suffix values are constrained and no plaintext password column exists [evidence: command:uv run pytest tests/test_schema_settings.py -q -k check]
- AC3: settings defaults are 3 in progress, 1 per endpoint, 500 queued, 5 MiB, 3600 s timeout, 10 auth failures per minute, 16-char minimum password, and bad CIDRs are named [evidence: command:uv run pytest tests/test_schema_settings.py -q -k settings]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/migrations/__init__.py`
- `src/agents_webhook/migrations/0001_init.sql`
- `src/agents_webhook/settings.py`
- `tests/conftest.py`
- `tests/test_schema_settings.py`

## Interfaces

- Owns `webhook-events-schema` (`migrations/0001_init.sql`: `endpoints`, `events`) and `webhook-settings-env` (`WEBHOOK_*` names, documented in README by webhook-docs-memory).

## Expected outcome

`agents-webhook migrate` (wired later) creates the endpoints and events tables; settings validate.

## Steps

- Red: tests; run: fail. Green: SQL and settings; run the verify command.

## Notes

- Later schema changes are new files `0002_*.sql`; never edit 0001 after it ships.

- 2026-10-25 amended: re-plan 2026-10-25: per-webhook endpoints (/webhook/<suffix>, one type, one preset, basic auth) replace per-source secrets and mappings; agent reuse is opt-in per preset (design D3, D7, D16-D19)

Gate Q23 answer (user, 2026-10-25): the limits (max in progress overall, max in progress per endpoint, queue cap, body cap) are settings with defaults 3, 1, 500 and 5 MiB, each set from an agents-webhook Helm chart value (for example `limits.maxInProgress`, `limits.maxInProgressPerEndpoint`, `limits.queueCap`, `limits.maxBodyBytes`) rendered into the ingest and worker env, and documented. This task delivers its part of that.

- 2026-10-25 done
