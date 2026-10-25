---
title: runs and outbound repo
status: todo
repo: agents-matrix-connector
value: agent runs per room and replies are stored so a restart never double-posts
files: [src/agents_matrix_connector/db/runs.py, tests/test_runs_repo.py]
verify: "uv run --frozen pytest tests/test_runs_repo.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [directory-repository]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# runs and outbound repo

## Requirement

The runs and outbound repository of the bot worker (design D8, D9, D10). Paths are in code/agents-matrix-connector.

`src/agents_matrix_connector/db/runs.py`:

- `PgRunStore(pool)`: implements the `RunStore` protocol of the pinned agents-common `agents_common.runs` (its session-id, message-id and finish methods, as renamed by orchestrator-rename-sessions), each a status-guarded update on an `in-progress` run.
- `create_run(conn, *, room_id, preset_id, kind) -> RunRef` (`kind` `first` or `follow`): inserts `in-progress` and sets `slug = "mx-<id>"`; returns the agents-common `RunRef`.
- `latest_session(conn, room_id) -> tuple[int, uuid.UUID] | None`: the newest run of the room that has a `session_id`.
- `in_progress(conn) -> list[RunRow]`; `count_first_in_progress(conn) -> int`.
- `finish(conn, run_id, status, reason=None) -> bool` (guarded `in-progress -> handled|failed`).
- Outbound: `add_outbound(conn, *, room_id, run_id, kind, chunks: Sequence[str]) -> list[int]` with `txn_id` `mxc-<run_id>-<n>` (n from 1) for `reply` and `mxc-<run_id>-notice` for `notice`, idempotent on `txn_id`; `pending(conn) -> list[OutboundRow]` oldest first; `mark_sent(conn, outbound_id, event_id)` and `mark_failed(conn, outbound_id, reason)` (guarded from `pending`).
- `list_outbound(pool, room_id, *, limit, before_id=None)` for the API, and `prune(conn, older_than) -> int` deleting finished runs and sent or failed outbound rows older than the cutoff.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: PgRunStore satisfies the agents-common RunStore protocol and its writes only touch in-progress runs [evidence: test:tests/test_runs_repo.py::test_run_store_protocol_and_guards]
- AC2: create_run assigns slug mx-<id> and latest_session returns the newest run with a session [evidence: test:tests/test_runs_repo.py::test_create_run_and_latest_session]
- AC3: count_first_in_progress counts only first runs in progress [evidence: test:tests/test_runs_repo.py::test_count_first_in_progress]
- AC4: outbound rows get deterministic transaction ids, re-adding is idempotent, and sent and failed are guarded [evidence: test:tests/test_runs_repo.py::test_outbound_txn_ids_and_guards]
- AC5: prune removes only old finished runs and old sent or failed outbound rows [evidence: test:tests/test_runs_repo.py::test_prune]

## Files

- `src/agents_matrix_connector/db/runs.py`
- `tests/test_runs_repo.py`

## Interfaces

- `src/agents_matrix_connector/db/runs.py`: `PgRunStore`, `RunRow`, `OutboundRow`, `create_run`, `latest_session`, `in_progress`, `count_first_in_progress`, `finish`, `add_outbound`, `pending`, `mark_sent`, `mark_failed`, `list_outbound`, `prune`. Used by dispatch-worker, reply-tracker, api-rooms-and-users.
- Implements `agents_common.runs.RunStore` (contract `agents-common-lib`, session names per design D15).

## Expected outcome

The worker can create, adopt and finish runs idempotently, and replies are stored with transaction ids that make re-sending safe.

## Steps

- Red: `tests/test_runs_repo.py` with the five tests on a migrated database. Fails on the missing module.
- Green: write the module. Run the verify (Docker).

## Notes

- Read the pinned `agents_common/runs.py` first; the protocol method names come from there, never guessed.
