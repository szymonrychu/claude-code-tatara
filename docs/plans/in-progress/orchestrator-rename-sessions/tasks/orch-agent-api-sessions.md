---
title: orch agent api sessions
status: in-progress
repo: agents-orchestrator
value: agents talk to their session through X-Orch-Session with any-mcp v0.3.0
files: [src/agents_orchestrator/api/agent.py, src/agents_orchestrator/k8s/render.py, src/agents_orchestrator/k8s/on_start.py, src/agents_orchestrator/settings.py, pyproject.toml, uv.lock, openapi.json, tests/]
verify: "uv run pytest -q tests/test_api_agent.py tests/test_agent_port.py tests/test_agent_scale.py tests/test_agent_init_scripts.py tests/test_on_start.py tests/test_render.py tests/test_nomenclature.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-sessions-sweep, anymcp-release-v0-3-0]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch agent api sessions

## Requirement

Rename the agent API's unit to session and pin any-mcp v0.3.0 (design D2, D11; contracts `orch-agent-api-session-header`, `any-mcp-release-v0-3-0`). Paths are in code/agents-orchestrator.

- `api/agent.py`: `require_agent()` reads `X-Orch-Session` (no `X-Orch-Cluster` fallback: a request carrying only the old header is refused like a missing header); `Me.session_id` replaces `Me.cluster_id`; every docstring and message says session. The token binding (Bearer token derived for the session id, caller IP equals `agents.pod_ip`) is unchanged.
- `k8s/render.py`: the agent pod env `ORCH_SESSION_ID` replaces `ORCH_CLUSTER_ID` (in `AGENT_PASSTHROUGH_ENV` too); the wrapper hook header renders `X-Orch-Session: ${ORCH_SESSION_ID}`.
- `k8s/on_start.py`: the rendered any-mcp orchestrator plugin entry uses key `session: ${ORCH_SESSION_ID}`.
- any-mcp pin: `pyproject.toml` `any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.3.0`, `uv.lock` refreshed, `settings.any_mcp_ref` default `v0.3.0`.
- `openapi.json` regenerated; README agent API section (header, `Me`, env names).
- `tests/test_nomenclature.py`: drop the agent-API exceptions so the guard covers all of `src/agents_orchestrator`, `tests` and `openapi.json`.
- Tests first: `tests/test_api_agent.py::test_old_cluster_header_refused`, `tests/test_render.py::test_agent_env_session_id`, `tests/test_on_start.py::test_plugin_entry_session_key` (validated with any-mcp v0.3.0's `AnyMcpConfig`), and `tests/test_agent_scale.py` running the real v0.3.0 `OrchestratorPlugin` against the agent API.

## Acceptance conditions

- AC1: the agent API accepts X-Orch-Session and refuses a request carrying only X-Orch-Cluster [evidence: test:tests/test_api_agent.py::test_old_cluster_header_refused]
- AC2: agent pods get ORCH_SESSION_ID and the hook header renders X-Orch-Session [evidence: test:tests/test_render.py::test_agent_env_session_id]
- AC3: the rendered any-mcp plugin entry uses the session key and validates under any-mcp v0.3.0 [evidence: test:tests/test_on_start.py::test_plugin_entry_session_key]
- AC4: the whole of src, tests and openapi.json names the unit session only [evidence: command:uv run pytest -q tests/test_nomenclature.py tests/test_readme_api.py]
- AC5: the agent API suites and lint pass [evidence: command:uv run pytest -q tests/test_api_agent.py tests/test_agent_port.py tests/test_agent_scale.py tests/test_agent_init_scripts.py tests/test_on_start.py tests/test_render.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/api/agent.py`
- `src/agents_orchestrator/k8s/render.py`
- `src/agents_orchestrator/k8s/on_start.py`
- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `openapi.json`
- `tests/`

## Interfaces

- `require_agent()`: `Authorization: Bearer <agent token>` plus `X-Orch-Session: <session id>`, caller IP = `agents.pod_ip`; `Me.session_id`; pod env `ORCH_SESSION_ID`; rendered plugin entry `{..., session: ${ORCH_SESSION_ID}, ...}` (contract `orch-agent-api-session-header`, matches any-mcp v0.3.0).

## Expected outcome

Agents reach their session's agent API with any-mcp v0.3.0; the old header is refused; the whole repo's src, tests and openapi.json pass the nomenclature guard.

## Steps

- Precondition: tag any-mcp v0.3.0 exists (`git ls-remote --tags https://github.com/szymonrychu/any-mcp v0.3.0`); else end `blocked`, whoCanClear "orchestrator: tag any-mcp v0.3.0".
- Red: bump the pin, `uv lock`, write the three named tests; run them: they fail.
- Green: rename header, env, field and plugin key; regenerate openapi.json; widen the guard; the verify passes.

## Notes

- The token derivation input (`purpose:session id`) is unchanged, so live tokens stay valid across the rename.
