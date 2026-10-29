---
title: mxc relay once per turn
status: todo
repo: agents-matrix-connector
value: a Matrix room gets one reply when several of its messages were answered by one agent turn
files: [pyproject.toml, uv.lock, src/agents_matrix_connector/migrations/0003_run_relayed_turn.sql, src/agents_matrix_connector/db/runs.py, src/agents_matrix_connector/tracker.py, tests/test_tracker.py, tests/test_schema.py, MEMORY.md]
verify: "uv run ruff check . && uv run ruff format --check . && uv run pytest tests/test_tracker.py tests/test_schema.py"
depends_on: [common-release-0-4-0]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 10
expected_tokens: 1875101
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc relay once per turn

## Requirement

Goal G4 (README), verbatim: "Matrix chat messages in a room whose run is in progress are delivered at once, and an answer shared by merged messages is relayed to the room once."

Design D18 (tracker part), verbatim: "The tracker relays a completed turn's final text once per turn, in any evaluation order (interrogate 1: `tick` finishes runs one at a time, so a rule over in-progress runs relays twice): a run that finishes from a completed turn records that turn id in `runs.relayed_turn_id` (new nullable column, migration `0003_run_relayed_turn.sql`, written only by the tracker inside the same guarded `runs.finish`); a run whose message links to a turn already recorded on another run of its room finishes `handled` with reason `merged` and no reply. agents-common `Message.turn_id` (new, released 0.4.0, connector pin moved) carries the link; the fake orchestrator can complete one turn for several messages."

Design anti-goal, verbatim: "The same final answer relayed twice to a Matrix room (D18)."

Scope (agents-matrix-connector): `pyproject.toml` and `uv.lock` (agents-common v0.3.0 to v0.4.0, both the dependency and the testing extra), `src/agents_matrix_connector/migrations/0003_run_relayed_turn.sql` (new, `runs.relayed_turn_id`), `src/agents_matrix_connector/db/runs.py` (`finish` writes it, `turn_relayed`), `src/agents_matrix_connector/tracker.py` (the once-per-turn rule), `tests/test_tracker.py`, `tests/test_schema.py`, `MEMORY.md`. Test no longer accurate (named): `tests/test_schema.py` pins the exact `MIGRATIONS` list; it gains `0003_run_relayed_turn.sql`.

## Acceptance conditions

- ac1: the connector pins agents-common v0.4.0 in both dependency lines and uv.lock, and Message has turn_id [evidence: command:test "$(grep -c 'agents-common@v0.4.0' pyproject.toml)" = 2 && ! grep -q 'agents-common@v0.3.0' pyproject.toml && uv run --frozen python -c "from agents_common.orchestrator import Message; assert 'turn_id' in Message.model_fields"]
- ac2: (CI or a Docker host) migration 0003 adds the nullable runs.relayed_turn_id with its writer comment, and the migration list, idempotence and writer-comment pins pass with it (new) [evidence: test:tests/test_schema.py::test_run_relayed_turn_column]
- ac3: (CI or a Docker host) two in-progress runs of one room whose messages link to the same completed turn produce exactly one reply in one tick; the relaying run stores relayed_turn_id in its finish and the other finishes handled with reason merged and sends nothing (new) [evidence: test:tests/test_tracker.py::test_merged_turn_relayed_once]
- ac4: (CI or a Docker host) a run evaluated in a later tick, after its sibling already finished and relayed the same turn (for example its poll hit OrchestratorUnavailable once), still sends nothing and finishes handled merged (new) [evidence: test:tests/test_tracker.py::test_merged_turn_not_relayed_after_sibling_finished]
- ac5: (CI or a Docker host) runs whose messages link to different turns each relay their own answer as today (new) [evidence: test:tests/test_tracker.py::test_distinct_turns_each_relayed]
- ac6: (CI or a Docker host) the existing tracker and schema cases pass, the schema MIGRATIONS list changed only to add 0003 (named) [evidence: command:uv run pytest tests/test_tracker.py tests/test_schema.py]
- ac7: MEMORY.md has a dated entry on relaying a merged turn once, the persisted relayed_turn_id and why [evidence: command:grep -q 'merged' MEMORY.md && grep -q 'relayed_turn_id' MEMORY.md]
- ac8: lint passes and the tracker and schema suites run [evidence: command:uv run ruff check . && uv run ruff format --check . && uv run pytest tests/test_tracker.py tests/test_schema.py]

## Files

- `pyproject.toml`
- `uv.lock`
- `src/agents_matrix_connector/migrations/0003_run_relayed_turn.sql`
- `src/agents_matrix_connector/db/runs.py`
- `src/agents_matrix_connector/tracker.py`
- `tests/test_tracker.py`
- `tests/test_schema.py`
- `MEMORY.md`

## Interfaces

- `migrations/0003_run_relayed_turn.sql` (next free number; if taken, the next free one, reported so the orchestrator amends `files`): `ALTER TABLE runs ADD COLUMN IF NOT EXISTS relayed_turn_id text NULL`, an index on `(room_id, relayed_turn_id)`, and the writer comment the schema test expects (written only by the tracker through `runs.finish`).
- `db/runs.py`: `finish(conn, run_id, status, reason=None, *, relayed_turn_id=None)` writes it in the same guarded `in-progress -> handled|failed` transition; `turn_relayed(conn, room_id, turn_id, *, exclude_run_id) -> bool`.
- `tracker._outcome`: when the run's message has `turn.status == "completed"` and `runs.turn_relayed(room, message.turn_id, exclude_run_id=run.id)`, the outcome is `_Outcome("handled", "merged")` with no chunks; otherwise the run relays as today (including `_send_match`) and `_finish` stores `relayed_turn_id = message.turn_id` for every run it finishes from a completed turn, so the rule holds in any evaluation order (design D18, interrogate 1).
- New reason constant `MERGED = "merged"` beside `ALREADY_SENT` / `EMPTY_REPLY`.

## Expected outcome

When several chat messages were answered by one merged agent turn, the room gets that answer once.

## Steps

- Read `pyproject.toml`, `src/agents_matrix_connector/tracker.py`, `db/runs.py`, `db/__init__.py` (`transition`), `migrations/0002_agent_sends.sql`, `tests/test_tracker.py`, `tests/test_schema.py`, `tests/conftest.py` and agents-common's `fake_orchestrator.complete_turn(..., turn_id=)` in one pass.
- Move the pin (`uv lock`); red: add the new tests named in the acceptance conditions and add `0003_run_relayed_turn.sql` to the `MIGRATIONS` list of `tests/test_schema.py` (no longer accurate: it lists the migrations exactly); they need Postgres and fail in CI until green.
- Green: write the migration, the runs writer, the once-per-turn rule and the MEMORY entry; run the task's verify; expect lint clean (the tracker suite runs in CI). Quote the summary lines.

## Notes

- Depends on the agents-common v0.4.0 tag on origin (common-release-0-4-0 ac3, pushed by the orchestrator session).
- Runs finish through the existing guarded transition in `db/runs.py`; `relayed_turn_id` gets no other writer.
- Tree state: the connector's repo tests (`pool`, `conn`, `url` fixtures from `agents_common.testing.migrated_db`) need Postgres through Docker, absent in agent pods; they run in CI on the PR and the reviewer quotes the CI summary line.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate (panel fable, opus, sonnet; lead verdict .scratchpad/immediate-delivery/interrogate.md): Requirement and acceptance conditions follow the amended design
