---
title: matrix client and fake hs
status: todo
repo: agents-matrix-connector
value: "the connector talks to Synapse as a bot user, and every Matrix path is testable against an in-memory homeserver"
files: [src/agents_matrix_connector/matrix.py, src/agents_matrix_connector/fake_homeserver.py, tests/test_matrix_client.py]
verify: "uv run --frozen pytest tests/test_matrix_client.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-scaffold-and-cli]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 14
expected_tokens: 1883475
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# matrix client and fake hs

## Requirement

A thin async Matrix client-server API client and an in-memory fake homeserver for tests (design D2, D14; contract `matrix-client`). Paths are in code/agents-matrix-connector.

`src/agents_matrix_connector/matrix.py`:

- `MatrixClient(base_url: str, access_token: str, *, timeout: float = 15, transport: httpx.AsyncBaseTransport | None = None)`, async context manager, `aclose()`; `Authorization: Bearer <token>`; every path segment percent-encoded (room ids contain `!` and `:`).
- `whoami() -> str` (`GET /_matrix/client/v3/account/whoami`); `create_filter(user_id, definition: dict) -> str` (`POST /user/{id}/filter`); `sync(since: str | None, timeout_ms: int, filter_id: str | None, full_state: bool = False) -> dict` (`GET /sync`, HTTP timeout `timeout_ms / 1000 + 10`); `join(room_id) -> str` (`POST /join/{id}`); `room_state(room_id) -> list[dict]` (`GET /rooms/{id}/state`); `joined_members(room_id) -> dict[str, str | None]` (user id to display name, `GET /rooms/{id}/joined_members`); `send_text(room_id, txn_id, body) -> str` (`PUT /rooms/{id}/send/m.room.message/{txn_id}`, content `{"msgtype": "m.text", "body": body}`, returns `event_id`); `typing(user_id, room_id, typing: bool, timeout_ms: int = 30000)` (`PUT /rooms/{id}/typing/{user_id}`).
- Errors: `MatrixError(status, errcode, error)` base; `MatrixAuthError` (401, or errcode `M_UNKNOWN_TOKEN` / `M_MISSING_TOKEN`); `MatrixForbidden` (403); `MatrixNotFound` (404); `MatrixUnavailable` (transport error, 5xx, and 429 `M_LIMIT_EXCEEDED` after one retry that sleeps `retry_after_ms`, capped at 10 s). The access token is never part of an exception message, a log record or a `repr()`.

`src/agents_matrix_connector/fake_homeserver.py`:

- `FakeHomeserver(user_id: str, token: str)` exposing `app` (an ASGI app) that implements exactly the routes above with Matrix-shaped JSON and errors (`{"errcode", "error"}`), checks the bearer token (401 `M_UNKNOWN_TOKEN` otherwise) and keeps state in memory: rooms (state events, members with membership and display names, timeline), the bot's invites, monotonically increasing batch tokens, sent messages, typing state, filters.
- `/sync` returns `rooms.invite`, `rooms.join` (state and timeline since the given batch; `full_state` or no `since` returns the whole state) and `rooms.leave` in the Matrix v3 shape, and `next_batch`; with nothing new it waits up to `timeout` for a new event (an `asyncio.Event`), then returns an empty response.
- Helpers: `add_room(room_id, state: list[dict], members: dict[str, str], *, join_rule="invite")`, `invite(room_id, inviter)`, `post(room_id, sender, content) -> event_id`, `set_state(room_id, event_type, state_key, content)`, `set_member(room_id, user_id, membership, display_name=None)`, `encrypt(room_id)`, `sent(room_id) -> list[dict]` (contents sent by the bot), `typing_state(room_id) -> bool`, `fail_next(route: str, status: int, errcode: str | None = None, retry_after_ms: int | None = None)`, `revoke_token()`.
- Join of a room the bot is invited to succeeds; join of an invite-only room without an invite answers 403 `M_FORBIDDEN`. A repeated `txn_id` from the same token returns the first `event_id` and stores no second message (Synapse behaviour, design D9).

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: whoami, create_filter, join, room_state, joined_members, send_text and typing hit the right method and percent-encoded path and parse the answer [evidence: test:tests/test_matrix_client.py::test_calls_and_paths]
- AC2: sync returns invites, joined state and timeline since a batch, and a long poll wakes when a message is posted [evidence: test:tests/test_matrix_client.py::test_sync_shape_and_long_poll]
- AC3: 401, 403, 404, other 4xx, 5xx and transport errors map to the five error classes [evidence: test:tests/test_matrix_client.py::test_error_mapping]
- AC4: a 429 is retried once after retry_after_ms, a second 429 raises MatrixUnavailable [evidence: test:tests/test_matrix_client.py::test_rate_limit_retry_once]
- AC5: a repeated transaction id posts one message and returns the same event id [evidence: test:tests/test_matrix_client.py::test_txn_id_dedupe]
- AC6: joining an invite-only room without an invite is MatrixForbidden [evidence: test:tests/test_matrix_client.py::test_join_needs_invite]
- AC7: the access token appears in no exception message or repr [evidence: test:tests/test_matrix_client.py::test_token_redacted]

## Files

- `src/agents_matrix_connector/matrix.py`
- `src/agents_matrix_connector/fake_homeserver.py`
- `tests/test_matrix_client.py`

## Interfaces

- `src/agents_matrix_connector/matrix.py`: `MatrixClient`, `MatrixError`, `MatrixAuthError`, `MatrixForbidden`, `MatrixNotFound`, `MatrixUnavailable` (contract `matrix-client`; used by matrix-sync-loop, dispatch-worker, reply-tracker, mxc-service-entrypoints).
- `src/agents_matrix_connector/fake_homeserver.py`: `FakeHomeserver` and helpers (used by every Matrix-facing test and by mxc-e2e-api, served by uvicorn there).

## Expected outcome

`MatrixClient(..., transport=httpx.ASGITransport(fake.app))` drives the fake through invites, joins, syncs and sends exactly as the live Synapse would for these eight calls.

## Steps

- Red: `tests/test_matrix_client.py` with the seven tests; fails on the missing modules.
- Green: write `matrix.py`, then `fake_homeserver.py` (FastAPI or Starlette, already installed with fastapi). Run the verify.

## Notes

- Matrix v3 client-server shapes: `/sync` body `{"next_batch", "rooms": {"join": {id: {"state": {"events": []}, "timeline": {"events": [], "limited": false}}}, "invite": {id: {"invite_state": {"events": []}}}, "leave": {}}}`.
- Hermes' `roomadmin.py` (ConfigMap `ai/hermes-agent-files`, key `scripts__hermes-rooms__roomadmin.py`) uses the same endpoints with urllib against the live Synapse; read it with `kubectl -n ai get cm hermes-agent-files -o go-template='{{index .data "scripts__hermes-rooms__roomadmin.py"}}'` for shapes (read-only).
- Keep the fake deterministic: no wall-clock sleeps except the long-poll wait bounded by the request timeout.
