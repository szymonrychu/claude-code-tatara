---
title: mxc matrix send event
status: todo
repo: agents-matrix-connector
value: "the bot can send any Matrix event type, which quoted replies and reactions need"
files: [src/agents_matrix_connector/matrix.py, tests/test_matrix_client.py]
verify: "uv run pytest tests/test_matrix_client.py && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: ""
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
