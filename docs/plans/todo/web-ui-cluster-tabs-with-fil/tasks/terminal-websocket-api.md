---
title: terminal websocket api
status: todo
repo: claude-code-wrapper
value: clients get interactive shells on an agent pod over an authenticated WebSocket
files: [src/claude_code_wrapper/api/terminals.py, src/claude_code_wrapper/api/auth.py, src/claude_code_wrapper/api/app.py, README.md, tests/test_api_terminals.py, tests/test_api_auth.py, tests/test_readme_api.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py tests/test_api_auth.py tests/test_readme_api.py && mise run lint"
depends_on: [terminal-registry]
owns: [wrapper-terminals-api]
uses: [terminal-registry]
model: opus
estimate: 44
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
- README (`## API reference`): a `###` section per HTTP route and one hand-written `### \`WS /v1/sessions/{id}/terminals/{terminal_id}/attach\`` section with the frame protocol and close codes; `## Errors` rows for `terminal_limit` and `terminal_not_found`; `## Trust model` note that terminals are interactive login shells of the agent uid with the listed secrets removed from their environment.
- `tests/test_readme_api.py` gains a check that every WebSocket route of the app (`APIWebSocketRoute`) has a README `### \`WS <path>\`` heading, since `_walk` sees only `APIRoute`.

## Acceptance conditions

- AC1: a WebSocket upgrade without a valid bearer is denied with 401 before accept, and HTTP auth behaves as before [evidence: test:tests/test_api_auth.py::test_websocket_requires_bearer]
- AC2: create, list and delete follow the documented statuses and bodies, with terminal_limit at the cap and terminal_not_found on unknown ids [evidence: test:tests/test_api_terminals.py::test_http_lifecycle]
- AC3: attach replays scrollback, streams output and writes input bytes to the shell [evidence: test:tests/test_api_terminals.py::test_attach_round_trip]
- AC4: resize and ping control frames work and an unknown control closes 1003 [evidence: test:tests/test_api_terminals.py::test_control_frames]
- AC5: an oversized frame closes 1009 and shell exit sends the exit frame then closes 1000 [evidence: test:tests/test_api_terminals.py::test_frame_cap_and_exit]
- AC6: detach leaves the shell alive and a second attach replays what was printed meanwhile [evidence: test:tests/test_api_terminals.py::test_reattach_replays]
- AC7: every WebSocket route is documented in the README [evidence: test:tests/test_readme_api.py::test_every_websocket_route_documented]
- AC8: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py tests/test_api_auth.py tests/test_readme_api.py && mise run lint]

## Files

- `src/claude_code_wrapper/api/terminals.py`
- `src/claude_code_wrapper/api/auth.py`
- `src/claude_code_wrapper/api/app.py`
- `README.md`
- `tests/test_api_terminals.py`
- `tests/test_api_auth.py`
- `tests/test_readme_api.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
