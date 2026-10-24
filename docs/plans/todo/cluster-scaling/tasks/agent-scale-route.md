---
title: agent scale route
status: todo
repo: agent-orchestrator
value: the leader agent grows or shrinks its own hive with a tool
files: [src/agent_orchestrator/api/agent.py, README.md, openapi.json, frontend/src/api/schema.d.ts, tests/test_agent_scale.py]
verify: "uv run --frozen pytest -q tests/test_agent_scale.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [scale-replicas-repo, public-scale-route]
owns: [orch-agent-scale-api]
uses: [scale-replicas-write, scale-schemas]
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

# agent scale route

## Requirement

Add the agent-facing scale route behind the leader check (design D2, D4; user S2, X1, Q4; foundation D1, D2). In `src/agent_orchestrator/api/agent.py` (the `/agent/v1` router built by hive-mode-leadership-handove F4) add `POST /agent/v1/scale` taking `ScaleRequest` and answering 202 `ScaleResult`. The caller is the agents row returned by F4's `require_agent()` dependency (token, `X-Orch-Cluster` and caller IP equal to `agents.pod_ip`); the route calls `set_replicas(..., caller_agent_id=agent.id)` and maps `not_leader` 403, `static_cluster` 409, `out_of_range` 422, `leader_would_leave` 409, `cluster_deleting` 409; authentication failures stay those of `require_agent()` (401, 403 `forbidden`). The route is served only on the agent port (F4 port branch): the same path on the public port answers 404, and `/api/v1/clusters/{id}/scale` is not reachable on the agent port. Document it in README `## Agent API` with its errors, in F4's format, and regenerate `openapi.json` and `frontend/src/api/schema.d.ts` when F4 includes agent routes there. Contract test: drive the `orchestrator_scale` tool of the pinned any-mcp `OrchestratorPlugin` (F1, release v0.2.0) against the orchestrator app and assert the tool returns the 202 body for the leader and reports `not_leader` as a tool error for another agent, so a mismatch between the plugin and this route fails here.

## Acceptance conditions

- AC1: the leader's call answers 202 and spec.replicas changes [evidence: test:tests/test_agent_scale.py::test_leader_scales_202]
- AC2: a ready non-leader agent of the same cluster gets 403 not_leader and nothing changes [evidence: test:tests/test_agent_scale.py::test_non_leader_refused_403]
- AC3: static_cluster, out_of_range and leader_would_leave are mapped like the public route; a missing token is 401 and a foreign caller IP is 403 forbidden [evidence: test:tests/test_agent_scale.py::test_agent_scale_refusals]
- AC4: /agent/v1/scale is 404 on the public port and the public scale route is 404 on the agent port [evidence: test:tests/test_agent_scale.py::test_scale_ports_are_separate]
- AC5: the any-mcp orchestrator_scale tool round-trips against the route for the leader and surfaces not_leader for another agent [evidence: test:tests/test_agent_scale.py::test_plugin_scale_tool_contract]
- AC6: README documents the agent scale route [evidence: command:grep -q "/agent/v1/scale" README.md]
- AC7: README and openapi checks stay green [evidence: command:uv run --frozen pytest -q tests/test_readme_api.py]
- AC8: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/api/agent.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`
- `tests/test_agent_scale.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
