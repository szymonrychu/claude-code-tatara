---
title: mxc matrix send event
status: done
repo: agents-matrix-connector
value: "the bot can send any Matrix event type, which quoted replies and reactions need"
files: [src/agents_matrix_connector/matrix.py, tests/test_matrix_client.py]
verify: "uv run pytest tests/test_matrix_client.py && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: 1153021ade112e9725cba092b91a8fc82e2b493a
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: 2
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc matrix send event

## Requirement

README Goal, verbatim: "An agent can reply to a specific chat message (quoted reply) and react to a message with an emoji."

Design D8, verbatim: "Reply: `m.room.message` `{msgtype: m.text, body, "m.relates_to": {"m.in_reply_to": {"event_id": E}}}` on the first chunk only, with no fallback body (fallbacks are best effort since MSC3676; removal proposed in MSC2781). Reaction: `m.reaction` `{"m.relates_to": {"rel_type": "m.annotation", "event_id": E, "key": <emoji>}}`. `MatrixClient.send_event(room_id, event_type, txn_id, content)` is the one PUT; `send_text` becomes a call of it."

Interrogate verdict Act on 5 (tracker test spy) moved `tests/test_tracker.py` into mxc-bot-sends-delivery; to keep that task within 8 files, the `MatrixClient.send_event` part of it is this task (planner, 2026-10-27).

Scope (agents-matrix-connector): `matrix.py` (`MatrixClient.send_event`; `send_text` calls it), `tests/test_matrix_client.py`. The callers (`Tracker._send_pending`, the sender) are mxc-bot-sends-delivery.

## Acceptance conditions

- ac1: `MatrixClient.send_event` PUTs the given event type, txn id and content and returns the event id, and `send_text` sends the same request it sent before through it [evidence: test:tests/test_matrix_client.py::test_send_event_type_and_content]
- ac2: send_event maps homeserver errors to the existing MatrixError taxonomy (MatrixUnavailable, MatrixAuthError, MatrixForbidden, MatrixNotFound) exactly as send_text did [evidence: test:tests/test_matrix_client.py::test_send_event_errors]
- ac3: the existing Matrix client tests pass unchanged [evidence: command:uv run pytest tests/test_matrix_client.py -k "not send_event"]
- ac4: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_matrix_client.py && mise run lint]

## Files

- `src/agents_matrix_connector/matrix.py`
- `tests/test_matrix_client.py`

## Interfaces

- `matrix.py:MatrixClient.send_event(room_id: str, event_type: str, txn_id: str, content: dict) -> str`: `PUT /_matrix/client/v3/rooms/{room_id}/send/{event_type}/{txn_id}` through `_request`, returning the event id.
- `send_text(room_id, txn_id, body)` calls `send_event(room_id, "m.room.message", txn_id, {"msgtype": "m.text", "body": body})`; its signature and callers are unchanged.

## Expected outcome

The bot has one PUT for every event type, so quoted replies and reactions can be sent with the same error handling and txn-id dedup as replies today.

## Steps

- Red: add `test_send_event_type_and_content` and `test_send_event_errors` to `tests/test_matrix_client.py`; run `uv run pytest tests/test_matrix_client.py`: they fail (no method).
- Green: `send_event`, `send_text` through it; run the task's verify: passes. Quote the summary line with counts.

## Notes

- Reuse `MatrixClient._request` and its error taxonomy; build the path with `_path("rooms", room_id, "send", event_type, txn_id)` as `send_text` does today.
- `tests/test_matrix_client.py` runs locally (no DB).

- 2026-10-28 done

- 2026-10-28 actuals: no agent records
