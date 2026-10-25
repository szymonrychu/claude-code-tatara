---
title: agent api me
status: done
repo: agent-orchestrator
value: "an agent can ask the orchestrator who it is, who leads and who is in its hive"
files: [src/agent_orchestrator/api/agent.py, src/agent_orchestrator/api/app.py, src/agent_orchestrator/db/agents.py, tests/test_api_agent.py, tests/test_api_clusters.py, README.md, openapi.json, frontend/src/api/schema.d.ts]
verify: "uv run pytest tests/test_api_agent.py tests/test_api_clusters.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [agent-token-env-render, agents-pod-ip-observe]
model: ""
review: ""
verified_head: b916d84bd0098d3d2f6ad17c57622609d17e72db
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 7
actual_tokens: 1369834
actual_roles: "impl 7, review 2"
actual_role_tokens: "impl 1184759, review 185075"
---

# agent api me

## Requirement

Foundation part F4, agent API identity (D1). `src/agent_orchestrator/api/agent.py`, router `/agent/v1`, served only on the agent port (gate from agent-port-listener).

- Dependency `require_agent()` (the contract every agent route of this and later epics reuses): needs `Authorization: Bearer <token>` and `X-Orch-Cluster: <cluster_id>`; 401 `unauthorized` when either is missing, the cluster is unknown or the token does not equal `tokens_for(settings, cluster_id).agent` (`hmac.compare_digest`, the same answer for every case so nothing leaks); 403 `forbidden` when the direct socket peer IP (`scope["client"]`, D22, no forwarded headers) is not the `pod_ip` of a not-gone agent of that cluster; returns that agents row, which is the caller's identity (no self-asserted pod name).
- `GET /agent/v1/me` -> `{cluster_id, agent_id, pod_name, ordinal, leader, epoch, max_replicas, static, members: [{pod_name, ready, state, context_pct, leader}]}`: `leader` is the leader's pod name or null and `epoch` an int or null (from `cluster_leaders`); members are the not-gone agents by ordinal.
- `db/agents.py`: `by_pod_ip(conn, cluster_id, ip)`.
- `api/app.py` includes the router.
- `tests/test_api_clusters.py::test_api_never_imports_k8s_or_wrapper`: `agent.py` may import `agent_orchestrator.tokens` (never the wrapper client, k8s or reconciler); the MEMORY note lands in hive-docs-memory.
- README `## Agent API`: transport (agents Service, port 8001), headers, errors, `/me` schema; `openapi.json` and `frontend/src/api/schema.d.ts` regenerated.

## Acceptance conditions

- AC1: a request from an agent's pod IP with the cluster token gets 200 and that agent's identity [evidence: test:tests/test_api_agent.py::test_me_identity]
- AC2: a missing, wrong or other-cluster token gets 401 unauthorized with one shared message [evidence: test:tests/test_api_agent.py::test_token_rejections]
- AC3: a non-agent IP or a gone agent's former IP gets 403 forbidden [evidence: test:tests/test_api_agent.py::test_ip_binding]
- AC4: leader and epoch are null without a leader row and set with one; members list ready, state and context_pct [evidence: test:tests/test_api_agent.py::test_me_leader_and_members]
- AC5: the import pin allows tokens in agent.py and still forbids wrapper, k8s and reconciler imports [evidence: test:tests/test_api_clusters.py::test_api_never_imports_k8s_or_wrapper]
- AC6: README, openapi.json and schema.d.ts agree [evidence: command:uv run pytest tests/test_readme_api.py -q]
- AC7: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/api/agent.py`
- `src/agent_orchestrator/api/app.py`
- `src/agent_orchestrator/db/agents.py`
- `tests/test_api_agent.py`
- `tests/test_api_clusters.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`

## Interfaces

- Owns part `orch-agent-api-auth` (cross-epic contract): `api/agent.py` router and `require_agent()` returning the agents row; `GET /agent/v1/me` response as in the requirement.

## Expected outcome

An agent pod with its cluster token gets its identity, the leader and the members; anything else is refused.

## Steps

- Red: write `tests/test_api_agent.py` for AC1-AC4 and widen the import pin test for AC5; run `uv run pytest tests/test_api_agent.py tests/test_api_clusters.py -q`: fails.
- Green: router, dependency, `by_pod_ip`, README, openapi and schema regeneration; run the verify command: passes.

## Notes

- Test the IP binding by driving the ASGI app with a scope `client` of the agent's stored `pod_ip` and `server` on the agent port (httpx `ASGITransport` takes `client=`).
- Error shape: `api/errors.py` `error_response`.
