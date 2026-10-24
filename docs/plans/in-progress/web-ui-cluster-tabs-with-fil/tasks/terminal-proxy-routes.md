---
title: terminal proxy routes
status: done
repo: agent-orchestrator
value: "headless clients and the UI can create, list and delete shells on any agent through /api/v1"
files: [src/agent_orchestrator/api/workspace.py, src/agent_orchestrator/api/schemas.py, tests/test_api_terminals.py, tests/fakes/fake_wrapper.py, tests/test_fake_wrapper_contract.py, README.md, openapi.json, frontend/src/api/schema.d.ts]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py tests/test_api_files.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check ."
depends_on: [file-proxy-routes, terminal-websocket-api, origin-allowlist]
owns: [orch-terminals-api, fake-wrapper-terminals]
uses: [workspace-proxy-module, origin-allowlist, wrapper-terminals-api]
model: ""
estimate: 6
estimate_by: formula
actual: 13
actual_roles: "impl 8, verify 3, review 1, land 1"
review: ""
worktree: /home/user/claude-code-tatara/.claude/worktrees/web-ui-cluster-tabs-with-fil-terminal-proxy-routes/agent-orchestrator
branch: web-ui-cluster-tabs-with-fil-terminal-proxy-routes
verified_head: fbd686b83861ccc1c74ee3bfa203f13a5e8fbfd2
run: web-ui-cluster-tabs-with-fil
provides: [workspace-resolve-agents, fake-wrapper-terminal-controls]
acs_for_audit: []
process_gaps: []
fork_point: 4ce96df
---

# terminal proxy routes

## Requirement

Proxy the wrapper terminal lifecycle through the orchestrator api (design D4, D5; user Q4, Q5), test-first.

Routes in `src/agent_orchestrator/api/workspace.py`, models in `api/schemas.py`:

- `POST /api/v1/agents/{agent_id}/terminals` body `CreateTerminal` `{rows?, cols?}` (extra forbidden) -> 201 `TerminalView` `{agent_id, cluster_id, pod_name, terminal_id, created_at, alive, exit_code, attached, rows, cols}`; forwards to `POST /v1/sessions/{session_id}/terminals` on that agent; wrapper `terminal_limit` passes through as 409, `session_not_active` as 409 and `invalid_size` as 422.
- `GET /api/v1/clusters/{cluster_id}/terminals` -> 200 `TerminalList` `{terminals: [TerminalView], unavailable_agents: [agent_id]}`: queries every ready agent of the cluster concurrently (bounded by the shared client timeouts); an agent that fails is listed in `unavailable_agents` instead of failing the request.
- `DELETE /api/v1/agents/{agent_id}/terminals/{terminal_id}` -> 204; wrapper `terminal_not_found` passes through as 404. `terminal_id` is checked with `validate_terminal_id` (part `workspace-proxy-module`, `^term_[0-9a-f]{12}$`) before any upstream request: anything else is 422 `invalid_request` and the wrapper is never called.
- POST and DELETE depend on `require_allowed_origin` (part `origin-allowlist`): an unlisted Origin is 403 `forbidden_origin`.

FakeWrapper gains the terminal HTTP routes and a WebSocket attach route that emulates the wrapper protocol (replay buffer, echo of input bytes as output, resize and ping control, exit frame, close codes, bearer check), and `tests/test_fake_wrapper_contract.py` gains terminal cases (HTTP and WebSocket) against fake and real image under `-m integration`.

README: a `###` section per route; `terminal_limit` (409), `terminal_not_found` (404), `session_not_active` (409), `invalid_size` (422), `invalid_request` (422 for a malformed terminal id) and `forbidden_origin` usage in the error code list. Regenerate `openapi.json` and `frontend/src/api/schema.d.ts`.
- Token hygiene: the routes send the derived token only through the seam's helper as an `Authorization` header; a DEBUG `caplog` test over create, list and delete finds the token in no log record and no response body (interrogate ruling 7).
- The routes use the seam's lazily created shared client, so their tests run through `httpx.ASGITransport` without the lifespan (interrogate ruling 8).

## Acceptance conditions

- AC1: create forwards to the agent's session and returns TerminalView with agent and pod fields [evidence: test:tests/test_api_terminals.py::test_create_on_agent]
- AC2: the cluster list merges every ready agent's terminals and reports a failing agent in unavailable_agents [evidence: test:tests/test_api_terminals.py::test_cluster_list_fans_out]
- AC3: delete returns 204 and unknown terminals are 404 terminal_not_found [evidence: test:tests/test_api_terminals.py::test_delete]
- AC4: terminal_limit passes through as 409 [evidence: test:tests/test_api_terminals.py::test_limit_passes_through]
- AC5: POST and DELETE with an unlisted Origin are 403 forbidden_origin, without Origin they pass [evidence: test:tests/test_api_terminals.py::test_origin_guard]
- AC6: README, openapi.json and schema.d.ts match the app [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_readme_api.py]
- AC7: terminal contract cases are collected under the integration marker [evidence: command:uv run pytest -q -p no:cacheprovider -m integration --collect-only tests/test_fake_wrapper_contract.py]
- AC8: targeted suites, schema check and lint pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py tests/test_api_files.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check .]
- AC9: invalid_size passes through as 422 [evidence: test:tests/test_api_terminals.py::test_invalid_size_passes_through]
- AC10: a terminal_id outside ^term_[0-9a-f]{12}$ on DELETE is 422 invalid_request and the fake wrapper receives no request [evidence: test:tests/test_api_terminals.py::test_invalid_terminal_id_rejected]
- AC11: session_not_active passes through as 409 [evidence: test:tests/test_api_terminals.py::test_session_not_active_passes_through]
- AC12: the README error code list names session_not_active and invalid_size and the README tests stay green [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_readme_api.py]
- AC13: a DEBUG caplog over create, list and delete finds the derived token in no log record and no response [evidence: test:tests/test_api_terminals.py::test_token_not_in_logs_or_responses]
- AC14: the terminal routes work in tests that never run the app lifespan [evidence: test:tests/test_api_terminals.py::test_routes_work_without_lifespan]

## Files

- `src/agent_orchestrator/api/workspace.py`
- `src/agent_orchestrator/api/schemas.py`
- `tests/test_api_terminals.py`
- `tests/fakes/fake_wrapper.py`
- `tests/test_fake_wrapper_contract.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`

## Interfaces

- `POST /api/v1/agents/{agent_id}/terminals`, `GET /api/v1/clusters/{cluster_id}/terminals`, `DELETE /api/v1/agents/{agent_id}/terminals/{terminal_id}`; `schemas.CreateTerminal`, `TerminalView`, `TerminalList` (owns part `orch-terminals-api`, consumed by fe-terminal-socket and kind-e2e-workspace).
- FakeWrapper terminal HTTP and WebSocket routes (owns part `fake-wrapper-terminals`, consumed by terminal-ws-relay).
- Uses `workspace-proxy-module`, `origin-allowlist` and the wrapper contract `wrapper-terminals-api`.

## Expected outcome

A headless client can create, list and delete shells on any agent of a cluster through `/api/v1`; FakeWrapper speaks the wrapper terminal protocol for the relay task.

## Steps

- Extend FakeWrapper (HTTP and WebSocket, real socket so the relay can use it) and write `tests/test_api_terminals.py`; run `uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py`: fails (404).
- Add routes and schemas; rerun: passes.
- README sections, regenerate `openapi.json` and `schema.d.ts`; run the verify command: passes.
- Add contract cases to `tests/test_fake_wrapper_contract.py`; confirm collection.

## Notes

- `tests/test_api_files.py` stays in the verify because both tasks edit `api/workspace.py` and `fake_wrapper.py`.
- The fake's WebSocket route must check the bearer header like the real wrapper (denial 401) so the relay test proves the token is sent.
- `schema.d.ts` is generated; never hand-edit it.
- Builder check ruling 3: Rows or cols outside 1..1000 on create answer 422 with code invalid_size (wrapper, passed through by the orchestrator); a resize control frame out of range or malformed is ignored and logged, the socket stays open.

- 2026-10-23 amended: builder check rulings 3 add acceptance conditions AC9-AC9

- 2026-10-23 amended: interrogate rulings 4 (terminal_id format check, 422), 5 (README error list gains session_not_active and invalid_size), 7 (token hygiene caplog test), 8 (lifespan-less tests)
