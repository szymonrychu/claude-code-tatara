---
title: public scale route
status: done
repo: agent-orchestrator
value: users and headless callers scale a cluster through a documented API
files: [src/agent_orchestrator/api/clusters.py, src/agent_orchestrator/api/schemas.py, README.md, openapi.json, frontend/src/api/schema.d.ts, tests/test_api_scale.py]
verify: "uv run --frozen pytest -q tests/test_api_scale.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [scale-replicas-repo]
model: ""
review: ""
verified_head: 126947162cca4e6a9c5241d9b51dcf331a3878aa
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 3
actual_tokens: 790807
actual_roles: "impl 2, review 2"
actual_role_tokens: "impl 416257, review 374550"
---

# public scale route

## Requirement

Add the public scale route for headless parity (design D2, D5; user S2, S3, X2; foundation D4). `POST /api/v1/clusters/{cluster_id}/scale` in `src/agent_orchestrator/api/clusters.py`, body `ScaleRequest {replicas: int}` (extra fields forbidden), answers 202 with `ScaleResult {cluster_id, replicas, previous_replicas, max_replicas}` (both models in `api/schemas.py`; the agent route reuses them). It calls `db.clusters.set_replicas` with no caller agent and maps `ScaleRefused`: `static_cluster` 409, `out_of_range` 422, `leader_would_leave` 409, `cluster_deleting` 409; unknown cluster 404 `not_found`; a malformed body 422 `invalid_request`. The route imports neither `k8s` nor `wrapper` (existing guard test). README.md: an H3 for the route, the four codes added to `## API` Error codes, the `max_replicas` and `static` spec fields in the `POST /api/v1/clusters` field list when not yet there, and a `### Scaling` section under `## API` that documents cap, static and replicas for API callers: `max_replicas` (1..`ORCH_MAX_REPLICAS`, default `replicas`, fixed at create), `static` (requires `max_replicas == replicas`), derived hive/alone/scalable, `spec.replicas` changed in place by this route and the agent route with no generation bump and no restart of surviving pods, scale-down removes the highest ordinals after the drain (D3), the leader is never removed (`leader_would_leave`; make another agent leader first), new pods never re-run init scripts. Regenerate `openapi.json` and `frontend/src/api/schema.d.ts`.

## Acceptance conditions

- AC1: scaling up and down answers 202 with the ScaleResult and the cluster view shows the new spec.replicas with an unchanged generation [evidence: test:tests/test_api_scale.py::test_scale_returns_202_and_updates_view]
- AC2: static_cluster 409, out_of_range 422, cluster_deleting 409, not_found 404 and invalid_request 422 are returned in the documented error shape [evidence: test:tests/test_api_scale.py::test_scale_refusals_map_to_error_codes]
- AC3: a scale that would remove the current leader answers 409 leader_would_leave and changes nothing [evidence: test:tests/test_api_scale.py::test_scale_leader_would_leave]
- AC4: the route is documented and openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_every_route_documented]
- AC5: openapi.json is regenerated [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC6: README documents cap, static and replicas for API callers [evidence: doc-section:README.md#Scaling]
- AC7: the frontend types match openapi.json [evidence: command:cd frontend && npm run check:api]
- AC8: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/api/schemas.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`
- `tests/test_api_scale.py`

## Interfaces

- Builds `POST /api/v1/clusters/{cluster_id}/scale` (part `orch-cluster-scale-api`, registered cross-epic, consumers agents-helmfile smoke) and `api/schemas.py::ScaleRequest`, `ScaleResult` (part `scale-schemas`).
- Uses `db/clusters.py::set_replicas` (part `scale-replicas-write`).
- README `### Scaling` is the API caller's reference for cap, static, replicas, drain (`status.drain {target, since, waiting}`, built by scale-down-drain) and the leader rule.

## Expected outcome

`curl -X POST .../clusters/<id>/scale -d '{"replicas":3}'` answers 202 and the cluster grows; every refusal has a documented code.

## Steps

- Red: write `tests/test_api_scale.py` with the three tests (factories for the cluster, a `cluster_leaders` row for the leader case); run `uv run --frozen pytest -q tests/test_api_scale.py`: fails with 404/405.
- Green: add the schemas and route; document in README; run `uv run python -m agent_orchestrator.api.openapi > openapi.json` and `npm --prefix frontend run gen:api`; run the verify command and `cd frontend && npm run check:api`.

## Notes

- Follow the existing `ApiError(status, code, message)` pattern in `api/errors.py`; no new error class is needed.
- `ClusterSpec` and the ClusterView already carry `max_replicas` and `static` after hive F3; this task adds only docs for them where missing.
- The route sits beside `create_cluster` and uses the same `Pool` dependency; no `_CREATE_LOCK` (the row lock in `set_replicas` serialises scale calls per cluster).
