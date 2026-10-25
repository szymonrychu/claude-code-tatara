---
title: retire cluster patch route
status: done
repo: agent-orchestrator
value: "running clusters can no longer be edited through the API, so they never restart under a live spec change"
files: [src/agent_orchestrator/api/clusters.py, src/agent_orchestrator/api/schemas.py, tests/test_api_clusters.py, README.md, MEMORY.md, openapi.json, frontend/src/api/schema.d.ts]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_clusters.py tests/test_api_presets.py tests/test_api_create_from_preset.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && mise x node@24.20.0 -- npm --prefix frontend run build && uv run ruff check . && uv run ruff format --check ."
depends_on: [create-cluster-from-preset, fe-preset-form]
model: ""
review: ""
verified_head: 97af5310b0335f47c62c74b8a20674460e70dce4
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 8
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# retire cluster patch route

## Requirement

Retire live cluster edit from the API (design D5; user Q4 and N2), test-first; the frontend stopped calling it in fe-preset-form.

- `api/clusters.py`: delete `patch_cluster`; `check_spec(spec, settings, stored=None)` keeps its `stored` parameter, which the preset PUT uses (builder check ruling 2).
- `api/schemas.py`: delete `PatchCluster`.
- `tests/test_api_clusters.py`: delete `test_patch_bumps_generation`, `test_patch_keeps_stored_legacy_model_and_effort` and the PATCH calls in `test_delete_is_discard_without_purge`; `test_spec_hardening_enforced_on_create_and_patch` becomes create-only; `test_write_fills_default_resources_per_key` and `test_patch_high_request_without_limit` keep their write-time fill coverage through POST. Add the retirement test `test_patch_cluster_retired_405`: `PATCH /api/v1/clusters/{id}` on an existing cluster answers 405, the app has no PATCH route under `/api/v1`, and `openapi.json` has no `patch` operation.
- README: the `### PATCH /api/v1/clusters/{cluster_id}` section is removed; every other README mention of editing a running cluster is removed or rewritten (a spec is fixed at create; to change it, discard and schedule again from a preset); the `Versioning` paragraph keeps "additive only" and adds a documented exception dated 2026-10-23 naming the PATCH removal and the create body that needs exactly one of `spec` and `preset_id`, with the why (a live edit rolled every agent pod; clusters now snapshot their preset).
- `MEMORY.md`: a dated (2026-10-23) entry for the exception and why.
- `openapi.json` and `frontend/src/api/schema.d.ts` regenerated; `npm run build` stays green (client.ts no longer names `PatchCluster`).

## Acceptance conditions

- AC1: PATCH on an existing cluster answers 405, no PATCH route exists under /api/v1, and openapi.json has no patch operation [evidence: test:tests/test_api_clusters.py::test_patch_cluster_retired_405]
- AC2: the spec hardening and write-time fill tests pass through POST only [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_api_clusters.py]
- AC3: patch_cluster and PatchCluster are gone from the api package [evidence: command:! grep -rnE 'patch_cluster|PatchCluster' src/agent_orchestrator/api]
- AC4: README documents the additive-only exception with date and why, and no PATCH section remains [evidence: doc-section:README.md#API]
- AC5: MEMORY.md records the exception with the date and why [evidence: judgement:MEMORY.md entry dated 2026-10-23 reviewed]
- AC6: README, openapi.json and schema.d.ts match the app and the frontend builds [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && mise x node@24.20.0 -- npm --prefix frontend run build]
- AC7: targeted tests and lint pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_clusters.py tests/test_api_presets.py tests/test_api_create_from_preset.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/api/schemas.py`
- `tests/test_api_clusters.py`
- `README.md`
- `MEMORY.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`

## Interfaces

- `check_spec(spec, settings) -> ClusterSpec` (part `check-spec-public`, final signature).
- `PATCH /api/v1/clusters/{cluster_id}` no longer exists; GET and DELETE on the path are unchanged.

## Expected outcome

The API cannot change a running cluster's spec any more; README, MEMORY and OpenAPI say so and why.

## Steps

- Add `test_patch_cluster_retired_405` and rewrite the PATCH-based tests to POST; run `uv run pytest -q -p no:cacheprovider tests/test_api_clusters.py`: the retirement test fails.
- Delete the route and schema, edit README and MEMORY, regenerate `openapi.json` and `schema.d.ts`; run the verify command: passes.

## Notes

- Deletion pinned by a retirement test (`test_patch_cluster_retired_405`).
- FastAPI answers 405 for a known path with an unknown method; `api/errors.py` maps it to `bad_request`, which the test may assert.
- `cluster_deleting` stays: messages and checks still return it.
- fe-preset-form already removed `PatchCluster` from `client.ts`, so `npm run build` stays green after the schema regen.
- Builder check ruling 2 (2026-10-23): PUT of a preset accepts a stored model, effort or image that is no longer in the settings lists only when that value is unchanged from the stored preset (the legacy rule PATCH used); changing to an unknown value is 422. validate_spec keeps its `stored` parameter (and check_spec its `stored` parameter) for this; retire-spec-update-repo must not delete it, it still deletes update_spec and ClusterDeleting if unused. Scheduling always validates fully (no `stored`) and returns 422 with the reason and the preset name. The editor's Model/Effort select shows a stored out-of-list value as an extra option labelled "<value> (not available)".

- 2026-10-23 amended: builder check ruling 2: check_spec keeps stored for the preset PUT (AC3 grep narrowed)
