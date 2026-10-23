---
title: migrations and schema
status: done
repo: agent-orchestrator
value: "The one Postgres schema every process coordinates through, applied safely by concurrent initContainers."
files: [src/agent_orchestrator/db/__init__.py, src/agent_orchestrator/db/pool.py, src/agent_orchestrator/db/migrate.py, src/agent_orchestrator/db/migrations/0001_init.sql, tests/conftest.py, tests/factories.py, tests/test_migrations.py]
verify: "uv run pytest tests/test_migrations.py -q && mise run lint"
depends_on: [scaffold-repo-and-cli]
owns: [schema-v1, pg-fixture]
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-migrations-and-schema/agent-orchestrator
branch: agent-orchestrator-migrations-and-schema
verified_head: 25a8811aefde4d144139311c3de985332088fd24
run: agent-orchestrator
provides: [insert-turn-factory, empty-dsn-fixture]
acs_for_audit: []
process_gaps: []
fork_point: 7844dd22f9b1dbdf592cc5c55c9d2b4160acbed7
---

# migrations and schema

## Requirement

Schema 0001 and the migration runner (design D3, D20).

- Tables, columns and constraints exactly as design.md D3 and design-orchestrator section 2: `clusters` (id uuid pk, slug unique, spec jsonb, generation int, observed_generation int, desired active|deleting, status jsonb, created_at; no deleted_at or purged column: a discard deletes the row and the cascade removes the history, D15), `agents` (id uuid, cluster_id fk cascade, last_dispatched_at timestamptz null (D23: written only by the dispatch claim; its row change forces the concurrent-claim recheck), ordinal, pod_name, url, pod_phase, ready, session_id, session_created_at, gone_at; unique (cluster_id, ordinal)), `agent_status` (agent_id pk fk cascade, wrapper_idle_since timestamptz null (stored wrapper `idle_since`, informational and never compared with database time), state unknown|booting|idle|busy|dead, free_since, current_turn_id, context_used_tokens, context_window_tokens, context_pct, last_seq, peers jsonb, updated_at), `messages` (id bigserial, cluster_id fk cascade, heartbeat_at timestamptz null (D24: the dispatcher refreshes it while a send is in flight), target_agent_id, text, status queued|dispatching|verifying|sent|failed|cancelled, agent_id, turn_id, attempts, error, created_at, dispatched_at, not_before timestamptz null (D24: the earliest retry time of a requeued message), ambiguous_at timestamptz null (D24: when the send became ambiguous; the settle window and deadline are measured from it); index (cluster_id, status, id)), `turns` (turn_id pk, agent_id fk cascade, origin, started_at, completed_at, status, final_text, usage jsonb), `events` (id bigserial, cluster_id fk cascade, agent_id, session_id, seq, ts, type, turn_id, data jsonb; unique (agent_id, session_id, seq); indexes (cluster_id, id desc) and (agent_id, id desc)), `commands` (id bigserial, agent_id fk cascade, kind interrupt|compact|restart|rebootstrap, status queued|running|done|failed|cancelled, result jsonb, created_at, started_at, finished_at), `checks` (id bigserial, cluster_id fk cascade, command, status queued|running|passed|failed|cancelled, job_name, exit_code, log_tail, created_at, started_at, finished_at). Enumerations are CHECK constraints on text columns. `messages.error` is free text with the documented reasons `dispatcher_lost`, `ambiguous`, `ambiguous_not_started`, `target_gone`, `session_gone`, `unavailable`, `rejected`, `config_error`.
- `migrate.run_migrations(dsn)`: applies `migrations/NNNN_*.sql` in order, each in its own transaction, under `pg_advisory_lock` on a fixed key, recording `schema_migrations(version, applied_at)`; a rerun applies nothing; two concurrent runs serialise and both succeed.
- `pool.open_pool(dsn) -> AsyncConnectionPool`; `pool.notify(conn, channel, payload: dict)` (JSON payload); `pool.listen(dsn, channels) -> AsyncIterator[tuple[str, dict]]` on a dedicated connection that reconnects with backoff.
- `tests/conftest.py`: session-scoped testcontainers Postgres (postgres:18-alpine), migrated once into a template database; function-scoped `dsn` and `pool` fixtures on a fresh database cloned from the template.
- `tests/factories.py`: `insert_cluster`, `insert_agent`, `set_agent_status`, `insert_message`, `insert_event`, `insert_command`, `insert_check` writing raw SQL rows with sensible defaults (including `last_dispatched_at`, `heartbeat_at`, `dispatched_at`, `not_before`, `ambiguous_at` and `status` overrides), so table-level tests never depend on another task's repository module.

## Acceptance conditions

- AC1: a fresh database gets every table and schema_migrations records 0001 [evidence: test:tests/test_migrations.py::test_fresh_database_gets_all_tables]
- AC2: rerunning migrations is a no-op [evidence: test:tests/test_migrations.py::test_rerun_is_noop]
- AC3: two concurrent run_migrations calls serialise and both succeed [evidence: test:tests/test_migrations.py::test_concurrent_migrate_serialises]
- AC4: a duplicate (agent_id, session_id, seq) event is rejected by the unique constraint [evidence: test:tests/test_migrations.py::test_events_unique_agent_session_seq]
- AC5: deleting a cluster row cascades to agents, messages, events, turns, commands and checks [evidence: test:tests/test_migrations.py::test_cluster_delete_cascades]
- AC6: notify and listen round-trip a JSON payload [evidence: test:tests/test_migrations.py::test_notify_listen_roundtrip]
- AC7: agents.last_dispatched_at, agent_status.wrapper_idle_since and messages.heartbeat_at exist, and commands.kind accepts rebootstrap [evidence: test:tests/test_migrations.py::test_dispatch_columns_and_rebootstrap_kind]
- AC8: messages.not_before and messages.ambiguous_at exist, messages.status accepts verifying, and clusters has no deleted_at or purged column [evidence: test:tests/test_migrations.py::test_retry_columns_verifying_status_and_no_purge_columns]

## Files

- `src/agent_orchestrator/db/__init__.py`
- `src/agent_orchestrator/db/pool.py`
- `src/agent_orchestrator/db/migrate.py`
- `src/agent_orchestrator/db/migrations/0001_init.sql`
- `tests/conftest.py`
- `tests/factories.py`
- `tests/test_migrations.py`

## Interfaces

- `agent_orchestrator.db.migrate:run_migrations(dsn: str) -> list[str]` (applied versions)
- `agent_orchestrator.db.pool:open_pool`, `notify`, `listen`
- contract `schema-v1` in `db/migrations/0001_init.sql`; contract `pg-fixture` in `tests/conftest.py` (`dsn`, `pool`) and `tests/factories.py`

## Expected outcome

A real Postgres in tests carries the full schema; migrations are idempotent and safe under concurrent initContainers.

## Steps

- Write tests/conftest.py, tests/factories.py and tests/test_migrations.py with the eight named tests; run `uv run pytest tests/test_migrations.py -q`; expect failures.
- Write 0001_init.sql, migrate.py and pool.py.
- Rerun; expect `8 passed`; run `mise run lint`.

## Notes

Docker is required (testcontainers); it is available locally and on ubuntu-latest. Only this task edits tests/conftest.py and tests/factories.py: put any later fixture in its own test file or under tests/fakes/. Writers per table (D3) are enforced by code ownership, not by database roles.
