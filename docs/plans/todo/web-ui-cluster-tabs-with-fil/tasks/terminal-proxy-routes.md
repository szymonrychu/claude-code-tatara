---
title: terminal proxy routes
status: todo
repo: agent-orchestrator
value: "headless clients and the UI can create, list and delete shells on any agent through /api/v1"
files: [src/agent_orchestrator/api/workspace.py, src/agent_orchestrator/api/schemas.py, tests/test_api_terminals.py, tests/fakes/fake_wrapper.py, tests/test_fake_wrapper_contract.py, README.md, openapi.json, frontend/src/api/schema.d.ts]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py tests/test_api_files.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && mise run lint"
depends_on: [file-proxy-routes, terminal-websocket-api, origin-allowlist]
owns: [orch-terminals-api, fake-wrapper-terminals]
uses: [workspace-proxy-module, origin-allowlist, wrapper-terminals-api]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# terminal proxy routes

## Requirement

Proxy the wrapper terminal lifecycle through the orchestrator api (design D4, D5; user Q4, Q5), test-first.

Routes in `src/agent_orchestrator/api/workspace.py`, models in `api/schemas.py`:

- `POST /api/v1/agents/{agent_id}/terminals` body `CreateTerminal` `{rows?, cols?}` (extra forbidden) -> 201 `TerminalView` `{agent_id, cluster_id, pod_name, terminal_id, created_at, alive, exit_code, attached, rows, cols}`; forwards to `POST /v1/sessions/{session_id}/terminals` on that agent; wrapper `terminal_limit` passes through as 409.
- `GET /api/v1/clusters/{cluster_id}/terminals` -> 200 `TerminalList` `{terminals: [TerminalView], unavailable_agents: [agent_id]}`: queries every ready agent of the cluster concurrently (bounded by the shared client timeouts); an agent that fails is listed in `unavailable_agents` instead of failing the request.
- `DELETE /api/v1/agents/{agent_id}/terminals/{terminal_id}` -> 204; wrapper `terminal_not_found` passes through as 404.
- POST and DELETE depend on `require_allowed_origin` (part `origin-allowlist`): an unlisted Origin is 403 `forbidden_origin`.

FakeWrapper gains the terminal HTTP routes and a WebSocket attach route that emulates the wrapper protocol (replay buffer, echo of input bytes as output, resize and ping control, exit frame, close codes, bearer check), and `tests/test_fake_wrapper_contract.py` gains terminal cases (HTTP and WebSocket) against fake and real image under `-m integration`.

README: a `###` section per route; `terminal_limit` (409), `terminal_not_found` (404) and `forbidden_origin` usage in the error code list. Regenerate `openapi.json` and `frontend/src/api/schema.d.ts`.

## Acceptance conditions

- AC1: create forwards to the agent's session and returns TerminalView with agent and pod fields [evidence: test:tests/test_api_terminals.py::test_create_on_agent]
- AC2: the cluster list merges every ready agent's terminals and reports a failing agent in unavailable_agents [evidence: test:tests/test_api_terminals.py::test_cluster_list_fans_out]
- AC3: delete returns 204 and unknown terminals are 404 terminal_not_found [evidence: test:tests/test_api_terminals.py::test_delete]
- AC4: terminal_limit passes through as 409 [evidence: test:tests/test_api_terminals.py::test_limit_passes_through]
- AC5: POST and DELETE with an unlisted Origin are 403 forbidden_origin, without Origin they pass [evidence: test:tests/test_api_terminals.py::test_origin_guard]
- AC6: README, openapi.json and schema.d.ts match the app [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_readme_api.py]
- AC7: terminal contract cases are collected under the integration marker [evidence: command:uv run pytest -q -p no:cacheprovider -m integration --collect-only tests/test_fake_wrapper_contract.py]
- AC8: targeted suites, schema check and lint pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py tests/test_api_files.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && mise run lint]

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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
