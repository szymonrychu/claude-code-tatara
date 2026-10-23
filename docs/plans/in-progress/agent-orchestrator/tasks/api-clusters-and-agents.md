---
title: api clusters and agents
status: done
repo: agent-orchestrator
value: "The headless API's cluster and agent surface: define, edit, list, discard clusters and see each agent's live state."
files: [src/agent_orchestrator/api/__init__.py, src/agent_orchestrator/api/app.py, src/agent_orchestrator/api/errors.py, src/agent_orchestrator/api/schemas.py, src/agent_orchestrator/api/clusters.py, src/agent_orchestrator/db/views.py, tests/test_api_clusters.py, src/agent_orchestrator/api/allowlist.py]
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
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-api-clusters-and-agents/agent-orchestrator
branch: agent-orchestrator-api-clusters-and-agents
verified_head: 8d361062e98c6826832909a184315d77af948b00
run: agent-orchestrator
provides: [api-app, api-error-helpers, cluster-views]
acs_for_audit: []
process_gaps: []
---

# api clusters and agents

## Requirement

The FastAPI app factory and the clusters and agents routes (D11, D15, D13).

- Source allowlist (D22, `api/allowlist.py`): middleware that compares the direct socket peer (`scope["client"]`) with `settings.allowed_networks()` and answers any other peer 403 `{"error": {"code": "forbidden", ...}}`. `Forwarded`, `X-Forwarded-For` and `X-Real-IP` are ignored (ingress-nginx is hostNetwork, so ingress traffic arrives from node IPs; pod-CIDR callers are refused). `/healthz` and `/readyz` are exempt. The middleware is installed by `create_app` and cannot be turned off by a request.
- `POST` and `PATCH` on clusters run `validate_spec(spec, settings)` and map `SpecInvalid` to 422 `invalid_request`; `POST` beyond `settings.max_clusters` active clusters is 409 `cluster_limit`.
- `create_app(settings, pool=None) -> FastAPI`. The lifespan opens and closes the pool when none is given. OpenAPI lives at `/api/v1/openapi.json`, docs at `/api/v1/docs`.
- Errors always use `{"error": {"code", "message"}}`:
  - not_found 404, conflict 409
  - invalid_request 422 (and for validation errors)
  - bad_request 400, internal 500
- Health: `/healthz` returns 200; `/readyz` returns 200 when the database answers, else 503.
- `GET /api/v1/clusters`, `POST /api/v1/clusters {slug, spec}` (201).
- `GET`, `PATCH {spec}` and `DELETE /api/v1/clusters/{id}`:
  - DELETE is the discard (D15): it returns 202 and sets desired deleting; a repeated DELETE on a deleting cluster is also 202. There is no `purge` parameter: the reconciler runs the optional pre-discard hook, deletes every Kubernetes object, then deletes the row and its whole history, after which GET is 404.
  - PATCH on a deleting cluster is 409 `cluster_deleting`.
- `GET /api/v1/clusters/{id}/agents`.
- `GET /api/v1/meta`: settings defaults (model, effort, replicas, auto_compact_pct, pvc_size, storage class, max_attempts), agent image, the image allowlist, models list, the caps `max_replicas`, `max_pvc_size`, `max_clusters`, and `discard_hook` (`none`, `command` or `url`, never the command text or URL itself) so the discard dialog can name it.
- Cluster view: id, slug, spec, desired, status (including the discard hook state `discard_hook_delivered` or `discard_hook_failed`), generation, observed_generation, created_at, and `summary`:
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
- AC5: DELETE returns 202 and sets deleting, a repeat is 202, ?purge is not accepted, and once the row is gone GET is 404 [evidence: test:tests/test_api_clusters.py::test_delete_is_discard_without_purge]
- AC6: agents list joins agent_status into the agent view [evidence: test:tests/test_api_clusters.py::test_agents_view_joins_status]
- AC7: summary state is working or waiting and context_pct_max is the max over agents [evidence: test:tests/test_api_clusters.py::test_cluster_summary_state_and_gauge_max]
- AC8: unknown ids are 404 in the wrapper error shape [evidence: test:tests/test_api_clusters.py::test_errors_use_wrapper_shape]
- AC9: the api package imports no k8s, wrapper or reconciler module [evidence: test:tests/test_api_clusters.py::test_api_never_imports_k8s_or_wrapper]
- AC10: meta returns the settings defaults, the image allowlist, the caps and the discard hook kind without its target [evidence: test:tests/test_api_clusters.py::test_meta_defaults]
- AC11: a peer outside ORCH_ALLOWED_CIDRS gets 403 forbidden on every route except /healthz and /readyz [evidence: test:tests/test_api_clusters.py::test_foreign_peer_forbidden_except_health]
- AC12: Forwarded and X-Forwarded-For headers do not change the peer that is checked [evidence: test:tests/test_api_clusters.py::test_forwarded_headers_ignored_by_allowlist]
- AC13: create and patch reject an image outside the allowlist, reserved env keys and caps with 422 [evidence: test:tests/test_api_clusters.py::test_spec_hardening_enforced_on_create_and_patch]
- AC14: creating a cluster beyond max_clusters is 409 cluster_limit [evidence: test:tests/test_api_clusters.py::test_cluster_count_cap_409]

## Files

- `src/agent_orchestrator/api/__init__.py`
- `src/agent_orchestrator/api/app.py`
- `src/agent_orchestrator/api/errors.py`
- `src/agent_orchestrator/api/schemas.py`
- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/db/views.py`
- `tests/test_api_clusters.py`
- `src/agent_orchestrator/api/allowlist.py`

## Interfaces

- `agent_orchestrator.api.app:create_app` (contract `api-app`); routers are included in it, and later tasks add theirs
- `agent_orchestrator.api.errors:ApiError(status, code, message)`
- `agent_orchestrator.api.schemas`: `ClusterView`, `ClusterSummary`, `AgentView`, `CreateCluster`, `PatchCluster`, `Meta`

## Expected outcome

Clusters can be defined, edited and discarded through `/api/v1`, and the views carry everything the ribbon draws.

## Steps

- Write tests/test_api_clusters.py with the fourteen named tests (httpx AsyncClient over ASGITransport, pool fixture); run it; expect failures.
- Implement errors.py, schemas.py, views.py, clusters.py and app.py.
- Rerun `uv run pytest tests/test_api_clusters.py -q`; expect `14 passed`; run `mise run lint`.

## Notes

Error shape mirrors the wrapper (README:1949 of claude-code-wrapper). The API writes only clusters columns it owns (D3).
