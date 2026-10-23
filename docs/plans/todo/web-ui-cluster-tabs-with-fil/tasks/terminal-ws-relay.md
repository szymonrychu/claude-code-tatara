---
title: terminal ws relay
status: todo
repo: agent-orchestrator
value: a browser or headless client gets a live shell on an agent pod without ever seeing the wrapper token
files: [src/agent_orchestrator/api/workspace.py, pyproject.toml, uv.lock, tests/test_terminal_relay.py, README.md]
verify: "uv run pytest -q -p no:cacheprovider tests/test_terminal_relay.py tests/test_api_terminals.py tests/test_readme_api.py && mise run lint"
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
- AC9: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_terminal_relay.py tests/test_api_terminals.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agent_orchestrator/api/workspace.py`
- `pyproject.toml`
- `uv.lock`
- `tests/test_terminal_relay.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
