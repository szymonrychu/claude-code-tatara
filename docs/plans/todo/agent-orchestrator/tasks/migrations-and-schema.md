---
title: migrations and schema
status: todo
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
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# migrations and schema

## Requirement

Schema 0001 and the migration runner (design D3, D20).

- Tables, columns and constraints exactly as design.md D3 and design-orchestrator section 2: `clusters` (id uuid pk, slug unique, spec jsonb, generation int, observed_generation int, desired active|deleting, status jsonb, created_at, deleted_at, purged bool), `agents` (id uuid, cluster_id fk cascade, ordinal, pod_name, url, pod_phase, ready, session_id, session_created_at, gone_at; unique (cluster_id, ordinal)), `agent_status` (agent_id pk fk cascade, state unknown|booting|idle|busy|dead, free_since, current_turn_id, context_used_tokens, context_window_tokens, context_pct, last_seq, peers jsonb, updated_at), `messages` (id bigserial, cluster_id fk cascade, target_agent_id, text, status queued|dispatching|sent|failed|cancelled, agent_id, turn_id, attempts, error, created_at, dispatched_at; index (cluster_id, status, id)), `turns` (turn_id pk, agent_id fk cascade, origin, started_at, completed_at, status, final_text, usage jsonb), `events` (id bigserial, cluster_id fk cascade, agent_id, session_id, seq, ts, type, turn_id, data jsonb; unique (agent_id, session_id, seq); indexes (cluster_id, id desc) and (agent_id, id desc)), `commands` (id bigserial, agent_id fk cascade, kind interrupt|compact|restart, status queued|running|done|failed|cancelled, result jsonb, created_at, started_at, finished_at), `checks` (id bigserial, cluster_id fk cascade, command, status queued|running|passed|failed|cancelled, job_name, exit_code, log_tail, created_at, started_at, finished_at). Enumerations are CHECK constraints on text columns.
- `migrate.run_migrations(dsn)`: applies `migrations/NNNN_*.sql` in order, each in its own transaction, under `pg_advisory_lock` on a fixed key, recording `schema_migrations(version, applied_at)`; a rerun applies nothing; two concurrent runs serialise and both succeed.
- `pool.open_pool(dsn) -> AsyncConnectionPool`; `pool.notify(conn, channel, payload: dict)` (JSON payload); `pool.listen(dsn, channels) -> AsyncIterator[tuple[str, dict]]` on a dedicated connection that reconnects with backoff.
- `tests/conftest.py`: session-scoped testcontainers Postgres (postgres:18-alpine), migrated once into a template database; function-scoped `dsn` and `pool` fixtures on a fresh database cloned from the template.
- `tests/factories.py`: `insert_cluster`, `insert_agent`, `set_agent_status`, `insert_message`, `insert_event`, `insert_command`, `insert_check` writing raw SQL rows with sensible defaults, so table-level tests never depend on another task's repository module.

## Acceptance conditions

- AC1: a fresh database gets every table and schema_migrations records 0001 [evidence: test:tests/test_migrations.py::test_fresh_database_gets_all_tables]
- AC2: rerunning migrations is a no-op [evidence: test:tests/test_migrations.py::test_rerun_is_noop]
- AC3: two concurrent run_migrations calls serialise and both succeed [evidence: test:tests/test_migrations.py::test_concurrent_migrate_serialises]
- AC4: a duplicate (agent_id, session_id, seq) event is rejected by the unique constraint [evidence: test:tests/test_migrations.py::test_events_unique_agent_session_seq]
- AC5: deleting a cluster row cascades to agents, messages, events, turns, commands and checks [evidence: test:tests/test_migrations.py::test_cluster_delete_cascades]
- AC6: notify and listen round-trip a JSON payload [evidence: test:tests/test_migrations.py::test_notify_listen_roundtrip]

## Files

- `src/agent_orchestrator/db/__init__.py`
- `src/agent_orchestrator/db/pool.py`
- `src/agent_orchestrator/db/migrate.py`
- `src/agent_orchestrator/db/migrations/0001_init.sql`
- `tests/conftest.py`
- `tests/factories.py`
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
