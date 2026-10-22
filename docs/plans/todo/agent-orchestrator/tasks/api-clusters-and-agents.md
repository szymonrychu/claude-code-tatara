---
title: api clusters and agents
status: todo
repo: agent-orchestrator
value: "The headless API's cluster and agent surface: define, edit, list, discard and purge clusters and see each agent's live state."
files: [src/agent_orchestrator/api/__init__.py, src/agent_orchestrator/api/app.py, src/agent_orchestrator/api/errors.py, src/agent_orchestrator/api/schemas.py, src/agent_orchestrator/api/clusters.py, src/agent_orchestrator/db/views.py, tests/test_api_clusters.py]
verify: "uv run pytest tests/test_api_clusters.py -q && mise run lint"
depends_on: [clusters-repository, settings-model]
owns: [api-app]
uses: [cluster-spec, settings, schema-v1, pg-fixture]
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

# api clusters and agents

## Requirement

The FastAPI app factory and the clusters and agents routes (D11, D15, D13).

- `create_app(settings, pool=None) -> FastAPI`. The lifespan opens and closes the pool when none is given. OpenAPI lives at `/api/v1/openapi.json`, docs at `/api/v1/docs`.
- Errors always use `{"error": {"code", "message"}}`:
  - not_found 404, conflict 409
  - invalid_request 422 (and for validation errors)
  - bad_request 400, internal 500
- Health: `/healthz` returns 200; `/readyz` returns 200 when the database answers, else 503.
- `GET /api/v1/clusters`, `POST /api/v1/clusters {slug, spec}` (201).
- `GET`, `PATCH {spec}` and `DELETE /api/v1/clusters/{id}`:
  - DELETE returns 202 and sets desired deleting.
  - `?purge=true` on a cluster already deleted purges it; on a live one it is 409 with code `not_deleted`.
- `GET /api/v1/clusters/{id}/agents`.
- `GET /api/v1/meta`: settings defaults (model, effort, replicas, auto_compact_pct, pvc_size, storage class), agent image, models list.
- Cluster view: id, slug, spec, desired, status, generation, observed_generation, created_at, deleted_at, and `summary`:
  - `state`: working when any agent is busy, waiting when every ready agent is idle, booting, error or deleting
  - `ready`, `replicas`
  - `context_pct_max` (max over agents, null when none known)
  - `auto_compact_pct`, `queued`, `failed`
- Agent view: id, ordinal, pod_name, ready, state, free_since, current_turn_id, `context {used_tokens, window_tokens, used_percentage}` or null, peers count, gone.
- `db/views.py` holds the read-only queries. The api package never imports `agent_orchestrator.k8s`, `agent_orchestrator.wrapper` or `agent_orchestrator.reconciler` (D1).

## Acceptance conditions

- AC1: POST then GET returns the cluster with generation 1 [evidence: test:tests/test_api_clusters.py::test_create_and_get_cluster]
- AC2: a bad slug or spec is 422 in the error shape [evidence: test:tests/test_api_clusters.py::test_create_rejects_bad_slug_422]
- AC3: a duplicate slug is 409 [evidence: test:tests/test_api_clusters.py::test_duplicate_slug_409]
- AC4: PATCH bumps generation [evidence: test:tests/test_api_clusters.py::test_patch_bumps_generation]
- AC5: DELETE sets deleting; purge on a deleted cluster drops it and its history [evidence: test:tests/test_api_clusters.py::test_delete_then_purge]
- AC6: agents list joins agent_status into the agent view [evidence: test:tests/test_api_clusters.py::test_agents_view_joins_status]
- AC7: summary state is working or waiting and context_pct_max is the max over agents [evidence: test:tests/test_api_clusters.py::test_cluster_summary_state_and_gauge_max]
- AC8: unknown ids are 404 in the wrapper error shape [evidence: test:tests/test_api_clusters.py::test_errors_use_wrapper_shape]
- AC9: the api package imports no k8s, wrapper or reconciler module [evidence: test:tests/test_api_clusters.py::test_api_never_imports_k8s_or_wrapper]
- AC10: meta returns the settings defaults [evidence: test:tests/test_api_clusters.py::test_meta_defaults]

## Files

- `src/agent_orchestrator/api/__init__.py`
- `src/agent_orchestrator/api/app.py`
- `src/agent_orchestrator/api/errors.py`
- `src/agent_orchestrator/api/schemas.py`
- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/db/views.py`
- `tests/test_api_clusters.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
