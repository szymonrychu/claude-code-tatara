---
title: mxc read receipts
status: in-progress
repo: agents-matrix-connector
value: allowed Messenger messages show as seen once the agent has them
files: [src/agents_matrix_connector/matrix.py, src/agents_matrix_connector/fake_homeserver.py, src/agents_matrix_connector/worker.py, tests/test_matrix_client.py, tests/test_worker.py, README.md, MEMORY.md]
verify: "uv run --frozen pytest -q tests/test_matrix_client.py tests/test_worker.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 6
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc read receipts

## Requirement

Send a Matrix read receipt when the connector hands messages to an agent (epic goals G1, G2). Paths are in code/agents-matrix-connector.

User request 2026-10-26, verbatim: 'Add read receipts'. User decision 2026-10-26: "On handoff": mark read once the message is delivered to the agent session, in the same step that starts the typing indicator; only in allowed chats.

- `src/agents_matrix_connector/matrix.py`: `MatrixClient.send_receipt(room_id: str, event_id: str) -> None` posts `POST /_matrix/client/v3/rooms/{roomId}/receipt/m.read/{eventId}` with body `{}`; path segments encoded through the existing `_path`; errors map through the existing `_error` like every other call; the token is never in an error or log.
- `src/agents_matrix_connector/fake_homeserver.py`: the receipt route, recording `(room_id, receipt_type, event_id)`; an accessor `receipts(room_id) -> list[str]` (event ids in order); unknown room answers as the other room routes do.
- `src/agents_matrix_connector/worker.py`: `_delivered(batch)` (reached after both `_dispatch` and `_deliver`) also sends one `m.read` receipt for the newest event of the batch (the row with the greatest `origin_ts`, falling back to the greatest `id`), best-effort: a `MatrixError` is logged as a warning (room id and status only) and never fails the run or skips the typing call. Rows that never reach `_delivered` (ignored, failed, session gone, orchestrator refused) get no receipt.
- Tests: `tests/test_matrix_client.py::test_send_receipt` (method, encoded path, empty JSON body, a 403 maps to MatrixForbidden without the token in the message); `tests/test_worker.py::test_handoff_sends_read_receipt` (first dispatch and delivery into a running session each mark the newest event of their batch read, exactly once, and typing still runs); `tests/test_worker.py::test_receipt_failure_does_not_fail_run` (the fake homeserver rejects the receipt; the run still proceeds and typing is still sent); `tests/test_worker.py::test_no_receipt_without_handoff` (a refused dispatch and an ignored row send no receipt).
- `README.md`: the Operations section says the bot marks a message read when it hands it to the agent, and never in chats it does not route. `MEMORY.md`: a dated line with the user decision and why receipts sit next to typing.

## Acceptance conditions

- AC1: send_receipt posts an empty m.read receipt to the encoded path and maps errors without the token [evidence: test:tests/test_matrix_client.py::test_send_receipt]
- AC2: dispatch and delivery each mark the newest event of the batch read once, next to typing [evidence: test:tests/test_worker.py::test_handoff_sends_read_receipt]
- AC3: a failing receipt never fails the run nor skips typing [evidence: test:tests/test_worker.py::test_receipt_failure_does_not_fail_run]
- AC4: messages that are never handed off get no receipt [evidence: test:tests/test_worker.py::test_no_receipt_without_handoff]
- AC5: README and MEMORY record the behaviour, and lint passes [evidence: command:grep -qi "read receipt\|marks .* read" README.md && grep -q "2026-10-26" MEMORY.md && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_matrix_connector/matrix.py`
- `src/agents_matrix_connector/fake_homeserver.py`
- `src/agents_matrix_connector/worker.py`
- `tests/test_matrix_client.py`
- `tests/test_worker.py`
- `README.md`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
