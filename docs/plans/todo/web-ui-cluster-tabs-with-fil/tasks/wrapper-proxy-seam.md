---
title: wrapper proxy seam
status: todo
repo: agent-orchestrator
value: "the api can reach a cluster's wrapper pods through one audited module"
files: [src/agent_orchestrator/api/workspace.py, src/agent_orchestrator/api/app.py, src/agent_orchestrator/wrapper/client.py, tests/test_workspace_proxy.py, tests/test_wrapper_client.py, tests/test_api_clusters.py, README.md, MEMORY.md]
verify: "uv run pytest -q -p no:cacheprovider tests/test_workspace_proxy.py tests/test_wrapper_client.py tests/test_api_clusters.py tests/test_settings.py && mise run lint"
depends_on: [origin-allowlist]
owns: [workspace-proxy-module]
uses: []
model: ""
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

# wrapper proxy seam

## Requirement

Open the narrow seam through which the orchestrator api may call wrapper pods (user decision N1, design D4), test-first, before any proxy route exists.

- New `src/agent_orchestrator/api/workspace.py`, the only api module allowed to import `agent_orchestrator.wrapper` or use `agent_orchestrator.tokens`. It provides:
  - `resolve_agent(conn, settings, *, cluster_id=None, agent_id=None) -> WrapperTarget` (`agent_id`, `cluster_id`, `pod_name`, `url`, `session_id`, `token`): with `agent_id` it loads that agent (404 `not_found` when unknown, or when `cluster_id` is given and differs); with only `cluster_id` it picks the first agent by ordinal that is ready (has `url` and `session_id` and a live status); none ready is 409 `agent_not_ready`; unknown cluster 404. The token is `tokens_for(settings, cluster_id).auth`; an unset master key raises 503 `unavailable`. Data comes from `db/agents.py` and `db/clusters.py`; no Kubernetes import.
  - a shared `httpx.AsyncClient` created in the app lifespan, stored on `app.state`, closed on shutdown, and a helper that sends a request to the wrapper through `WrapperClient` and maps the outcome: wrapper 2xx returned as JSON; wrapper 4xx re-raised as `ApiError` with the wrapper's status and code; wrapper 5xx 502 `wrapper_error`; transport failure 502 `wrapper_unreachable`.
- `WrapperClient` (`src/agent_orchestrator/wrapper/client.py`) gains one generic method used by the helper, for example `request_json(method, path, *, params=None, json=None) -> tuple[int, Any]`, with its own test in `tests/test_wrapper_client.py`; existing methods are unchanged.
- `tests/test_api_clusters.py::test_api_never_imports_k8s_or_wrapper` whitelists exactly `api/workspace.py` for `agent_orchestrator.wrapper` (still banned: `agent_orchestrator.k8s` and `agent_orchestrator.reconciler` everywhere, and `agent_orchestrator.wrapper` in every other api module); a second assertion fails if any other api module imports `agent_orchestrator.tokens`.
- README `## Architecture`: the api row says the api calls wrappers only for the file and terminal proxies in `api/workspace.py`, never Kubernetes; `## Configuration`: `ORCH_MASTER_KEY` and `ORCH_MASTER_KEY_FILE` "Read by" lists include the api for the proxies; error codes `agent_not_ready` (409), `wrapper_error` (502), `wrapper_unreachable` (502), `unavailable` (503) in the API intro list.
- `MEMORY.md`: a dated entry (2026-10-23) amending D5: the api now calls wrapper pods with derived tokens, only through `api/workspace.py`, for the file and terminal proxies (user decision N1), because the wrapper is the only process with the workdir mounted and a PTY, and Kubernetes `pods/exec` is excluded.

## Acceptance conditions

- AC1: resolve_agent picks the first ready agent by ordinal, honours an explicit agent_id, and answers not_found, agent_not_ready and unavailable as specified [evidence: test:tests/test_workspace_proxy.py::test_resolve_agent_rules]
- AC2: the forwarding helper maps wrapper 2xx, 4xx, 5xx and transport failure to the specified results [evidence: test:tests/test_workspace_proxy.py::test_forward_error_mapping]
- AC3: the shared httpx client is created in the lifespan and closed on shutdown [evidence: test:tests/test_workspace_proxy.py::test_shared_client_lifecycle]
- AC4: WrapperClient.request_json sends the bearer and returns status and body [evidence: test:tests/test_wrapper_client.py::test_request_json_passthrough]
- AC5: only api/workspace.py may import agent_orchestrator.wrapper or agent_orchestrator.tokens [evidence: test:tests/test_api_clusters.py::test_api_never_imports_k8s_or_wrapper]
- AC6: MEMORY.md records the D5 amendment with date and why, and README Architecture names the proxy module [evidence: judgement:MEMORY.md and README.md Architecture]
- AC7: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_workspace_proxy.py tests/test_wrapper_client.py tests/test_api_clusters.py tests/test_settings.py && mise run lint]

## Files

- `src/agent_orchestrator/api/workspace.py`
- `src/agent_orchestrator/api/app.py`
- `src/agent_orchestrator/wrapper/client.py`
- `tests/test_workspace_proxy.py`
- `tests/test_wrapper_client.py`
- `tests/test_api_clusters.py`
- `README.md`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
