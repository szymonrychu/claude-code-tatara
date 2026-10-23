---
title: terminal ws relay
status: todo
repo: agent-orchestrator
value: a browser or headless client gets a live shell on an agent pod without ever seeing the wrapper token
files: [src/agent_orchestrator/api/workspace.py, pyproject.toml, uv.lock, tests/test_terminal_relay.py, README.md]
verify: "uv run pytest -q -p no:cacheprovider tests/test_terminal_relay.py tests/test_api_terminals.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [terminal-proxy-routes]
owns: [orch-terminal-ws]
uses: [workspace-proxy-module, origin-allowlist, fake-wrapper-terminals, wrapper-terminals-api]
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

# terminal ws relay

## Requirement

Relay terminal WebSockets from browsers and headless clients to the wrapper (design D2, D5, D6), test-first.

- `WS /api/v1/agents/{agent_id}/terminals/{terminal_id}/attach` in `src/agent_orchestrator/api/workspace.py`: the Origin middleware (part `origin-allowlist`) has already refused unlisted origins with 1008 before accept. The route accepts the client socket, resolves the agent with `resolve_agent`, and opens a client connection to `ws://<agent url host:port>/v1/sessions/{session_id}/terminals/{terminal_id}/attach` with `Authorization: Bearer <derived token>` using `websockets`. Failures close the client socket with: 4404 for an unknown agent or a wrapper 404 (unknown session or terminal), 4409 for an agent that is not ready, 1011 for an unreachable wrapper, a wrapper 401 or any other upstream failure.
- After both sides are open: binary frames and text frames are relayed unchanged in both directions; when either side closes, the other side is closed with the same code (1000, 1003, 1009, 1013 from the wrapper pass through), and both relay tasks end. No buffering beyond the `websockets` defaults; a relay never outlives its connections.
- `websockets` becomes a declared dependency in `pyproject.toml` (`websockets>=17.3`) and `uv.lock` is updated (`uv lock`).
- README: a hand-written `### \`WS /api/v1/agents/{agent_id}/terminals/{terminal_id}/attach\`` section with the frame protocol (binary PTY bytes; JSON `resize`, `ping`/`pong`, `exit`), the replay on attach, the close codes, the Origin rule and a headless example (Python `websockets` client), since WebSocket routes are not in OpenAPI.

## Acceptance conditions

- AC1: bytes typed into the api socket reach the fake wrapper shell and its output and replay come back unchanged [evidence: test:tests/test_terminal_relay.py::test_relay_round_trip]
- AC2: resize and ping control frames are relayed and pong comes back [evidence: test:tests/test_terminal_relay.py::test_control_frames_relayed]
- AC3: the relay sends the derived bearer token to the wrapper [evidence: test:tests/test_terminal_relay.py::test_bearer_sent_upstream]
- AC4: an unlisted Origin is refused before any wrapper connection is opened [evidence: test:tests/test_terminal_relay.py::test_origin_refused_before_upstream]
- AC5: unknown agent, unknown terminal, agent not ready and unreachable wrapper close with the documented codes [evidence: test:tests/test_terminal_relay.py::test_failure_close_codes]
- AC6: a close on either side closes the other with the same code and leaves no relay task running [evidence: test:tests/test_terminal_relay.py::test_close_propagates_without_leak]
- AC7: websockets is a declared dependency and the lock is current [evidence: command:uv lock --check]
- AC8: the WebSocket route is documented in the README [evidence: command:grep -qF 'WS /api/v1/agents/{agent_id}/terminals/{terminal_id}/attach' README.md]
- AC9: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_terminal_relay.py tests/test_api_terminals.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/api/workspace.py`
- `pyproject.toml`
- `uv.lock`
- `tests/test_terminal_relay.py`
- `README.md`

## Interfaces

- `WS /api/v1/agents/{agent_id}/terminals/{terminal_id}/attach` (owns part `orch-terminal-ws`, consumed by fe-terminal-socket and kind-e2e-workspace).
- Uses `workspace-proxy-module`, `origin-allowlist`, `fake-wrapper-terminals` and the wrapper contract `wrapper-terminals-api`.

## Expected outcome

A browser on an allowed origin, or a headless client with no Origin, gets an interactive shell on any agent pod through the api, with the wrapper token never leaving the api.

## Steps

- Write `tests/test_terminal_relay.py`: serve `create_app(...)` with uvicorn on 127.0.0.1:0 inside the test loop (same pattern as `FakeWrapper.start`), register a FakeWrapper agent in the DB, connect with `websockets.asyncio.client.connect` (with and without an `origin`); run `uv run pytest -q -p no:cacheprovider tests/test_terminal_relay.py`: fails.
- Implement the relay and declare the dependency (`uv add 'websockets>=17.3'` or edit plus `uv lock`); rerun: passes.
- README section; run the verify command: passes.

## Notes

- Do not use Starlette `TestClient` for these tests: it runs the app on its own loop, which conflicts with the async psycopg pool fixture; `httpx.ASGITransport` cannot do WebSockets at all (fix-as-ac from the reuse map).
- Only the Origin refusal happens before accept (middleware, 1008, seen by the client as HTTP 403); every other failure is a close after accept with the codes in the requirement, documented in the README.
- `websockets` 17 asyncio client: `from websockets.asyncio.client import connect`; pass headers with `additional_headers=`.
- A ping every 20 s comes from the browser and is relayed like any text frame; the api adds no pings of its own.
- Opus task: two concurrent pumps with cancellation on either close; make sure `asyncio.TaskGroup` or explicit cancel-and-await leaves nothing running.
