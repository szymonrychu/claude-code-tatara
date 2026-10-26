---
title: compaction status projection
status: done
repo: agents-orchestrator
value: the orchestrator knows when each agent last compacted
files: [src/agents_orchestrator/db/migrations/0006_compaction.sql, src/agents_orchestrator/db/status.py, src/agents_orchestrator/ingester/loop.py, tests/test_ingester.py, tests/test_migrations.py, README.md]
verify: "uv run --frozen pytest -q tests/test_ingester.py tests/test_migrations.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: opus
review: ""
verified_head: cc336cb6b426e15c3689659727502205d4e2c3b8
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: 3
actual_minutes: 323
actual_tokens: 2641899
actual_roles: "impl 28, review 1"
actual_role_tokens: "impl 2570954, review 70945"
---

# compaction status projection

## Requirement

Goal G1: "the orchestrator moves leadership to another ready agent of the cluster" when the leader is about to compact. User call: "every compaction counts, auto and manual."

Design D2, verbatim: both `compacting` (before) and `compacted` (after, from the transcript boundary) count as a compaction of that agent. Auto, manual, the orchestrator's compact command, the wrapper's idle auto-compact and Claude Code's own idle compaction all count.

Design D3, verbatim: migration `0006_compaction.sql` adds `agent_status.compaction_at timestamptz` (nullable). The ingester's projection sets it from the event's own `ts` (the wrapper's clock, when the compaction was reported), never from the ingest time, and never moves it backwards (`greatest(compaction_at, ts)`), when it stores a `compacting` or `compacted` event of that agent; it NOTIFYs `status` as it does for `context` and wakes the dispatcher (D15). Nothing else writes it. An old event ingested late (a stream resume or replay) therefore carries its old time, and a leader elected after it (`since` later than the event's `ts`) is never handed over for it.

Design D15, verbatim (ingester half): when the ingester projects a compaction (D3) it also sends `NOTIFY leadership_requested {session_id}`.

Scope:
- `src/agents_orchestrator/db/migrations/0006_compaction.sql`: `ALTER TABLE agent_status ADD COLUMN IF NOT EXISTS compaction_at timestamptz;` (idempotent like 0003).
- `src/agents_orchestrator/db/status.py`: a `set_compaction(conn, agent_id, at)` (name left to the builder) that sets `compaction_at = greatest(compaction_at, at)` and `updated_at = now()`.
- `src/agents_orchestrator/ingester/loop.py` `_project`: a branch for `compacting` and `compacted` that calls it with the envelope's `ts` (`env.ts`), then `status.notify_status` and `NOTIFY leadership_requested {session_id}` (the channel constant `db/leadership.CHANNEL`); the event is still stored as an events row.
- README: the `agent_status` row of the tables list names the last compaction time (`compaction_at`, written by the ingester on `compacting` or `compacted`).
- Tests in `tests/test_ingester.py`: emitting `compacting` through the fake wrapper sets `compaction_at` to the event's `ts` and NOTIFYs `status` and `leadership_requested`; a later `compacted` moves it forward; an event whose `ts` is older than the stored value (a late or replayed event) never moves it backwards; other event types leave it unchanged.
- Tests no longer accurate, to update: `tests/test_migrations.py::test_fresh_database_gets_all_tables` and `tests/test_migrations.py::test_presets_migration_on_existing_sessions` pin the applied migration versions as ending at `0005`; they now end at `0006`. Add a `0006` schema test there (column exists, nullable, rerun is a no-op).

Notes: the fake wrapper's `emit` does not validate event names (`tests/fakes/fake_wrapper.py:314`), so this task does not need the wrapper 0.3.0 pin. Reuse the `context` branch's shape (`ingester/loop.py:194-196`). The dispatcher reads the column in task leadership-auto-handover; do not touch `db/leadership.py` here. Docker disk: the DB tests need testcontainers (or the shared Postgres override); a full Docker VM disk is an environment blocker to report, not to work around.

## Acceptance conditions

- AC1: a stored `compacting` event sets `agent_status.compaction_at` to the event's own `ts`, not the ingest time, and NOTIFYs `status` and `leadership_requested {session_id}` [evidence: test:tests/test_ingester.py::test_compacting_sets_compaction_at]
- AC2: a later `compacted` event moves `compaction_at` forward and other event types leave it unchanged [evidence: test:tests/test_ingester.py::test_compacted_moves_compaction_at]
- AC3: a late or replayed compaction event with an older `ts` never moves `compaction_at` backwards and never sets it later than its own `ts` [evidence: test:tests/test_ingester.py::test_late_compaction_event_keeps_its_time]
- AC4: migration 0006 adds the nullable column, is idempotent, and the applied versions end at 0006 [evidence: command:uv run --frozen pytest -q tests/test_migrations.py]
- AC5: README documents the column and every table stays documented [evidence: command:uv run --frozen pytest -q tests/test_readme_api.py]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/db/migrations/0006_compaction.sql`
- `src/agents_orchestrator/db/status.py`
- `src/agents_orchestrator/ingester/loop.py`
- `tests/test_ingester.py`
- `tests/test_migrations.py`
- `README.md`

## Interfaces

See the Requirement and the acceptance conditions above.

## Expected outcome

See the Requirement and the acceptance conditions above.

## Steps

- Red: add the three ingester tests to `tests/test_ingester.py` and the 0006 schema test plus the updated version lists to `tests/test_migrations.py`; run `uv run --frozen pytest -q tests/test_ingester.py tests/test_migrations.py`: the new tests fail (no column, no projection).
- Green: add `0006_compaction.sql`, the `db/status.py` setter, the ingester branch with the `leadership_requested` NOTIFY, and the README row; run the task's verify command: passes.

## Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 amended: interrogate 2026-10-26 (fable, opus, sonnet): findings 2 and 3 (wake, event time)

- 2026-10-26 done
