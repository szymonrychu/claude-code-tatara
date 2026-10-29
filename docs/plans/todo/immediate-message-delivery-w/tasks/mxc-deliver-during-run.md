---
title: mxc deliver during run
status: todo
repo: agents-matrix-connector
value: a Matrix follow-up reaches the agent at once while it is still working
files: [src/agents_matrix_connector/db/inbound.py, tests/test_inbound_repo.py, tests/test_worker.py, README.md, MEMORY.md]
verify: "uv run ruff check . && uv run ruff format --check . && uv run pytest tests/test_inbound_repo.py tests/test_worker.py"
depends_on: [mxc-relay-once-per-turn]
model: sonnet
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

# mxc deliver during run

## Requirement

User request (2026-10-28 21:02Z via mx-34 #262), verbatim: "currently the messages wait for too long. [...] message should get through PTY immediately and let either Claude Code or even agent queue them internally."

Goal G4 (README), verbatim: "Matrix chat messages in a room whose run is in progress are delivered at once, and an answer shared by merged messages is relayed to the room once."

Design D18 (delivery part), verbatim: "`inbound.rooms_ready` also returns a room whose in-progress runs are all `follow` runs with a posted message (`message_id` set) and a session, so its new rows are claimed into a new follow run and posted at once (server default `immediate`); a room whose first run has not posted yet still waits (there is no session to post to)."

Scope (agents-matrix-connector): `src/agents_matrix_connector/db/inbound.py` (`rooms_ready`), `tests/test_inbound_repo.py`, `tests/test_worker.py`, `README.md` (the run model), `MEMORY.md`.

## Acceptance conditions

- ac1: (CI or a Docker host) rooms_ready returns a room with new rows whose in-progress runs are all follow runs with a message_id and a session (new) [evidence: test:tests/test_inbound_repo.py::test_rooms_ready_includes_room_with_posted_follow_run]
- ac2: (CI or a Docker host) rooms_ready does not return a room whose in-progress run is a first run or has no message_id yet (new) [evidence: test:tests/test_inbound_repo.py::test_rooms_ready_waits_for_unposted_or_first_run]
- ac3: (CI or a Docker host) the worker claims a room's new rows into a second follow run and posts them to the bound session while the first run is still in progress (new) [evidence: test:tests/test_worker.py::test_new_messages_posted_while_run_in_progress]
- ac4: (CI or a Docker host) the existing inbound and worker cases pass unchanged [evidence: command:uv run pytest tests/test_inbound_repo.py tests/test_worker.py]
- ac5: README and MEMORY.md describe delivery during a run and why [evidence: command:grep -qi 'in progress' README.md && grep -q 'rooms_ready' MEMORY.md]
- ac6: lint passes and the suites run [evidence: command:uv run ruff check . && uv run ruff format --check . && uv run pytest tests/test_inbound_repo.py tests/test_worker.py]

## Files

- `src/agents_matrix_connector/db/inbound.py`
- `tests/test_inbound_repo.py`
- `tests/test_worker.py`
- `README.md`
- `MEMORY.md`

## Interfaces

- `db/inbound.rooms_ready(conn) -> list[str]`: a room is ready when it has `status = 'new'` rows and every `runs` row of it with `status = 'in-progress'` has `kind = 'follow'`, `message_id IS NOT NULL` and `session_id IS NOT NULL` (none in progress keeps today's meaning); order by the oldest new row as today.
- The worker's `_room` / `_follow` / `_claim` path is reused unchanged: a bound room's new rows become a new follow run.

## Expected outcome

A Matrix user's follow-up message reaches the agent at once while it is still working on the previous one; the answer reaches the room once (mxc-relay-once-per-turn).

## Steps

- Read `db/inbound.py`, `db/runs.py`, `worker.py` (`tick`, `_room`, `_follow`, `_claim`, `_deliver`), `tests/test_inbound_repo.py`, `tests/test_worker.py`, README and MEMORY.md in one pass.
- Red: add ac1 to ac3; they need Postgres and fail in CI until green.
- Green: change `rooms_ready`, README and MEMORY; run the task's verify; expect lint clean (the suites run in CI). Quote the summary lines.

## Notes

- Ordering inside a room stays by row id: a new follow run claims only rows newer than every claimed one, because `claim_room` takes `status = 'new'` rows only.
- The PREAMBLE rule of `_deliver` (sent when the session has no other run in the room) stays as is; a second concurrent run gets no preamble.
- Depends on mxc-relay-once-per-turn, so a room can never get the same merged answer twice.
- Tree state: the connector's repo tests (`pool`, `conn`, `url` fixtures from `agents_common.testing.migrated_db`) need Postgres through Docker, absent in agent pods; they run in CI on the PR and the reviewer quotes the CI summary line.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
