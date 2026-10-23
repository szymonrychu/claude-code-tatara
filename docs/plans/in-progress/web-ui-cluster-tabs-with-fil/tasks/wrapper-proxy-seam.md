---
title: wrapper proxy seam
status: in-progress
repo: agent-orchestrator
value: "the api can reach a cluster's wrapper pods through one audited module"
files: [src/agent_orchestrator/api/workspace.py, src/agent_orchestrator/api/app.py, src/agent_orchestrator/wrapper/client.py, tests/test_workspace_proxy.py, tests/test_wrapper_client.py, tests/test_api_clusters.py, README.md, MEMORY.md]
verify: "uv run pytest -q -p no:cacheprovider tests/test_workspace_proxy.py tests/test_wrapper_client.py tests/test_api_clusters.py tests/test_settings.py && uv run ruff check . && uv run ruff format --check ."
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
  - `resolve_agent(conn, settings, *, cluster_id=None, agent_id=None) -> WrapperTarget` (a frozen dataclass: `agent_id`, `cluster_id`, `pod_name`, `url`, `session_id`, and `token` declared `field(repr=False)` so it never shows in a repr, traceback or log line): with `agent_id` it loads that agent (404 `not_found` when unknown, or when `cluster_id` is given and differs); with only `cluster_id` it picks the first agent by ordinal that is ready (has `url` and `session_id` and a live status); none ready is 409 `agent_not_ready`; unknown cluster 404. The token is `tokens_for(settings, cluster_id).auth`; an unset master key raises 503 `unavailable`. Data comes from `db/agents.py` and `db/clusters.py`; no Kubernetes import.
  - a shared `httpx.AsyncClient` created lazily on first use (a `get_client(app)` helper, stored on `app.state`; no lifespan needed, so tests that never run the lifespan and drive the app through `httpx.ASGITransport` work), closed in the lifespan shutdown when it was created, and a helper that sends a request to the wrapper through `WrapperClient` and maps the outcome: wrapper 2xx returned as JSON; wrapper 4xx re-raised as `ApiError` with the wrapper's status and code; wrapper 5xx 502 `wrapper_error`; transport failure 502 `wrapper_unreachable`.
- `WrapperClient` (`src/agent_orchestrator/wrapper/client.py`) gains one generic method used by the helper, for example `request_json(method, path, *, params=None, json=None) -> tuple[int, Any]`, with its own test in `tests/test_wrapper_client.py`; existing methods are unchanged.
- `tests/test_api_clusters.py::test_api_never_imports_k8s_or_wrapper` whitelists exactly `api/workspace.py` for `agent_orchestrator.wrapper` (still banned: `agent_orchestrator.k8s` and `agent_orchestrator.reconciler` everywhere, and `agent_orchestrator.wrapper` in every other api module); a second assertion fails if any other api module imports `agent_orchestrator.tokens`.
- README `## Architecture`: the api row says the api calls wrappers only for the file and terminal proxies in `api/workspace.py`, never Kubernetes; `## Configuration`: `ORCH_MASTER_KEY` and `ORCH_MASTER_KEY_FILE` "Read by" lists include the api for the proxies; error codes `agent_not_ready` (409), `wrapper_error` (502), `wrapper_unreachable` (502), `unavailable` (503) in the API intro list.
- `MEMORY.md`: a dated entry (2026-10-23) amending D5: the api now calls wrapper pods with derived tokens, only through `api/workspace.py`, for the file and terminal proxies (user decision N1), because the wrapper is the only process with the workdir mounted and a PTY, and Kubernetes `pods/exec` is excluded.
- Token hygiene: the derived token is sent only as the `Authorization` header by `WrapperClient` (never in a URL, query string, response body, error detail or log message); a `caplog` test at DEBUG over the helper (file path and terminal path requests, success and every error mapping) finds the token in no log record and no response (interrogate ruling 7).
- Terminal id check: this module defines, once, `TERMINAL_ID_RE = re.compile(r"^term_[0-9a-f]{12}$")` (the wrapper registry's id format) and `validate_terminal_id(value) -> str`, which raises `ApiError` 422 `invalid_request` for anything else; the terminal HTTP routes and the WebSocket relay call it before any upstream request so the derived bearer can never reach another upstream path through a crafted id such as `..` (interrogate ruling 4).

## Acceptance conditions

- AC1: resolve_agent picks the first ready agent by ordinal, honours an explicit agent_id, and answers not_found, agent_not_ready and unavailable as specified [evidence: test:tests/test_workspace_proxy.py::test_resolve_agent_rules]
- AC2: the forwarding helper maps wrapper 2xx, 4xx, 5xx and transport failure to the specified results [evidence: test:tests/test_workspace_proxy.py::test_forward_error_mapping]
- AC3: the shared httpx client is created lazily on first use, reused, and closed in the lifespan shutdown [evidence: test:tests/test_workspace_proxy.py::test_shared_client_lifecycle]
- AC4: WrapperClient.request_json sends the bearer and returns status and body [evidence: test:tests/test_wrapper_client.py::test_request_json_passthrough]
- AC5: only api/workspace.py may import agent_orchestrator.wrapper or agent_orchestrator.tokens [evidence: test:tests/test_api_clusters.py::test_api_never_imports_k8s_or_wrapper]
- AC6: MEMORY.md records the D5 amendment with date and why, and README Architecture names the proxy module [evidence: judgement:MEMORY.md and README.md Architecture]
- AC7: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_workspace_proxy.py tests/test_wrapper_client.py tests/test_api_clusters.py tests/test_settings.py && uv run ruff check . && uv run ruff format --check .]
- AC8: an app driven through httpx.ASGITransport without running the lifespan can use the proxy helper (the client is created on demand) [evidence: test:tests/test_workspace_proxy.py::test_client_works_without_lifespan]
- AC9: WrapperTarget.token is excluded from repr and a DEBUG caplog over file and terminal proxy requests, success and error paths, finds the token in no log record and no response [evidence: test:tests/test_workspace_proxy.py::test_token_never_in_logs_or_responses]
- AC10: validate_terminal_id accepts term_<12 lowercase hex> and answers 422 invalid_request for .., term_zz, uppercase, overlong, empty and path-like ids [evidence: test:tests/test_workspace_proxy.py::test_terminal_id_validator]

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

- `agent_orchestrator.api.workspace.resolve_agent`, `WrapperTarget`, the forwarding helper and the lifespan-managed client on `app.state` (owns part `workspace-proxy-module`, consumed by file-proxy-routes, terminal-proxy-routes, terminal-ws-relay).
- `agent_orchestrator.wrapper.client.WrapperClient.request_json`.

## Expected outcome

The api has one audited module that can reach a cluster's wrapper pods with the derived token; every other api module stays wrapper-free, and the docs say so.

## Steps

- Write `tests/test_workspace_proxy.py` (DB fixtures `pool`/`dsn`, `tests/factories.py:insert_cluster`/`insert_agent`, `FakeWrapper` for the forwarding cases), `test_request_json_passthrough` in `tests/test_wrapper_client.py`, and tighten `test_api_never_imports_k8s_or_wrapper`; run `uv run pytest -q -p no:cacheprovider tests/test_workspace_proxy.py tests/test_wrapper_client.py tests/test_api_clusters.py`: new tests fail.
- Implement `api/workspace.py`, the lifespan client in `api/app.py`, `request_json`; rerun: passes.
- README and MEMORY edits; `uv run pytest -q -p no:cacheprovider tests/test_settings.py`: passes.
- `uv run ruff check . && uv run ruff format --check .`: clean.

## Notes

- `db/views.py:agent_rows` does not select `url`/`session_id`; use `db/agents.py:get_agent`/`list_agents` (`Agent.url`, `Agent.session_id`, `pod_name`, `ordinal`).
- Readiness: use the same notion of a usable agent the dispatcher uses (has a session and is not in a dead or discarding state); name the exact rule in the docstring.
- `WrapperClient` errors are `WrapperError`/`WrapperUnreachable` (`wrapper/client.py`); reuse its `_error_parts` for the wrapper code.
- DB tests use testcontainers (dockerd is running in this container).

- 2026-10-23 amended: interrogate rulings 4 (terminal id format pinned in one place), 7 (token hygiene: repr=False, header only, caplog test), 8 (shared httpx client created lazily so lifespan-less ASGITransport tests work)
