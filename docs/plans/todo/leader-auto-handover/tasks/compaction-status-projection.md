---
title: compaction status projection
status: todo
repo: agents-orchestrator
value: the orchestrator knows when each agent last compacted
files: [src/agents_orchestrator/db/migrations/0006_compaction.sql, src/agents_orchestrator/db/status.py, src/agents_orchestrator/ingester/loop.py, tests/test_ingester.py, tests/test_migrations.py, README.md]
verify: "uv run --frozen pytest -q tests/test_ingester.py tests/test_migrations.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# compaction status projection

## Requirement

Goal G1: "the orchestrator moves leadership to another ready agent of the cluster" when the leader is about to compact. User call: "every compaction counts, auto and manual."

Design D2, verbatim: both `compacting` (before) and `compacted` (after, from the transcript boundary) count as a compaction of that agent. Auto, manual, the orchestrator's compact command, the wrapper's idle auto-compact and Claude Code's own idle compaction all count.

Design D3, verbatim: migration `0006_compaction.sql` adds `agent_status.compaction_at timestamptz` (nullable). The ingester's projection sets it to the database clock (`now()`) when it stores a `compacting` or `compacted` event of that agent, and NOTIFYs `status` as it does for `context`. Nothing else reads or writes it.

Scope:
- `src/agents_orchestrator/db/migrations/0006_compaction.sql`: `ALTER TABLE agent_status ADD COLUMN IF NOT EXISTS compaction_at timestamptz;` (idempotent like 0003).
- `src/agents_orchestrator/db/status.py`: a `set_compaction(conn, agent_id)` (name left to the builder) that sets `compaction_at = now()` and `updated_at = now()`.
- `src/agents_orchestrator/ingester/loop.py` `_project`: a branch for `compacting` and `compacted` that calls it and `status.notify_status`; the event is still stored as an events row.
- README: the `agent_status` row of the tables list names the last compaction time (`compaction_at`, written by the ingester on `compacting` or `compacted`).
- Tests in `tests/test_ingester.py`: emitting `compacting` through the fake wrapper sets `compaction_at` (not null, within the test's DB-clock window) and NOTIFYs `status`; a later `compacted` moves it forward; other event types leave it unchanged.
- Tests no longer accurate, to update: `tests/test_migrations.py::test_fresh_database_gets_all_tables` and `tests/test_migrations.py::test_presets_migration_on_existing_sessions` pin the applied migration versions as ending at `0005`; they now end at `0006`. Add a `0006` schema test there (column exists, nullable, rerun is a no-op).

Notes: the fake wrapper's `emit` does not validate event names (`tests/fakes/fake_wrapper.py:314`), so this task does not need the wrapper 0.3.0 pin. Reuse the `context` branch's shape (`ingester/loop.py:194-196`). The dispatcher reads the column in task leadership-auto-handover; do not touch `db/leadership.py` here. Docker disk: the DB tests need testcontainers (or the shared Postgres override); a full Docker VM disk is an environment blocker to report, not to work around.

## Acceptance conditions

- AC1: a stored `compacting` event sets `agent_status.compaction_at` on the database clock and NOTIFYs `status` [evidence: test:tests/test_ingester.py::test_compacting_sets_compaction_at]
- AC2: a later `compacted` event moves `compaction_at` forward and other event types leave it unchanged [evidence: test:tests/test_ingester.py::test_compacted_moves_compaction_at]
- AC3: migration 0006 adds the nullable column, is idempotent, and the applied versions end at 0006 [evidence: command:uv run --frozen pytest -q tests/test_migrations.py]
- AC4: README documents the column and every table stays documented [evidence: command:uv run --frozen pytest -q tests/test_readme_api.py]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/db/migrations/0006_compaction.sql`
- `src/agents_orchestrator/db/status.py`
- `src/agents_orchestrator/ingester/loop.py`
- `tests/test_ingester.py`
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
