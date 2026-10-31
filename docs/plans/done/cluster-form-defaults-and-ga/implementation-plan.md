# cluster form defaults and gauge tick implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: sonnet)

### S1: deploy pin d5a7738

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agent-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `uv run pytest -q -p no:cacheprovider && mise run lint`
- Verified head: 7329bc8d44d83b96616485336f273d94f8744ea4

#### Requirement

Deploy agent-orchestrator main d5a7738 (PR #3 merge): set helmfile.yaml.gotmpl release agent-orchestrator chart version to 0.1.0-main.d5a7738 and values/agent-orchestrator/common.yaml image tag to d5a7738. Nothing else changes. Pin the new version in a test so a stale pin is caught (the test asserts the chart version and image tag agree on the same sha7).

#### Acceptance conditions

- AC1: chart version and image tag both point at d5a7738 and agree [evidence: command:uv run pytest -q -p no:cacheprovider && mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

`helmfile diff` would show only the image tag and chart version change for agent-orchestrator.

#### Steps

- Add a test in tests/test_orchestrator_release.py asserting chart version 0.1.0-main.d5a7738 and image tag d5a7738; run `uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py`: fails.
- Change the two pins; rerun the verify command: passes.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S2: deterministic in-flight cap test

- Status: done
- Files: `tests/test_dispatcher.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_dispatcher.py && mise run lint`
- Verified head: 3fcbb0ba697209495a2b3a6cc21b3379da6e5068

#### Requirement

tests/test_dispatcher.py::test_at_most_eight_sends_in_flight is timing-flaky: under full-suite load the peak reaches 7, not 8 (seen twice in full runs, always passes alone). Make it deterministic without weakening it: the counting _send wrapper blocks on an asyncio.Event released only after 8 sends are in flight (or after a bounded timeout that fails the test), so the test asserts the cap is reached and never exceeded, instead of relying on asyncio.sleep(0.2) overlap. Do not change dispatcher behaviour.

#### Acceptance conditions

- AC1: the in-flight cap test reaches exactly 8 concurrent sends and passes 20 runs in a row [evidence: command:for i in $(seq 20); do uv run pytest -q -p no:cacheprovider tests/test_dispatcher.py::test_at_most_eight_sends_in_flight || exit 1; done]

#### Files

- `tests/test_dispatcher.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The cap test synchronises on an event, not sleep overlap, and is stable under load.

#### Steps

- Test-only change (exception: the test itself is the deliverable). Rewrite the wrapper to gate on an asyncio.Event set when now reaches 8; assert peak == 8 and never above.
- Run the AC1 loop: 20 passes. Run the verify command.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S3: meta form defaults

- Status: done
- Files: `src/agent_orchestrator/settings.py`, `src/agent_orchestrator/api/clusters.py`, `src/agent_orchestrator/api/schemas.py`, `src/agent_orchestrator/spec.py`, `src/agent_orchestrator/k8s/render.py`, `openapi.json`, `frontend/src/api/schema.d.ts`, `README.md`
- Verify: `uv run pytest tests/test_settings.py tests/test_api_clusters.py tests/test_render.py tests/test_readme_api.py -q -p no:cacheprovider && mise run lint`
- Verified head: 9b0efb6c24775830a06976d9277c367ac511df31

#### Requirement

Settings and /meta carry every cluster-form default. settings.py: models default [claude-opus-5-5, claude-sonnet-5-5, claude-haiku-5-5, claude-fable-5-1] (ORCH_MODELS), default_model claude-opus-5-5 (ORCH_DEFAULT_MODEL), efforts [low, medium, high, xhigh, max] (ORCH_EFFORTS), default_effort stays configurable (ORCH_DEFAULT_EFFORT, empty = Claude Code default), default resources cpu request 500m / limit 4, memory request 1Gi / limit 8Gi (ORCH_DEFAULT_CPU_REQUEST, ORCH_DEFAULT_CPU_LIMIT, ORCH_DEFAULT_MEMORY_REQUEST, ORCH_DEFAULT_MEMORY_LIMIT), validated as Kubernetes quantities. GET /api/v1/meta returns models, efforts and defaults for every ClusterSpec field the form edits (model, effort, replicas, pvc_size, storage_class, workdir, max_attempts, auto_compact_pct, resources requests/limits, any_mcp_config, discard hook). k8s/render.py applies the default resources to agent containers when the spec leaves a value empty (explicit spec values win per key). Spec validation rejects a model not in settings.models and an effort not in settings.efforts (empty effort allowed). Regenerate openapi.json and frontend/src/api/schema.d.ts (npm run gen:api) and update the README configuration table.

#### Acceptance conditions

- AC1: settings expose the model, effort and resource defaults with env overrides [evidence: test:tests/test_settings.py::test_form_defaults_and_overrides]
- AC2: /meta returns models, efforts and a default for every form field [evidence: test:tests/test_api_clusters.py::test_meta_returns_all_form_defaults]
- AC3: agent pods get default resources when the spec leaves them empty, spec values win per key [evidence: test:tests/test_render.py::test_default_resources_applied_per_key]
- AC4: spec rejects unknown model or effort [evidence: test:tests/test_api_clusters.py::test_spec_rejects_unknown_model_and_effort]
- AC5: frontend API types match openapi.json [evidence: test:tests/test_readme_api.py::test_frontend_schema_matches_openapi]

#### Files

- `src/agent_orchestrator/settings.py`
- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/api/schemas.py`
- `src/agent_orchestrator/spec.py`
- `src/agent_orchestrator/k8s/render.py`
- `openapi.json`
- `frontend/src/api/schema.d.ts`
- `README.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The requirement holds, pinned by the acceptance tests.

What is true and observable when the task is done.

#### Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S4: defaults at write time and legacy edit

- Status: done
- Files: `src/agent_orchestrator/api/clusters.py`, `src/agent_orchestrator/spec.py`, `src/agent_orchestrator/k8s/render.py`, `tests/test_render.py`, `tests/test_api_clusters.py`, `tests/golden/cluster_single.yaml`, `tests/golden/cluster_two_peers.yaml`, `README.md`
- Verify: `uv run pytest tests/test_render.py tests/test_api_clusters.py -q -p no:cacheprovider && mise run lint`
- Verified head: 2d099eca38ab71be5e17c4332237c42cb442a38a

#### Requirement

Honour the README non-goal "No change to clusters already running until they are edited" and keep edit mode usable for clusters stored before this epic.
1. Resource defaults move from render time to write time. POST and PATCH /api/v1/clusters fill each empty resources key (requests.cpu, requests.memory, limits.cpu, limits.memory) from settings before storing the spec; explicit values win per key. A default limit is not filled when it would be below the spec's explicit request of the same resource, and a default request is not filled when it would be above the spec's explicit limit. k8s/render.py stops merging defaults and emits the stored spec resources as-is (no resources key when the spec has none), so a running cluster whose spec has no resources renders exactly as before this epic; tests/golden/cluster_single.yaml and tests/golden/cluster_two_peers.yaml return to their pre-epic content for that case. Replace test_default_resources_applied_per_key with tests that pin the write-time fill (per key, the request/limit guard) and the unchanged render.
2. PATCH validates model and effort against settings.models / settings.efforts only when the value differs from the stored one: re-saving a cluster whose stored model or effort is outside the lists succeeds, changing to an unknown value still returns 422. POST keeps full validation. The merged request-vs-limit check uses the same rule: a stored spec with requests.cpu 8 and no limit can be patched (the guard in 1 leaves the limit empty).

#### Acceptance conditions

- AC1: POST/PATCH fill empty resource keys from settings, explicit keys win, the request/limit guard holds [evidence: test:tests/test_api_clusters.py::test_write_fills_default_resources_per_key]
- AC2: render emits stored resources as-is and a spec without resources renders no resources key [evidence: test:tests/test_render.py::test_render_keeps_spec_resources_unchanged]
- AC3: PATCH accepts an unchanged out-of-list model or effort and rejects a changed unknown one [evidence: test:tests/test_api_clusters.py::test_patch_keeps_stored_legacy_model_and_effort]
- AC4: PATCH of a stored spec with requests.cpu 8 and no limit succeeds [evidence: test:tests/test_api_clusters.py::test_patch_high_request_without_limit]

#### Files

- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/spec.py`
- `src/agent_orchestrator/k8s/render.py`
- `tests/test_render.py`
- `tests/test_api_clusters.py`
- `tests/golden/cluster_single.yaml`
- `tests/golden/cluster_two_peers.yaml`
- `README.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

Rendering a stored spec without resources gives the pre-epic pod template (golden files match the pre-epic content). New and edited clusters store default resources. Re-saving a legacy cluster in the form succeeds.

#### Steps

- Write the AC1-AC5 tests and run the verify command: they fail.
- Move the resource fill from k8s/render.py into the POST/PATCH write path (api/clusters.py or spec.py), with the request/limit guard; restore the golden files to `git show origin/main:tests/golden/<file>`.
- Make PATCH validate model/effort only when changed.
- Run the verify command: all pass.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S5: form dropdowns and gauge tick

- Status: done
- Files: `frontend/src/clusters/ClusterForm.tsx`, `frontend/src/clusters/ClusterForm.test.tsx`, `frontend/src/clusters/clusterSpecForm.ts`, `frontend/src/ribbon/ContextGauge.tsx`, `frontend/src/ribbon/ContextGauge.test.tsx`
- Verify: `cd frontend && npx vitest run src/clusters src/ribbon && npm run lint`
- Verified head: c993d7c1e48faa40a81d4f87d79ee0836a479ea7

#### Requirement

ClusterForm (frontend/src/clusters/ClusterForm.tsx): Model and Effort are select dropdowns fed by /meta models and efforts (Effort includes an empty 'model default' entry; an edited cluster whose value is not in the list keeps it as an extra option). Every other field is prefilled from /meta defaults exactly the way Max attempts is (blankValues(meta)), including cpu/memory requests and limits, workdir, any-mcp config and the auto-compact percent. ContextGauge (frontend/src/ribbon/ContextGauge.tsx): the auto-compact tick is a short radial mark lying on the ring at autoCompactPct (rotated about the gauge centre, inside the gauge box), not a skewed bar outside the circle; pin its geometry in the test. Theme tokens only (designRules test stays green).

#### Acceptance conditions

- AC1: Model and Effort render as selects with the /meta options [evidence: command:cd frontend && npx vitest run src/clusters/ClusterForm.test.tsx]
- AC2: create mode prefills every field from /meta defaults [evidence: command:cd frontend && npx vitest run src/clusters/ClusterForm.test.tsx]
- AC3: the gauge tick is a radial mark on the ring at the auto-compact percent [evidence: command:cd frontend && npx vitest run src/ribbon]
- AC4: frontend lint, tests and build pass [evidence: command:cd frontend && npm run lint && npm test && npm run build && npm run check:api]

#### Files

- `frontend/src/clusters/ClusterForm.tsx`
- `frontend/src/clusters/ClusterForm.test.tsx`
- `frontend/src/clusters/clusterSpecForm.ts`
- `frontend/src/ribbon/ContextGauge.tsx`
- `frontend/src/ribbon/ContextGauge.test.tsx`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The requirement holds, pinned by the acceptance tests.

What is true and observable when the task is done.

#### Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S6: model default option

- Status: done
- Files: `frontend/src/clusters/ClusterForm.tsx`, `frontend/src/clusters/ClusterForm.test.tsx`
- Verify: `cd frontend && npx vitest run src/clusters && npm run lint`
- Verified head: 34631bdb6477cad78277a8766ef29d9dd5376f2e

#### Requirement

ClusterForm.tsx: the Model select gets an empty "default" option like Effort, so an edited cluster with a null model shows that option instead of a blank select; the create form still preselects meta.defaults.model.

#### Acceptance conditions

- AC1: Model select offers an empty default option and an edited cluster with a null model shows it [evidence: command:cd frontend && npx vitest run src/clusters/ClusterForm.test.tsx]

#### Files

- `frontend/src/clusters/ClusterForm.tsx`
- `frontend/src/clusters/ClusterForm.test.tsx`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The Model select lists a default (empty) option followed by meta.models; null model in edit mode selects it.

#### Steps

- Add the AC1 test, run `cd frontend && npx vitest run src/clusters/ClusterForm.test.tsx`: it fails.
- Add the empty option to the Model select, reuse the Effort select's pattern; rerun: passes; `npm run lint` clean.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S7: fast full-spec form test

- Status: done
- Files: `frontend/src/clusters/ClusterForm.test.tsx`
- Verify: `cd frontend && npx vitest run src/clusters && npm run lint`
- Verified head: 3f272a6823fb43b2d13b3de545b5d8cb23b42a83

#### Requirement

PR #3 frontend CI fails: frontend/src/clusters/ClusterForm.test.tsx "creates cluster with full spec" hits the 5000 ms vitest default timeout on the GitHub runner (5046 ms; job 120353282871). Make it fast without weakening its assertions: replace character-by-character userEvent.type calls for long values (slug, env key/value, webhook URL, every prefilled field it rewrites) with the file's existing paste helper or a userEvent.setup({ delay: null }) instance, so the test runs well under 2 s locally. Also give that one test an explicit 15000 ms timeout as CI headroom. Do not change ClusterForm.tsx behaviour.

#### Acceptance conditions

- AC1: ClusterForm tests pass and "creates cluster with full spec" runs under 2000 ms locally [evidence: command:cd frontend && npx vitest run src/clusters/ClusterForm.test.tsx --reporter=verbose]

#### Files

- `frontend/src/clusters/ClusterForm.test.tsx`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The full-spec test runs in well under 2 s locally with a 15 s explicit timeout; assertions unchanged.

#### Steps

- Test-only change (exception: no behaviour change). Record the current duration with `npx vitest run src/clusters/ClusterForm.test.tsx --reporter=verbose`.
- Switch long typing to paste or a no-delay userEvent instance, add the 15000 ms timeout, rerun: passes, duration under 2000 ms.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
