---
title: mxc schema migrations
status: todo
repo: agents-matrix-connector
value: "the connector's own database holds rooms, users, rules, the message queue and replies with one writer per table"
files: [src/agents_matrix_connector/migrations/__init__.py, src/agents_matrix_connector/migrations/0001_init.sql, tests/test_schema.py]
verify: "uv run --frozen pytest tests/test_schema.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-scaffold-and-cli]
model: sonnet
review: full
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc schema migrations

## Requirement

The connector's database schema (design D10; contract `matrix-connector-schema`). Paths are in code/agents-matrix-connector.

`src/agents_matrix_connector/migrations/__init__.py` (package marker) and `0001_init.sql`, applied by `agents_common.db.migrate.run_migrations(url, "agents_matrix_connector.migrations")`:

- `sync_state` (one row, `id smallint PRIMARY KEY CHECK (id = 1)` seeded with id 1; `next_batch text`, `filter_id text`, `last_sync_at timestamptz`, `updated_at`).
- `rooms` (`room_id text PRIMARY KEY`, `kind text CHECK IN ('dm','group','matrix','infrastructure')` nullable until classified, `name`, `alias`, `encrypted boolean NOT NULL DEFAULT false`, `message_request boolean NOT NULL DEFAULT false`, `membership text NOT NULL CHECK IN ('invite','join','leave')`, `inviter`, `member_count int NOT NULL DEFAULT 0`, `discovered_at`, `last_event_at`, `updated_at`).
- `users` (`user_id text PRIMARY KEY`, `display_name`, `facebook_id`, `first_seen_at`, `last_seen_at`), index on `facebook_id`.
- `room_members` (`room_id` FK rooms, `user_id` FK users, `membership text NOT NULL`, `display_name`, `updated_at`, PK `(room_id, user_id)`).
- `access_rules` (`id bigserial PK`, `list text CHECK IN ('allow','deny')`, `kind text CHECK IN ('user','facebook','room','alias','display_name')`, `value text NOT NULL CHECK (length(value) BETWEEN 1 AND 255)`, `note text`, `created_at`, `UNIQUE (list, kind, value)`, `CHECK (NOT (list = 'allow' AND kind = 'display_name'))`).
- `room_settings` (`room_id text PRIMARY KEY`, `preset_id uuid`, `trigger text CHECK IN ('all','mention')`, `updated_at`).
- `settings` (one row, id 1 seeded; `default_preset_id uuid`, `updated_at`).
- `inbound` (`id bigserial PK`, `event_id text NOT NULL UNIQUE`, `room_id text NOT NULL`, `sender text NOT NULL`, `sender_name`, `body text` nullable, `mentioned boolean NOT NULL DEFAULT false`, `origin_ts timestamptz`, `received_at timestamptz NOT NULL DEFAULT now()`, `status text NOT NULL CHECK IN ('new','in-progress','handled','ignored','failed')`, `reason text`, `run_id bigint`), partial index `(room_id, id) WHERE status = 'new'`, index `(room_id, id)`.
- `runs` (`id bigserial PK`, `room_id`, `preset_id uuid NOT NULL`, `kind text CHECK IN ('first','follow')`, `slug text`, `session_id uuid`, `message_id text`, `status text CHECK IN ('in-progress','handled','failed')`, `reason`, `started_at`, `finished_at`), partial index `WHERE status = 'in-progress'`, index `(room_id, id)`.
- `outbound` (`id bigserial PK`, `room_id`, `run_id bigint`, `kind text CHECK IN ('reply','notice')`, `body text NOT NULL`, `txn_id text NOT NULL UNIQUE`, `event_id text`, `status text CHECK IN ('pending','sent','failed')`, `reason`, `created_at`, `sent_at`), partial index `WHERE status = 'pending'`.
- `COMMENT ON TABLE` for every table naming its writer: `writer: bot sync` (sync_state, rooms, users, room_members), `writer: api` (access_rules, room_settings, settings), `queue: inserted by bot sync, transitions by bot worker` (inbound), `writer: bot worker` (runs, outbound).

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: the migration applies on an empty database and a second run applies nothing [evidence: test:tests/test_schema.py::test_migration_idempotent]
- AC2: every table carries its writer comment [evidence: test:tests/test_schema.py::test_writer_comments]
- AC3: status, kind and list checks reject unknown values and an allow display_name rule is rejected [evidence: test:tests/test_schema.py::test_check_constraints]
- AC4: rules are unique per (list, kind, value), inbound per event_id and outbound per txn_id [evidence: test:tests/test_schema.py::test_unique_keys]
- AC5: sync_state and settings hold exactly one seeded row and refuse id 2 [evidence: test:tests/test_schema.py::test_single_row_tables]

## Files

- `src/agents_matrix_connector/migrations/__init__.py`
- `src/agents_matrix_connector/migrations/0001_init.sql`
- `tests/test_schema.py`

## Interfaces

- `src/agents_matrix_connector/migrations/0001_init.sql` (contract `matrix-connector-schema`): read by every repository task and by mxc-service-entrypoints (`migrate`).

## Expected outcome

`run_migrations(url, "agents_matrix_connector.migrations")` creates the ten tables of design D10 with their constraints, indexes and writer comments.

## Steps

- Red: `tests/test_schema.py` using the `migrated_db` / `pg_url` fixtures of `agents_common.testing`; it fails on the missing package.
- Green: write the SQL. Run the verify (needs Docker for testcontainers).

## Notes

- Follow `code/agents-webhook/src/agents_webhook/migrations/0001_init.sql` style.
- Use `timestamptz` with `DEFAULT now()` for `*_at` columns that are set on insert.
