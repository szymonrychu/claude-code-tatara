---
title: terminal websocket api
status: in-progress
repo: claude-code-wrapper
value: clients get interactive shells on an agent pod over an authenticated WebSocket
files: [src/claude_code_wrapper/api/terminals.py, src/claude_code_wrapper/api/auth.py, src/claude_code_wrapper/api/app.py, README.md, tests/test_api_terminals.py, tests/test_api_auth.py, tests/test_readme_api.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py tests/test_api_auth.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [terminal-registry]
owns: [wrapper-terminals-api]
uses: [terminal-registry]
model: opus
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# terminal websocket api

## Requirement

Expose the terminal registry over HTTP and a WebSocket (design D2, D3), test-first, and make bearer auth work on WebSocket routes.

- `api/auth.py:require_auth` takes `starlette.requests.HTTPConnection` instead of `Request`, so the same dependency guards HTTP and WebSocket routes; a WebSocket upgrade without a valid bearer is denied before accept (HTTP 401 denial response with the `unauthorized` envelope).
- New `src/claude_code_wrapper/api/terminals.py`, registered in `api/app.py` under the `/v1` router:
  - `POST /v1/sessions/{id}/terminals` body `{"rows"?: int, "cols"?: int}` (extra keys rejected) -> 201 terminal object `{terminal_id, session_id, created_at, alive, exit_code, attached, rows, cols}`; 409 `terminal_limit` at the cap, 404 `not_found` for an unknown session.
  - `GET /v1/sessions/{id}/terminals` -> 200 `{"terminals": [...]}`.
  - `DELETE /v1/sessions/{id}/terminals/{terminal_id}` -> 204; 404 `terminal_not_found` when unknown.
  - `WS /v1/sessions/{id}/terminals/{terminal_id}/attach`: unknown session or terminal is denied before accept with 404. After accept: the scrollback snapshot as binary frames, then live PTY output as binary frames; client binary frames are written to the PTY; client text frames are JSON control: `{"type":"resize","cols","rows"}` resizes, `{"type":"ping"}` answers `{"type":"pong"}`, anything else closes 1003. A frame over `limits.terminal_max_frame_bytes` closes 1009. A subscriber dropped for overflow closes 1013. Shell exit sends `{"type":"exit","code":N}` then closes 1000. Closing the socket detaches (the shell keeps running).
- README (`## API reference`): a `###` section per HTTP route and one hand-written `### \`WS /v1/sessions/{id}/terminals/{terminal_id}/attach\`` section with the frame protocol and close codes; `## Errors` rows for `terminal_limit`, `terminal_not_found`, `session_not_active` (409) and `invalid_size` (422); `## Trust model` note that terminals are interactive login shells of the agent uid with every secret-kind Claude variable and the `CCW_*` tokens removed from their environment.
- `tests/test_readme_api.py` gains a check that every WebSocket route of the app (`APIWebSocketRoute`) has a README `### \`WS <path>\`` heading, since `_walk` sees only `APIRoute`.
- `terminal_id` path parameters (DELETE and the WebSocket attach) are accepted only in the registry's id format, `TERMINAL_ID_RE = ^term_[0-9a-f]{12}$`, defined once in `api/terminals.py` next to the id generator's format; anything else is 422 `invalid_request` (the WebSocket is denied before accept with the same 422), so a crafted id never reaches the registry or a path (interrogate ruling 4).

## Acceptance conditions

- AC1: a WebSocket upgrade without a valid bearer is denied with 401 before accept, and HTTP auth behaves as before [evidence: test:tests/test_api_auth.py::test_websocket_requires_bearer]
- AC2: create, list and delete follow the documented statuses and bodies, with terminal_limit at the cap and terminal_not_found on unknown ids [evidence: test:tests/test_api_terminals.py::test_http_lifecycle]
- AC3: attach replays scrollback, streams output and writes input bytes to the shell [evidence: test:tests/test_api_terminals.py::test_attach_round_trip]
- AC4: resize and ping control frames work and an unknown control closes 1003 [evidence: test:tests/test_api_terminals.py::test_control_frames]
- AC5: an oversized frame closes 1009 and shell exit sends the exit frame then closes 1000 [evidence: test:tests/test_api_terminals.py::test_frame_cap_and_exit]
- AC6: detach leaves the shell alive and a second attach replays what was printed meanwhile [evidence: test:tests/test_api_terminals.py::test_reattach_replays]
- AC7: every WebSocket route is documented in the README [evidence: test:tests/test_readme_api.py::test_every_websocket_route_documented]
- AC8: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py tests/test_api_auth.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .]
- AC9: attaching to an exited shell replays the scrollback, sends the exit frame and closes 1000 [evidence: test:tests/test_api_terminals.py::test_attach_exited_replays_and_closes]
- AC10: create with rows or cols outside 1..1000 answers 422 invalid_size [evidence: test:tests/test_api_terminals.py::test_create_invalid_size]
- AC11: a resize frame out of range or malformed is ignored and the socket stays open [evidence: test:tests/test_api_terminals.py::test_bad_resize_ignored]
- AC12: create or attach on a known but not active session answers 409 session_not_active and an unknown session 404 [evidence: test:tests/test_api_terminals.py::test_session_not_active_vs_unknown]
- AC13: a terminal_id outside ^term_[0-9a-f]{12}$ (for example ..%2F, term_zz, an uppercase or overlong id) is 422 invalid_request on DELETE and denied with 422 before accept on the WebSocket [evidence: test:tests/test_api_terminals.py::test_invalid_terminal_id_rejected]
- AC14: the README Errors table lists session_not_active and invalid_size and the README tests stay green [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_readme_api.py]

## Files

- `src/claude_code_wrapper/api/terminals.py`
- `src/claude_code_wrapper/api/auth.py`
- `src/claude_code_wrapper/api/app.py`
- `README.md`
- `tests/test_api_terminals.py`
- `tests/test_api_auth.py`
- `tests/test_readme_api.py`

## Interfaces

- `claude_code_wrapper.api.auth.require_auth(conn: HTTPConnection) -> None`.
- Routes above (owns part `wrapper-terminals-api`, cross-repo contract `wrapper-terminals-api`, consumed by agent-orchestrator tasks terminal-proxy-routes and terminal-ws-relay): body fields, frame protocol and close codes are the contract.
- Uses `TerminalRegistry` (part `terminal-registry`).

## Expected outcome

A client with the bearer token can create a shell in a session workdir, attach over WebSocket, type, resize, detach and reattach with scrollback, and delete it; every route is in the README.

## Steps

- Write `tests/test_api_auth.py::test_websocket_requires_bearer` and `tests/test_api_terminals.py` (Starlette `TestClient.websocket_connect`, a real registry over `tmp_path` and `/bin/sh`), and `tests/test_readme_api.py::test_every_websocket_route_documented`; run `uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py tests/test_api_auth.py tests/test_readme_api.py`: new tests fail.
- Retype `require_auth`, add `api/terminals.py` and register it; write the README sections; rerun: passes.
- `uv run ruff check . && uv run ruff format --check .`: clean.

## Notes

- Probe result from discovery: with `Request` typing, a WebSocket route under `v1` fails with `TypeError: require_auth() missing ... 'request'`; `HTTPConnection` works for both, and an `ApiError` raised during the handshake becomes a denial response.
- HTTP exception handlers do not apply inside an accepted WebSocket: errors there are close codes or the JSON control frames above.
- Run the send loop (queue to socket) and the receive loop (socket to PTY) as two tasks; when either ends, cancel the other and detach, so no task leaks per connection.
- `tests/test_manager.py::test_shutdown_stops_all` fails only in this container; never a verify target.
- Builder check ruling 1: Attaching to an exited shell replays the scrollback, sends the exit control frame, then closes 1000. The panel reopens tabs on mount only for alive shells from listTerminals.
- Builder check ruling 3: Rows or cols outside 1..1000 on create answer 422 with code invalid_size (wrapper, passed through by the orchestrator); a resize control frame out of range or malformed is ignored and logged, the socket stays open.
- Builder check ruling 5: Terminals exist only for an active session; create or attach on a known but not active session answers 409 session_not_active; 404 only for an unknown session. Stopping or destroying a session closes its shells.

- 2026-10-23 amended: builder check rulings 1,3,5 add acceptance conditions AC9-AC12

- 2026-10-23 amended: interrogate rulings 4 (terminal_id format check in the wrapper routes), 5 (README Errors rows session_not_active and invalid_size), 1 (Trust model wording follows the new env contract)
