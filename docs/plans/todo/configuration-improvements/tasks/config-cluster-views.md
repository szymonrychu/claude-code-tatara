---
title: config cluster views
status: todo
repo: agent-orchestrator
value: "API callers can set and see every new field, documented"
files: [src/agent_orchestrator/api/schemas.py, src/agent_orchestrator/db/views.py, src/agent_orchestrator/api/clusters.py, README.md, openapi.json, tests/test_api_config.py]
verify: "uv run --frozen pytest -q tests/test_api_config.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [spec-config-fields]
owns: [orch-cluster-config-api]
uses: [orch-spec-config-fields, orch-presets-api, orch-cluster-create-api]
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

# config cluster views

## Requirement

Document and expose the new fields through the public API (design D9, D11; approvals A1, A3, A4, A6).

- `src/agent_orchestrator/api/schemas.py`: `ClusterView` adds `closes_at: datetime | None` (`created_at + autoclose_after_seconds`, null when unset), `leader_since: datetime | None` and `leader_reason: str | None` (from `cluster_leaders`, null without a leader).
- `src/agent_orchestrator/db/views.py` (the aggregates query) and `src/agent_orchestrator/api/clusters.py` (the view builder) fill them.
- The create and preset routes already validate `ClusterSpec` through `check_spec` and `validate_spec`; a refused new field answers 422 `invalid_request` whose message names the field, on `POST /api/v1/clusters`, `POST /api/v1/presets` and `PUT /api/v1/presets/{id}`, and a cluster created from a preset snapshots the preset's new fields.
- README.md: `### Cluster configuration` under `## API` documenting `spec.wrapper` (every key of design D1, its wrapper config path, the reserved entries and the `$` escaping), `leader_lease_seconds`, `autoclose_after_seconds`, `ORCH_AUTOCLOSE_MIN_SECONDS`, the three view fields and the refusal messages; the `POST /api/v1/clusters` field list and the ClusterView field list name the new fields.
- Regenerate `openapi.json` with `uv run python -m agent_orchestrator.api.openapi > openapi.json`.

## Acceptance conditions

- AC1: a spec with a full wrapper block, a lease and an autoclose round-trips through POST /api/v1/clusters, the preset routes, and a cluster created from that preset [evidence: test:tests/test_api_config.py::test_config_fields_round_trip_through_presets_and_clusters]
- AC2: a bad hook, a lease on a single-agent spec and an autoclose below the floor answer 422 invalid_request naming the field on the cluster and preset routes [evidence: test:tests/test_api_config.py::test_config_fields_refused_with_named_errors]
- AC3: the cluster view shows closes_at as created_at plus autoclose_after_seconds or null, and leader_since and leader_reason from the leader row or null [evidence: test:tests/test_api_config.py::test_cluster_view_lease_and_autoclose_fields]
- AC4: README documents the cluster configuration fields for API callers [evidence: doc-section:README.md#Cluster configuration]
- AC5: openapi.json is regenerated and matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/api/schemas.py`
- `src/agent_orchestrator/db/views.py`
- `src/agent_orchestrator/api/clusters.py`
- `README.md`
- `openapi.json`
- `tests/test_api_config.py`

## Interfaces

Builds part `orch-cluster-config-api` (README `### Cluster configuration` and the ClusterView fields; consumed by kind-e2e-config, web-form-config-fields, web-clusters-page and smoke-config-check); uses `orch-spec-config-fields` and the contracts `orch-presets-api` and `orch-cluster-create-api`.

## Expected outcome

`GET /api/v1/clusters/{id}` shows the new spec fields plus `closes_at`, `leader_since` and `leader_reason`; README `### Cluster configuration` documents them; openapi.json is current.

## Steps

- Red, write `tests/test_api_config.py` with the three tests
- Green, add the view fields and docs
- Regenerate openapi.json
- Run the verify command.

## Notes

After frontend-decoupling the orchestrator repo has no `frontend/`, so no `schema.d.ts` is regenerated here; agents-web syncs its vendored copy in web-form-config-fields. `leader_reason` is set by test SQL here; the lease task produces `lease_expired` in production.
