---
title: retire cluster patch route
status: todo
repo: agent-orchestrator
value: "running clusters can no longer be edited through the API, so they never restart under a live spec change"
files: [src/agent_orchestrator/api/clusters.py, src/agent_orchestrator/api/schemas.py, tests/test_api_clusters.py, README.md, MEMORY.md, openapi.json, frontend/src/api/schema.d.ts]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_clusters.py tests/test_api_presets.py tests/test_api_create_from_preset.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && mise x node@24.20.0 -- npm --prefix frontend run build && uv run ruff check . && uv run ruff format --check ."
depends_on: [create-cluster-from-preset, fe-preset-form]
owns: []
uses: [check-spec-public]
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

# retire cluster patch route

## Requirement

Retire live cluster edit from the API (design D5; user Q4 and N2), test-first; the frontend stopped calling it in fe-preset-form.

- `api/clusters.py`: delete `patch_cluster`; `check_spec(spec, settings)` loses its `stored` parameter.
- `api/schemas.py`: delete `PatchCluster`.
- `tests/test_api_clusters.py`: delete `test_patch_bumps_generation`, `test_patch_keeps_stored_legacy_model_and_effort` and the PATCH calls in `test_delete_is_discard_without_purge`; `test_spec_hardening_enforced_on_create_and_patch` becomes create-only; `test_write_fills_default_resources_per_key` and `test_patch_high_request_without_limit` keep their write-time fill coverage through POST. Add the retirement test `test_patch_cluster_retired_405`: `PATCH /api/v1/clusters/{id}` on an existing cluster answers 405, the app has no PATCH route under `/api/v1`, and `openapi.json` has no `patch` operation.
- README: the `### PATCH /api/v1/clusters/{cluster_id}` section is removed; every other README mention of editing a running cluster is removed or rewritten (a spec is fixed at create; to change it, discard and schedule again from a preset); the `Versioning` paragraph keeps "additive only" and adds a documented exception dated 2026-10-23 naming the PATCH removal and the create body that needs exactly one of `spec` and `preset_id`, with the why (a live edit rolled every agent pod; clusters now snapshot their preset).
- `MEMORY.md`: a dated (2026-10-23) entry for the exception and why.
- `openapi.json` and `frontend/src/api/schema.d.ts` regenerated; `npm run build` stays green (client.ts no longer names `PatchCluster`).

## Acceptance conditions

- AC1: PATCH on an existing cluster answers 405, no PATCH route exists under /api/v1, and openapi.json has no patch operation [evidence: test:tests/test_api_clusters.py::test_patch_cluster_retired_405]
- AC2: the spec hardening and write-time fill tests pass through POST only [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_api_clusters.py]
- AC3: patch_cluster and PatchCluster are gone from the api package [evidence: command:! grep -rnE 'patch_cluster|PatchCluster|stored: ClusterSpec' src/agent_orchestrator/api]
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
