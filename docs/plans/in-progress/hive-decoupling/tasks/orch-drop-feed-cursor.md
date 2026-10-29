---
title: orch drop feed cursor
status: in-progress
repo: agents-orchestrator
value: the dead feed bookkeeping column is gone from the schema
files: [src/agents_orchestrator/db/migrations/0011_drop_feed_cursor.sql, src/agents_orchestrator/db/leadership.py, tests/test_migrations.py, tests/test_leadership_pass.py, README.md]
verify: "uv run --frozen pytest tests/test_migrations.py tests/test_leadership_pass.py tests/test_hive_push.py && mise run lint"
depends_on: [orch-hive-feed-removal]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 936557
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch drop feed cursor

## Requirement

README Goal G1, verbatim: "Members receive no streamed activity: the dispatcher sends no appended feed note, `hive_state` is re-pushed only when the leader, epoch, membership or readiness changes, and `session_leaders.feed_cursor` is dropped."

Design D1, verbatim: "`session_leaders.feed_cursor` loses its only writer and readers (`hive.py`, `_set_leader`; probed: no view, export or other reader), so a migration (next free number, 0009 if nothing else lands) drops it."

Constraint, verbatim: "Orchestrator migration number: the next free one at build time (slash-commands adds 0008, so 0009 if nothing else lands); the task is amended to the free number if 0009 is taken."

Open question Q6 (pending gate, recommended yes): "Drop the session_leaders.feed_cursor column in a migration rather than leave it dead?"

Scope (agents-orchestrator):
- `src/agents_orchestrator/db/migrations/0011_drop_feed_cursor.sql`: `ALTER TABLE session_leaders DROP COLUMN IF EXISTS feed_cursor;` with a header comment (idempotent like 0003 and 0006).
- `src/agents_orchestrator/db/leadership.py` `_set_leader`: the INSERT no longer names `feed_cursor` nor reads `max(events.id)`; the docstring sentence about the feed cursor goes.
- `README.md` `### Leadership` step 1: the sentence "The new row starts `feed_cursor` at the session's newest event id, so history is never pushed as current activity." goes.
- Tests no longer accurate, named: `tests/test_migrations.py::test_0003_hive_schema` (runs every migration, then asserts `feed_cursor` exists: it now copies only 0001-0003, like the other per-version tests, and keeps its 0003 assertions); `tests/test_migrations.py::test_0003_feed_cursor_default` (runs on the head schema through `pool`: it now runs 0001-0003 on `empty_dsn`, keeping its assertion); `tests/test_leadership_pass.py::test_initial_leader` (asserts the cursor starts at the newest event: that assertion is removed, the rule is gone; the rest stays).
- New: `tests/test_migrations.py::test_drop_feed_cursor_migration` (after every earlier migration the column exists; the new migration removes it; re-running its SQL is a no-op; `run_migrations` returns `["0011"]` then `[]`).
- Depends on orch-hive-feed-removal: no code reads or writes the column when it is dropped.

Builder check settlement 1 (2026-10-27, my call): the build starts only after slash-commands-from-chat and matrix-connector-agent-initi have merged. `v0.4.0` (the plugins release tag, `vX.Y.Z`), `0.4.0` (the same without the `v`) and `0011` (the orchestrator migration number, four digits) in this task are placeholders: orch-activity-route reads the real values from main and replaces them here with `ticket.py amend` before this task starts. No number in this task is assumed; `0.4.0` and `0009` in design.md are only the expectation.

## Acceptance conditions

- ac1: the migration drops session_leaders.feed_cursor and is idempotent [evidence: test:tests/test_migrations.py::test_drop_feed_cursor_migration]
- ac2: the 0003 schema test still tests 0003 alone (updated, named) [evidence: test:tests/test_migrations.py::test_0003_hive_schema]
- ac3: the 0003 feed_cursor default test runs on the 0003 schema (updated, named) [evidence: test:tests/test_migrations.py::test_0003_feed_cursor_default]
- ac4: the initial election still writes epoch 1, reason initial, with no cursor (updated, named) [evidence: test:tests/test_leadership_pass.py::test_initial_leader]
- ac5: no source or README line names feed_cursor outside migration 0003 and the new migration [evidence: command:! grep -rn feed_cursor src/agents_orchestrator --include=*.py && ! grep -n feed_cursor README.md]
- ac6: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_migrations.py tests/test_leadership_pass.py tests/test_hive_push.py && mise run lint]

## Files

- `src/agents_orchestrator/db/migrations/0011_drop_feed_cursor.sql`
- `src/agents_orchestrator/db/leadership.py`
- `tests/test_migrations.py`
- `tests/test_leadership_pass.py`
- `README.md`

## Interfaces

- Migration `0011_drop_feed_cursor.sql` (or the next free number; amend the task if 0011 is taken): `ALTER TABLE session_leaders DROP COLUMN IF EXISTS feed_cursor;`.
- `db/leadership.py:_set_leader` INSERT columns `(session_id, agent_id, epoch, since, reason)`.

## Expected outcome

The live schema has no `feed_cursor`; elections write no cursor; the 0003 tests still describe 0003.

## Steps

- Check the free migration number: `ls src/agents_orchestrator/db/migrations/`; if 0011 exists, stop and report so the task is amended.
- Red: add `test_drop_feed_cursor_migration`, restrict `test_0003_hive_schema` and `test_0003_feed_cursor_default` to 0001-0003, drop the cursor assertion in `test_initial_leader`; run `uv run --frozen pytest tests/test_migrations.py tests/test_leadership_pass.py`: the new test fails.
- Green: the migration, `_set_leader`, README step 1; run the task's verify: passes. Quote the summary line.

## Notes

- Data change: the column's values are dropped in the live database on deploy (listed in design.md Irreversible operations).
- Follow the per-version copy pattern of `test_0006_compaction_column` (`MIGRATIONS_DIR.glob("000[1-3]_*.sql")`).
- DB tests are CI-only in agent pods (no Docker); CI on the PR is the gate.

- 2026-10-27 amended: builder check settlement 1: migration number and plugins tag are placeholders until orch-activity-route amends them from main
