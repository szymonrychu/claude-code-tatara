---
title: sync limited timeline backfill
status: done
repo: agents-matrix-connector
value: no message is lost when a sync timeline arrives limited after downtime
files: [src/agents_matrix_connector/matrix.py, src/agents_matrix_connector/fake_homeserver.py, src/agents_matrix_connector/sync.py, src/agents_matrix_connector/settings.py, tests/test_sync.py, tests/test_matrix_client.py, README.md]
verify: "uv run --frozen pytest tests/test_sync.py tests/test_matrix_client.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [matrix-sync-loop]
model: opus
review: ""
verified_head: 3a439783a14591b9ec93cae49b255f616ebbc371
points: 3
expected_minutes: 6
expected_tokens: 849076
points_actual: 3
actual_minutes: 7
actual_tokens: 1427934
actual_roles: "impl 6, review 1"
actual_role_tokens: "impl 1260451, review 167483"
---

# sync limited timeline backfill

## Requirement

Discovered in task matrix-sync-loop (2026-10-25): a joined room's `/sync` timeline arrives `limited: true` when more events happened since the last sync than the filter's timeline limit (for example after the bot was down), and the dropped events are never processed, which breaks goal G4 ("no message is lost ... across restarts"). Paths are in code/agents-matrix-connector.

- `src/agents_matrix_connector/matrix.py`: `MatrixClient.room_messages(room_id, from_token, *, direction="b", limit=100, filter=None) -> dict` over `GET /_matrix/client/v3/rooms/{roomId}/messages` (same auth, error mapping, token redaction and 429 handling as the existing calls).
- `src/agents_matrix_connector/fake_homeserver.py`: the `/messages` route, paging a room's stored timeline backwards from a token, plus a way for tests to make a sync timeline `limited` with a `prev_batch`.
- `src/agents_matrix_connector/sync.py`: for each joined room whose timeline is `limited` in an incremental sync (never on the first sync after an empty database, D5 no-replay), page backwards from `prev_batch` until an event already recorded in `inbound` (by `event_id`) or the bot's own join event is reached, or `MATRIX_BACKFILL_MAX_EVENTS` (default 500, setting in settings.py) events were read; process the recovered `m.room.message` events oldest first through the same intake path as live events (same policy, loop guard, trigger and body rules), in the same transaction as that sync's `next_batch`. Hitting the cap logs a warning with the room id and the count, never message bodies.
- Tests in `tests/test_sync.py` and `tests/test_matrix_client.py`.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: `room_messages` calls `/rooms/{roomId}/messages` with `from`, `dir` and `limit`, maps errors and never exposes the token [evidence: test:tests/test_matrix_client.py::test_room_messages]
- AC2: a limited timeline is backfilled oldest first up to the last recorded event, and every recovered message goes through intake exactly once [evidence: test:tests/test_sync.py::test_limited_timeline_backfill]
- AC3: no backfill on the first sync after an empty database and none before the bot's own join [evidence: test:tests/test_sync.py::test_backfill_respects_no_replay]
- AC4: the backfill stops at MATRIX_BACKFILL_MAX_EVENTS and logs the room and count without bodies [evidence: test:tests/test_sync.py::test_backfill_cap]

## Files

- `src/agents_matrix_connector/matrix.py`
- `src/agents_matrix_connector/fake_homeserver.py`
- `src/agents_matrix_connector/sync.py`
- `src/agents_matrix_connector/settings.py`
- `tests/test_sync.py`
- `tests/test_matrix_client.py`
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

- 2026-10-25 done
