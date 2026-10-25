---
title: defaults at write time and legacy edit
status: done
repo: agent-orchestrator
value: "deploying the new image does not roll running clusters, and old clusters stay editable"
files: [src/agent_orchestrator/api/clusters.py, src/agent_orchestrator/spec.py, src/agent_orchestrator/k8s/render.py, tests/test_render.py, tests/test_api_clusters.py, tests/golden/cluster_single.yaml, tests/golden/cluster_two_peers.yaml, README.md]
verify: "uv run pytest tests/test_render.py tests/test_api_clusters.py -q -p no:cacheprovider && mise run lint"
depends_on: [meta-form-defaults]
model: sonnet
review: ""
verified_head: 2d099eca38ab71be5e17c4332237c42cb442a38a
points: 1
expected_minutes: 7
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# defaults at write time and legacy edit

## Requirement

Honour the README non-goal "No change to clusters already running until they are edited" and keep edit mode usable for clusters stored before this epic.
1. Resource defaults move from render time to write time. POST and PATCH /api/v1/clusters fill each empty resources key (requests.cpu, requests.memory, limits.cpu, limits.memory) from settings before storing the spec; explicit values win per key. A default limit is not filled when it would be below the spec's explicit request of the same resource, and a default request is not filled when it would be above the spec's explicit limit. k8s/render.py stops merging defaults and emits the stored spec resources as-is (no resources key when the spec has none), so a running cluster whose spec has no resources renders exactly as before this epic; tests/golden/cluster_single.yaml and tests/golden/cluster_two_peers.yaml return to their pre-epic content for that case. Replace test_default_resources_applied_per_key with tests that pin the write-time fill (per key, the request/limit guard) and the unchanged render.
2. PATCH validates model and effort against settings.models / settings.efforts only when the value differs from the stored one: re-saving a cluster whose stored model or effort is outside the lists succeeds, changing to an unknown value still returns 422. POST keeps full validation. The merged request-vs-limit check uses the same rule: a stored spec with requests.cpu 8 and no limit can be patched (the guard in 1 leaves the limit empty).

## Acceptance conditions

- AC1: POST/PATCH fill empty resource keys from settings, explicit keys win, the request/limit guard holds [evidence: test:tests/test_api_clusters.py::test_write_fills_default_resources_per_key]
- AC2: render emits stored resources as-is and a spec without resources renders no resources key [evidence: test:tests/test_render.py::test_render_keeps_spec_resources_unchanged]
- AC3: PATCH accepts an unchanged out-of-list model or effort and rejects a changed unknown one [evidence: test:tests/test_api_clusters.py::test_patch_keeps_stored_legacy_model_and_effort]
- AC4: PATCH of a stored spec with requests.cpu 8 and no limit succeeds [evidence: test:tests/test_api_clusters.py::test_patch_high_request_without_limit]

## Files

- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/spec.py`
- `src/agent_orchestrator/k8s/render.py`
- `tests/test_render.py`
- `tests/test_api_clusters.py`
- `tests/golden/cluster_single.yaml`
- `tests/golden/cluster_two_peers.yaml`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

Rendering a stored spec without resources gives the pre-epic pod template (golden files match the pre-epic content). New and edited clusters store default resources. Re-saving a legacy cluster in the form succeeds.

## Steps

- Write the AC1-AC5 tests and run the verify command: they fail.
- Move the resource fill from k8s/render.py into the POST/PATCH write path (api/clusters.py or spec.py), with the request/limit guard; restore the golden files to `git show origin/main:tests/golden/<file>`.
- Make PATCH validate model/effort only when changed.
- Run the verify command: all pass.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
