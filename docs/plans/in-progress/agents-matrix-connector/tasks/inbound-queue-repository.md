---
title: inbound queue repository
status: in-progress
repo: agents-matrix-connector
value: "incoming chat messages queue per room in order, are batched, and can be put back without loss"
files: [src/agents_matrix_connector/db/inbound.py, tests/test_inbound_repo.py]
verify: "uv run --frozen pytest tests/test_inbound_repo.py -q && uv run ruff check . && uv run ruff format --check ."
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

# inbound queue repository

## Requirement

The inbound message queue repository (design D7, D8, D10). Rows are inserted by the bot's sync loop and change status only through guarded transitions (`agents_common.db.queue.transition` / `claim` or equivalent `UPDATE ... WHERE status = <expected>`). Paths are in code/agents-matrix-connector.

`src/agents_matrix_connector/db/inbound.py`:

- `InboundRow` dataclass (all columns).
- `insert(conn, *, event_id, room_id, sender, sender_name, body, mentioned, origin_ts, status, reason) -> bool`: `ON CONFLICT (event_id) DO NOTHING`; True when inserted. `status` is `new` or `ignored`.
- `count_new(conn, room_id) -> int`.
- `rooms_ready(conn) -> list[str]`: rooms with `new` rows and no `runs` row `in-progress`, ordered by their oldest `new` id.
- `claim_room(conn, room_id, run_id) -> list[InboundRow]`: every `new` row of the room, oldest first, guarded `new -> in-progress`, `run_id` set.
- `finish_run_rows(conn, run_id, status, reason=None) -> int`: guarded `in-progress -> handled|failed`.
- `requeue_run_rows(conn, run_id) -> int`: guarded `in-progress -> new`, `run_id` cleared (rows keep their ids, so FIFO order holds).
- `ignore_new(conn, room_id, reason) -> int`: guarded `new -> ignored`.
- `list_messages(pool, *, room_id=None, status=None, limit=50, before_id=None) -> list[InboundRow]` newest first.
- `prune(conn, older_than: datetime) -> int`: deletes rows received before the cutoff whose status is `handled`, `ignored` or `failed`.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: insert is idempotent per event id [evidence: test:tests/test_inbound_repo.py::test_insert_idempotent]
- AC2: rooms_ready skips rooms with a run in progress and orders rooms by their oldest new row [evidence: test:tests/test_inbound_repo.py::test_rooms_ready]
- AC3: claim_room moves every new row of the room to in-progress oldest first and leaves other rooms untouched [evidence: test:tests/test_inbound_repo.py::test_claim_room]
- AC4: finish, requeue and ignore only move rows in the expected status [evidence: test:tests/test_inbound_repo.py::test_guarded_transitions]
- AC5: list_messages filters and pages newest first, and prune deletes only old finished rows [evidence: test:tests/test_inbound_repo.py::test_list_and_prune]

## Files

- `src/agents_matrix_connector/db/inbound.py`
- `tests/test_inbound_repo.py`

## Interfaces

- `src/agents_matrix_connector/db/inbound.py`: `InboundRow`, `insert`, `count_new`, `rooms_ready`, `claim_room`, `finish_run_rows`, `requeue_run_rows`, `ignore_new`, `list_messages`, `prune`. Used by matrix-sync-loop (insert, count_new), dispatch-worker, reply-tracker, api routes.

## Expected outcome

A burst of messages in one room is claimed as one batch; a failed delivery puts the batch back in place.

## Steps

- Red: `tests/test_inbound_repo.py` with the five tests on a migrated database (insert `runs` rows with SQL where needed). Fails on the missing module.
- Green: write the module. Run the verify (Docker).

## Notes

- Read `code/agents-common/src/agents_common/db/queue.py` first and use `transition` / `claim` where their shape fits; a batch claim by room may need its own guarded `UPDATE ... WHERE room_id = %s AND status = 'new' RETURNING *`.
