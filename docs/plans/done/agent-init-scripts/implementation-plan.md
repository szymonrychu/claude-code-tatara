# agent init scripts implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: init scripts spec field

- Status: done
- Files: `src/agent_orchestrator/spec.py`, `tests/test_spec_init_scripts.py`, `tests/test_render.py`, `openapi.json`, `frontend/src/api/schema.d.ts`, `README.md`
- Verify: `uv run pytest tests/test_spec_init_scripts.py tests/test_render.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 41da5fab4a7a94ff18382e55a34abc388750a041

#### Requirement

Add init scripts to ClusterSpec, and so to presets (user decision C1; design D1). Paths are in code/agent-orchestrator. Precondition: the hive-mode-leadership-handove foundation tasks (F3 spec/render, F4 agent API) are on main; this task builds on that code.

- `src/agent_orchestrator/spec.py`: `ClusterSpec.init_scripts: list[str] = []`. Field validator: at most 20 entries; each entry is a string that is non-empty after strip and at most 16384 characters; the message names the offending index. `extra="forbid"` stays. Add the module constant `INIT_DIR = ".agent-init"` and `init_scripts_hash(scripts: list[str]) -> str` = sha256 hex of `json.dumps(scripts, separators=(",", ":"))` (defined for the empty list too). These two are the only shared definitions the reconciler, the api and the views use for the directory and the hash.
- Render: `init_scripts` never reaches any rendered object (ConfigMap, Secret, Service, PVC, StatefulSet template). Extend the hive hash pin test `tests/test_render.py::test_runtime_fields_change_only_statefulset_replicas` (contract "Hash invariant", owned by hive) so two specs that differ only in `init_scripts` render byte-identical objects, StatefulSet included. If that test does not exist under that name on main, add `test_init_scripts_never_rendered` in the same file with the same assertion.
- Presets: a preset POST/PUT body carrying `init_scripts` stores it sparse (only when set, as the existing `exclude_unset` dump does) and rejects an invalid list with 422 `invalid_request`; creating a cluster from a preset snapshots `init_scripts` into the cluster spec (the existing `_create_from_preset` path; no code change expected there, the test pins it).
- Docs and generated files: document the field (limits, run once per cluster, edits apply to the next cluster, never rendered into pods) where README.md documents ClusterSpec fields; regenerate `openapi.json` (`uv run python -m agent_orchestrator.api.openapi > openapi.json`) and `frontend/src/api/schema.d.ts` (`npm --prefix frontend run gen:api`) so `tests/test_readme_api.py` passes.

Interfaces: `spec.py::ClusterSpec.init_scripts`, `spec.py::INIT_DIR`, `spec.py::init_scripts_hash` (contract orch-cluster-spec-init-scripts).

Steps: write `tests/test_spec_init_scripts.py` (model limits, hash, preset round trip through the API client fixture, create-from-preset snapshot) and the render pin first, see them fail, then add the field.

#### Acceptance conditions

- AC1: ClusterSpec accepts up to 20 non-empty scripts of at most 16384 characters and rejects an empty entry, a 21st entry and an oversize entry with a message naming the index [evidence: test:tests/test_spec_init_scripts.py::test_init_scripts_limits]
- AC2: init_scripts_hash is the sha256 of the compact JSON list and differs when any script changes [evidence: test:tests/test_spec_init_scripts.py::test_init_scripts_hash]
- AC3: two specs that differ only in init_scripts render byte-identical objects [evidence: command:uv run pytest tests/test_render.py -q -k "runtime_fields_change_only_statefulset_replicas or init_scripts_never_rendered"]
- AC4: a preset created and updated with init_scripts returns them sparse, an invalid list is 422 invalid_request [evidence: test:tests/test_spec_init_scripts.py::test_preset_round_trips_init_scripts]
- AC5: a cluster created from a preset carries the preset's init_scripts in its spec [evidence: test:tests/test_spec_init_scripts.py::test_cluster_from_preset_snapshots_init_scripts]
- AC6: README documents the field and openapi.json and schema.d.ts match the code [evidence: command:uv run pytest tests/test_readme_api.py -q]
- AC7: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/spec.py`
- `tests/test_spec_init_scripts.py`
- `tests/test_render.py`
- `openapi.json`
- `frontend/src/api/schema.d.ts`
- `README.md`

#### Interfaces

- `src/agent_orchestrator/spec.py::ClusterSpec.init_scripts`, `spec.py::INIT_DIR`, `spec.py::init_scripts_hash` (contract orch-cluster-spec-init-scripts).
- Keeps the hive hash invariant test green and extends it to `init_scripts`.

#### Expected outcome

A preset or cluster spec carries `init_scripts`; nothing rendered for pods changes with it; README, openapi.json and schema.d.ts describe it.

#### Steps

- Red: write `tests/test_spec_init_scripts.py` and the render pin; `uv run pytest tests/test_spec_init_scripts.py tests/test_render.py -q` fails on the missing field.
- Green: add the field, constant and hash helper; regenerate openapi.json and schema.d.ts; document in README; run the verify command: all pass.

#### Notes

- Presets dump `exclude_unset` (`api/presets.py:42-54`), so an unset `init_scripts` stays absent from the stored preset.
- `extra="forbid"` means older orchestrator builds reject a spec with the field; this build only moves forward.

### S2: smoke init scripts

- Status: done
- Files: `scripts/smoke.sh`, `tests/test_smoke_script.py`, `README.md`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: ce31b78b15b14faee9019662ad3cbfacb90ee18b

#### Requirement

Extend the deployed smoke to prove init scripts end to end (user decisions C1, X2; design D7). Paths are in code/agents-helmfile.

- `scripts/smoke.sh`: the smoke cluster body becomes `{slug, spec: {replicas: 1, init_scripts: ["echo smoke-init"]}}` (still a raw spec, no preset). Pick the agent pod by name, `pod/agent-${SLUG}-0`, instead of the first pod of the cluster label selector: the init Job pod carries the same cluster label and must never be taken for the agent. After the pod is Ready and any-mcp is checked, poll `GET /api/v1/clusters/${CLUSTER_ID}/init-scripts` within the remaining `SMOKE_TIMEOUT_S` until `.status.state` is `succeeded` (fail fast on `failed`, printing `.status.reason`, `.status.exit_code` and `.status.log_tail`), assert `.status.log_tail` contains `smoke-init` and `.scripts == ["echo smoke-init"]`, and log each step. Cleanup, strict mode, bounded waits and the trap stay as they are.
- `tests/test_smoke_script.py`: the fake API and fake kubectl serve the init-scripts route and a Job pod listed before the agent pod; tests for the happy path (init succeeded, the agent pod chosen by name even when the Job pod is listed first), init failed exits non-zero with the reason and still cleans up, and init never finishing within the timeout fails and cleans up. Existing tests keep passing; the shellcheck test stays green.
- README `## Operating` smoke line mentions the init scripts check.

#### Acceptance conditions

- AC1: the happy path exits 0, creates the cluster with init_scripts, picks agent-<slug>-0 even when the init Job pod is listed first, and sees init succeeded with smoke-init in the log tail [evidence: test:tests/test_smoke_script.py::test_init_scripts_succeed]
- AC2: a failed init exits non-zero printing the reason and exit code and deletes the cluster [evidence: test:tests/test_smoke_script.py::test_init_scripts_failed_fails_and_cleans_up]
- AC3: an init that never finishes within the timeout fails and deletes the cluster [evidence: test:tests/test_smoke_script.py::test_init_scripts_timeout_fails_and_cleans_up]
- AC4: the existing smoke tests, the strict-mode test and shellcheck pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

#### Interfaces

- Consumes `GET /api/v1/clusters/{id}/init-scripts` and `status.init` (contracts orch-cluster-init-scripts-api, orch-cluster-status-init).

#### Expected outcome

`mise run smoke` creates its cluster with an init script and fails unless the init run succeeds and is visible through the API.

#### Steps

- Red: add the three smoke tests with the fake API and kubectl; `uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py` fails.
- Green: update `scripts/smoke.sh`; run the verify command: all pass, shellcheck clean.

#### Notes

- Today the pod is the first of `kubectl get pods -l agents.szymonrichert.pl/cluster=<slug>` (`scripts/smoke.sh`, step 3); the init Job pod matches that label.

### S3: fe preset init scripts

- Status: done
- Files: `frontend/src/clusters/clusterSpecForm.ts`, `frontend/src/presets/PresetForm.tsx`, `frontend/src/presets/PresetForm.test.tsx`
- Verify: `cd frontend && npx vitest run src/presets/PresetForm.test.tsx && npm run lint`
- Verified head: 5de9bd8393d2c5ca835f44215aa867b6dadce8d1

#### Requirement

Init scripts as preset form fields in the UI (user decisions C1, X2; design D5). Paths are in code/agent-orchestrator/frontend. The generated `src/api/schema.d.ts` already carries `init_scripts` (task init-scripts-spec-field).

- `src/clusters/clusterSpecForm.ts`: form value `initScripts: string[]`, set key `initScripts` (added to `SetKey`); loading a stored spec fills it and marks it set when `init_scripts` is present; validation mirrors the server (at most 20 entries, each non-empty after trim and at most 16384 characters; the error names the script number); the built spec carries `init_scripts` only when the key is set (sparse, like the other fields); clearing every row of a set key sends `[]`.
- `src/presets/PresetForm.tsx`: an "Init scripts" group after the any-mcp config, modelled on the env rows: one multiline monospace TextField per script labelled `Init script <n>`, a remove button `Remove init script <n>`, an `Add init script` button, and helper text "Runs once when a cluster starts, in the shared workdir; agents can read and edit it; edits apply to the next cluster." Theme tokens only, no colour literals (designRules).
- `src/presets/PresetForm.test.tsx`: add, edit, remove, load existing, validation messages, sparse submit body.

Interfaces: `clusterSpecForm.ts` `SetKey` `initScripts`, form value `initScripts`.

Steps: write the PresetForm tests first, see them fail, implement; then `npm run build` and `npm run check:api`.

#### Acceptance conditions

- AC1: the preset form adds, edits and removes init script rows and submits them as init_scripts [evidence: command:cd frontend && npx vitest run src/presets/PresetForm.test.tsx -t "init scripts"]
- AC2: an existing preset's init_scripts load into the rows and a preset without them submits no init_scripts key [evidence: command:cd frontend && npx vitest run src/presets/PresetForm.test.tsx -t "init scripts sparse"]
- AC3: an empty or oversize script and a 21st script show a validation message naming the script and block Save [evidence: command:cd frontend && npx vitest run src/presets/PresetForm.test.tsx -t "init scripts validation"]
- AC4: lint, typecheck build, design rules and API drift check pass [evidence: command:cd frontend && npm run lint && npm run build && npx vitest run src/layout/designRules.test.ts && npm run check:api]

#### Files

- `frontend/src/clusters/clusterSpecForm.ts`
- `frontend/src/presets/PresetForm.tsx`
- `frontend/src/presets/PresetForm.test.tsx`

#### Interfaces

- `frontend/src/clusters/clusterSpecForm.ts` `SetKey` `initScripts`, form value `initScripts: string[]`, its validation (reused by fe-cluster-init-dialog).

#### Expected outcome

The preset form edits init scripts as rows and submits them sparse.

#### Steps

- Red: add the PresetForm tests; `cd frontend && npx vitest run src/presets/PresetForm.test.tsx` fails.
- Green: form value, validation, rows; run the verify command, then `npm run build` and `npm run check:api`.

#### Notes

- Export the validation helper so the cluster dialog reuses it.

### S4: init job runner

- Status: done
- Files: `src/agent_orchestrator/reconciler/init.py`, `src/agent_orchestrator/reconciler/loop.py`, `src/agent_orchestrator/reconciler/checks.py`, `tests/test_init_runner.py`, `README.md`, `MEMORY.md`
- Verify: `uv run pytest tests/test_init_runner.py tests/test_reconciler.py tests/test_checks.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 36d4fed9a4856bed44ceec5026b58c52fabe83bc

#### Requirement

Run a cluster's init scripts exactly once per cluster, as one Kubernetes Job, and record the run in `clusters.status.init` (user decisions C1, C2; design D2, D3). Paths are in code/agent-orchestrator.

New module `src/agent_orchestrator/reconciler/init.py` with `InitRunner(pool, kube, settings)` and `async step(cluster) -> InitGate`, called from `ReconcileLoop._converge` in `reconciler/loop.py` after the apply and prune and before `_bootstrap_sessions`.

State, written only by the reconciler through the existing merging `_write_status` (other status keys survive): `status.init = {state, scripts_hash, started_at, finished_at, exit_code, log_tail, reason, job}` (contract orch-cluster-status-init). `state` is one of `skipped`, `running`, `succeeded`, `failed`.
- First converge of a cluster with no `status.init`: empty `spec.init_scripts` writes `{state: skipped, scripts_hash: init_scripts_hash([])}` and nothing else happens; a non-empty list writes `{state: running, started_at, scripts_hash: init_scripts_hash(spec.init_scripts), job: null}` and then creates the Job. Once `status.init` exists the runner never starts another Job for that cluster, whatever later edits do to `spec.init_scripts` (a cluster created with no scripts and edited later still never runs them; edits apply to the next cluster).
- Crash safety (pattern of `reconciler/checks.py`): the state is written before the create; `job` is set to the Job name only after the create succeeds. On a later tick with state `running`: Job absent and `job` null means create it (crashed between the write and the create); Job absent and `job` set means `failed`, reason `job_missing`; a Job without the cluster labels means `failed`, reason `foreign_object`; a create error means `failed`, reason `job_create_failed: <msg>` cut to 2000 chars.
- Outcome: Job Complete gives `succeeded`, exit 0; Job Failed gives `failed` with the container exit code; DeadlineExceeded or no outcome `DEADLINE_SECONDS + DEADLINE_GRACE_SECONDS` after `started_at` gives `failed`, reason `timeout`. `log_tail` is the pod log tail (200 lines, 16 KiB, the checks limits). `finished_at` is set. After recording the outcome the runner deletes the Job (background propagation).
- Job `agent-<slug>-init` (name helper in init.py, built with `k8s/labels.prefix`): the cluster labels plus `agents.szymonrichert.pl/init: "true"`; image `spec.image or settings.agent_image`; `restartPolicy: Never`, `backoffLimit: 0`, `activeDeadlineSeconds: 1800`, no `ttlSecondsAfterFinished`; `securityContext` runAsUser 1000 / fsGroup 1000; the cluster PVC with `workdir_mount(spec)` and `workingDir: workdir_path(spec)`; env from `spec.env`; resources as the agent container; `imagePullSecrets` when `settings.image_pull_secret` is set. Command `["sh", "-c", WRAPPER, "agent-init", INIT_SH]`, where INIT_SH is a header comment (cluster slug, "run once at cluster start by agent-orchestrator; edits through the init scripts API or the orchestrator_init_scripts_edit tool apply to the next cluster") followed by each script under a `# --- script <n> ---` line, and WRAPPER creates `$INIT_DIR` (`spec.INIT_DIR`), writes `.agent-init/.gitignore` containing `*`, writes `$1` to `.agent-init/init.sh`, runs it with `sh -eu` with stdout and stderr to `.agent-init/init.log`, prints the log and exits with the script's exit code. Files on the shared workdir (contract orch-init-workdir-files): `<workdir_path>/.agent-init/init.sh`, `init.log`, `.gitignore`.
- Gate: `_bootstrap_sessions` is skipped while `status.init` is absent or `running`; then phase is `pending` and the message carries `init running`. On `failed` sessions start, phase is `degraded` and the message carries `init failed` (with the exit code or reason). `skipped` and `succeeded` change nothing. The init Job pod is never an agent (`_observe` already ignores non-ordinal pod names; the test pins it).
- A converge never prunes the init Job; a discard deletes it (`DISCARD_ORDER` already deletes labelled Jobs; the test pins it).
- Reuse the checks helpers `_condition`, `_tail`, `_exit_code` and the limits constants by importing them from `reconciler/checks.py` (rename to public names there if ruff or clarity asks; keep checks behaviour unchanged).
- Docs: README `### Reconcile loop` gains the init step and states, README `## Data model` row for `clusters` mentions `status.init`; MEMORY.md dated 2026-10-24 entry: init scripts run once per cluster as a reconciler Job recorded in `status.init` (why: status has one writer that survives restarts; a pod marker races under Parallel pods), pod-local installs by a script do not reach agent pods (only the shared workdir is shared), failure starts sessions degraded instead of blocking.

Interfaces: `reconciler/init.py::InitRunner`, `reconciler/init.py::init_job_name`, `reconciler/init.py::render_init_job`; status shape above.

Steps: write `tests/test_init_runner.py` against `tests/fakes/fake_kube.py` (first tick creates once, second tick does not, skipped never runs after an edit, crash between write and create, job_missing, foreign_object, timeout, success and failure outcomes with log tail and exit code, Job deleted after the outcome, gate holds sessions while running and releases on failure, discard deletes the init Job) and see it fail; then implement.

#### Acceptance conditions

- AC1: a cluster with scripts gets exactly one Job agent-<slug>-init across repeated ticks, and status.init goes running then succeeded with exit_code 0, log_tail and finished_at [evidence: test:tests/test_init_runner.py::test_runs_once_and_records_success]
- AC2: a failed script records failed with the container exit code and log tail, sessions start, phase degraded and the message names init failed [evidence: test:tests/test_init_runner.py::test_failure_records_and_releases_sessions]
- AC3: a cluster first seen with no scripts records skipped and never creates a Job, also after its init_scripts are edited to a non-empty list [evidence: test:tests/test_init_runner.py::test_skipped_never_runs_after_edit]
- AC4: an edit after a run never starts a second Job [evidence: test:tests/test_init_runner.py::test_edit_after_run_never_reruns]
- AC5: a crash between the running write and the create creates the Job on the next tick; a vanished created Job records job_missing; an unlabelled Job records foreign_object; an overdue Job records timeout [evidence: test:tests/test_init_runner.py::test_crash_and_failure_reasons]
- AC6: no session is bootstrapped while init is absent or running, and phase is pending with init running in the message [evidence: test:tests/test_init_runner.py::test_sessions_held_while_running]
- AC7: the Job writes .agent-init/init.sh, init.log and a .gitignore of * in the workdir, runs as uid 1000 with the agent image, spec.env and the PVC mount [evidence: test:tests/test_init_runner.py::test_render_init_job]
- AC8: the init Job is deleted after its outcome is recorded, is not pruned by a converge, is deleted by a discard, and its pod never becomes an agent row [evidence: test:tests/test_init_runner.py::test_job_lifecycle_and_not_an_agent]
- AC9: existing reconciler and checks tests still pass [evidence: command:uv run pytest tests/test_reconciler.py tests/test_checks.py -q]
- AC10: README documents the init step and status.init, MEMORY.md has the dated decision [evidence: command:grep -q "status.init" README.md && grep -q "init" MEMORY.md && grep -q "2026-10-24" MEMORY.md]
- AC11: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/reconciler/init.py`
- `src/agent_orchestrator/reconciler/loop.py`
- `src/agent_orchestrator/reconciler/checks.py`
- `tests/test_init_runner.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

- `reconciler/init.py::InitRunner.step`, `init_job_name`, `render_init_job`.
- `clusters.status.init` shape (contract orch-cluster-status-init) and `<workdir>/.agent-init/` files (contract orch-init-workdir-files).

#### Expected outcome

A new cluster with scripts runs them once in one Job, records the outcome in `status.init`, and its agents get sessions after the run; edits, restarts and scaling never run them again.

#### Steps

- Red: write `tests/test_init_runner.py` on `tests/fakes/fake_kube.py`; `uv run pytest tests/test_init_runner.py -q` fails on the missing module.
- Green: implement `reconciler/init.py`, call it from `_converge` before `_bootstrap_sessions`, gate the bootstrap; run the verify command: all pass.
- Docs: README Reconcile loop and Data model, MEMORY.md dated entry.

#### Notes

- `_write_status` merges keys (`reconciler/loop.py:500-520`); write `{"init": {...}}` through it so the discard hook keys survive.
- `_observe` skips pods whose name suffix is not an ordinal (`loop.py:282`), so `agent-<slug>-init-xxxxx` never becomes an agent.
- `DISCARD_ORDER` already deletes labelled Jobs; `PRUNE_ORDER` has no Job, so converge never prunes it.

### S5: init scripts public api

- Status: done
- Files: `src/agent_orchestrator/db/clusters.py`, `src/agent_orchestrator/api/clusters.py`, `src/agent_orchestrator/api/schemas.py`, `tests/test_api_init_scripts.py`, `openapi.json`, `frontend/src/api/schema.d.ts`, `README.md`
- Verify: `uv run pytest tests/test_api_init_scripts.py tests/test_api_clusters.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: a38fbb6535ea1bfebfab92bfa3a8febcfb04bcbc

#### Requirement

Public, documented API to read and edit a cluster's init scripts, writing the cluster's stored spec AND its source preset (user decisions C3, X2; design D4, D5). Paths are in code/agent-orchestrator.

- `src/agent_orchestrator/db/clusters.py`: `set_init_scripts(conn, cluster_id, scripts) -> tuple[Cluster, bool]`. One transaction: lock the clusters row (`FOR UPDATE`), raise `ClusterNotFound` when absent; set `spec = jsonb_set(spec, '{init_scripts}', <list>)` with no `generation` bump; when `preset_id` is not null and that preset row exists, lock it (`FOR UPDATE`, clusters row first, then presets, always in that order) and set its sparse `spec.init_scripts` to the same list, bumping `presets.updated_at`; NOTIFY `cluster_changed` as the other clusters writes do. Returns the updated cluster and whether a preset was written. The Default preset is written like any other preset when it is the source (C3 to the letter). Writer stays the api process (README single-writer table unchanged; hive's README `## API` Versioning text already names `spec.init_scripts` as mutable in place, contract owned by hive; if that sentence is absent on main, add it).
- Shared api helpers in `src/agent_orchestrator/api/clusters.py`, used by these routes and by the agent routes (task init-scripts-agent-api): `init_scripts_view(conn, cluster, settings, preset_updated=False) -> schemas.InitScriptsView` and `edit_init_scripts(conn, cluster_id, scripts, settings) -> schemas.InitScriptsView`. Validation reuses the ClusterSpec field validator (422 `invalid_request` through the existing error shape); a cluster with `desired == deleting` is 409 `conflict`; unknown is 404 `not_found`.
- `src/agent_orchestrator/api/schemas.py`: `InitScriptsIn {scripts: list[str]}`; `InitStatus {state: Literal[skipped, running, succeeded, failed], scripts_hash, started_at, finished_at, exit_code, log_tail, reason}` (all but state and scripts_hash nullable); `InitScriptsView {cluster_id, scripts, preset_id, preset_name, status: InitStatus | None, edited_since_run: bool, script_path, log_path, preset_updated: bool}`. `edited_since_run` is true when `status.init` exists, its state is not `skipped`, and its `scripts_hash != init_scripts_hash(spec.init_scripts)`. `script_path` / `log_path` are `<workdir_path(spec)>/.agent-init/init.sh` and `init.log` built from `spec.INIT_DIR` and the workdir root constant (import the path helper without importing `k8s`: the api import boundary test `tests/test_api_clusters.py::test_api_never_imports_k8s_or_wrapper` must stay green, so compute from `spec.workdir` and a constant in spec.py or settings if `WORKDIR_ROOT` lives in k8s). `ClusterView` gains `init_edited_since_run: bool` with the same rule, so the list, get and status stream frames carry it.
- Routes: `GET /api/v1/clusters/{cluster_id}/init-scripts` -> 200 InitScriptsView; `PUT /api/v1/clusters/{cluster_id}/init-scripts` body InitScriptsIn -> 200 InitScriptsView with `preset_updated`. Behind the existing SourceAllowlist like every `/api/v1` route.
- README `## API`: one H3 per route (request, response, errors, the preset write-back, "the running cluster never re-runs; the next cluster from the preset runs the new list", no pod roll); regenerate `openapi.json` and `frontend/src/api/schema.d.ts`.

Interfaces: `db/clusters.py::set_init_scripts`, `api/clusters.py::init_scripts_view`, `api/clusters.py::edit_init_scripts`, `api/schemas.py::InitScriptsView`, `api/schemas.py::InitStatus` (contract orch-cluster-init-scripts-api).

Steps: write `tests/test_api_init_scripts.py` first (repo function and both routes), see it fail, implement.

#### Acceptance conditions

- AC1: PUT writes the cluster spec and the source preset in one transaction, returns preset_updated true, and generation is unchanged [evidence: test:tests/test_api_init_scripts.py::test_put_writes_cluster_and_preset]
- AC2: PUT on a cluster whose preset was deleted or that was created from a raw spec writes only the cluster and returns preset_updated false [evidence: test:tests/test_api_init_scripts.py::test_put_without_preset]
- AC3: a cluster created from the Default preset writes the Default preset's init_scripts [evidence: test:tests/test_api_init_scripts.py::test_put_writes_default_preset]
- AC4: GET returns scripts, preset, status from status.init, script_path and log_path under the workdir, and edited_since_run true only after an edit following a run [evidence: test:tests/test_api_init_scripts.py::test_get_view_and_edited_since_run]
- AC5: an invalid list is 422 invalid_request, an unknown cluster 404 not_found, a deleting cluster 409 conflict, and nothing is written [evidence: test:tests/test_api_init_scripts.py::test_put_errors]
- AC6: ClusterView carries init_edited_since_run in the list, get and stream snapshot [evidence: test:tests/test_api_init_scripts.py::test_cluster_view_edited_flag]
- AC7: the api still imports neither k8s nor the wrapper [evidence: test:tests/test_api_clusters.py::test_api_never_imports_k8s_or_wrapper]
- AC8: README documents both routes and openapi.json and schema.d.ts match [evidence: command:uv run pytest tests/test_readme_api.py -q]
- AC9: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/db/clusters.py`
- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/api/schemas.py`
- `tests/test_api_init_scripts.py`
- `openapi.json`
- `frontend/src/api/schema.d.ts`
- `README.md`

#### Interfaces

- `db/clusters.py::set_init_scripts`, `api/clusters.py::init_scripts_view`, `api/clusters.py::edit_init_scripts`, `api/schemas.py::InitScriptsIn`, `InitStatus`, `InitScriptsView`, `ClusterView.init_edited_since_run` (contract orch-cluster-init-scripts-api).

#### Expected outcome

`GET|PUT /api/v1/clusters/{id}/init-scripts` work and are documented; a PUT updates the cluster and its preset in one transaction with no pod roll.

#### Steps

- Red: write `tests/test_api_init_scripts.py`; `uv run pytest tests/test_api_init_scripts.py -q` fails with 404 on the routes.
- Green: repo function, helpers, schemas, routes; regenerate openapi.json and schema.d.ts; README H3s; run the verify command: all pass.

#### Notes

- The clusters single-writer is the api process; `presets` too. Lock clusters then presets in every path that takes both.
- `preset_id` is null after the preset was deleted (`ON DELETE SET NULL`).

### S6: fe cluster init dialog

- Status: done
- Files: `frontend/src/clusters/InitScriptsDialog.tsx`, `frontend/src/clusters/InitScriptsDialog.test.tsx`, `frontend/src/layout/TopBar.tsx`, `frontend/src/layout/TopBar.test.tsx`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`
- Verify: `cd frontend && npx vitest run src/clusters/InitScriptsDialog.test.tsx src/layout/TopBar.test.tsx && npm run lint`
- Verified head: ec7dd9a246cbbb48a196977ad22b94200661ff87

#### Requirement

A cluster-level "Init scripts" dialog in the UI: see how the cluster was initialised and edit the scripts for the next cluster (user decisions C2, C3, X2; design D5). Paths are in code/agent-orchestrator/frontend. Reads and writes only the public routes from task init-scripts-public-api (`GET|PUT /api/v1/clusters/{id}/init-scripts`); the generated schema already has `InitScriptsView`.

- `src/api/client.ts`: `getInitScripts(clusterId)` and `putInitScripts(clusterId, scripts)` typed from the schema, using the existing request helper and error type.
- `src/clusters/InitScriptsDialog.tsx`: opened with a ClusterView; loads the view; shows the run state (`skipped`, `running`, `succeeded`, `failed` with exit code or reason), started and finished times, the log tail in a monospace scroll box, `script_path`, and a note when `edited_since_run`; edits the scripts with the same row editor behaviour and validation as the preset form (reuse the validation from `clusterSpecForm.ts`, do not duplicate it); Save PUTs and then shows "Saved. Applies to the next cluster" plus "Preset <name> updated" when `preset_updated`; server errors show in an Alert. Theme tokens only.
- `src/layout/TopBar.tsx`: the cluster actions menu gains an `Init scripts` item before `Discard`, calling a new `onInitScripts(cluster)` prop; `src/App.tsx` holds the open-dialog state and renders the dialog like `DiscardClusterDialog`.
- Tests: `src/clusters/InitScriptsDialog.test.tsx` (each state rendered, edit and save body, preset_updated message, error Alert) and `src/layout/TopBar.test.tsx` (menu item calls the prop).

Interfaces: `client.ts::getInitScripts`, `client.ts::putInitScripts`, `TopBarProps.onInitScripts`.

Steps: write both tests first, see them fail, implement; then `npm run build`.

#### Acceptance conditions

- AC1: the dialog renders skipped, running, succeeded and failed states with exit code, log tail, script path and the edited-since-run note [evidence: command:cd frontend && npx vitest run src/clusters/InitScriptsDialog.test.tsx -t "states"]
- AC2: saving PUTs the edited scripts and shows the next-cluster and preset-updated messages; a server error shows an Alert [evidence: command:cd frontend && npx vitest run src/clusters/InitScriptsDialog.test.tsx -t "save"]
- AC3: the TopBar cluster menu has Init scripts before Discard and it calls onInitScripts with the cluster [evidence: command:cd frontend && npx vitest run src/layout/TopBar.test.tsx -t "init scripts"]
- AC4: lint, typecheck build and design rules pass [evidence: command:cd frontend && npm run lint && npm run build && npx vitest run src/layout/designRules.test.ts]

#### Files

- `frontend/src/clusters/InitScriptsDialog.tsx`
- `frontend/src/clusters/InitScriptsDialog.test.tsx`
- `frontend/src/layout/TopBar.tsx`
- `frontend/src/layout/TopBar.test.tsx`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`

#### Interfaces

- `frontend/src/api/client.ts::getInitScripts`, `putInitScripts`; `TopBarProps.onInitScripts`; `InitScriptsDialog`.

#### Expected outcome

The cluster menu opens an Init scripts dialog that shows the run and saves edited scripts for the next cluster.

#### Steps

- Red: write `InitScriptsDialog.test.tsx` and the TopBar test; `cd frontend && npx vitest run src/clusters/InitScriptsDialog.test.tsx src/layout/TopBar.test.tsx` fails.
- Green: client functions, dialog, menu item, App wiring; run the verify command, then `npm run build`.

#### Notes

- Mirror `DiscardClusterDialog` for open state in `App.tsx`.

### S7: init scripts agent api

- Status: done
- Files: `src/agent_orchestrator/api/agent.py`, `tests/test_agent_init_scripts.py`, `README.md`
- Verify: `uv run pytest tests/test_agent_init_scripts.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 1bf5c9636de7f32da8e68faf1291b0622da5386b

#### Requirement

Agent-facing init scripts routes, so an agent knows how its cluster was initialised and can edit the scripts for the next cluster (user decisions C2, C3, X1; design D3, D4, D6). Paths are in code/agent-orchestrator. Builds on hive F4 (`src/agent_orchestrator/api/agent.py`, dependency `require_agent()` returning the caller's Agent row from the cluster bearer token, `X-Orch-Cluster` and caller IP = `agents.pod_ip`; contracts of hive-mode-leadership-handove) and on task init-scripts-public-api.

- In `src/agent_orchestrator/api/agent.py` add `GET /agent/v1/init-scripts` -> 200 InitScriptsView of the caller's cluster, and `PUT /agent/v1/init-scripts` body InitScriptsIn -> 200 InitScriptsView with `preset_updated`. Both use `require_agent()` and the shared helpers `init_scripts_view` / `edit_init_scripts` from `api/clusters.py`; no other logic, no new auth. The cluster is always the token's cluster (the agent cannot name another). Errors as the public routes (422 `invalid_request`, 409 `conflict` when deleting) plus the F4 auth errors (401, 403 `forbidden`).
- Any agent of the cluster may call both (subagents are already refused by the wrapper `claude.main_agent_only_tools` gate rendered by hive F3).
- These are the routes the hive F1 plugin tools `orchestrator_init_scripts_get` and `orchestrator_init_scripts_edit` call (contract orch-agent-init-scripts-api, request and response shape fixed there). Add a parity test that runs the real `any_mcp.orchestrator:OrchestratorPlugin` (the any-mcp version the orchestrator pins after F3) through `any_mcp.testing` against this app: `init_scripts_get` returns the scripts and status, `init_scripts_edit` writes cluster and preset, and the `init_scripts_get` description names `.agent-init/init.sh` and that edits apply to the next cluster. If the harness cannot route the plugin's HTTP client to the ASGI app, serve the agent app with uvicorn on 127.0.0.1 and an ephemeral port, with an agents row whose `pod_ip` is 127.0.0.1. If the plugin's description or payload disagrees with the contract, record a `discovered` entry naming hive F1 and the mismatch; do not change any-mcp in this task.
- Document both routes the way F4 documents `/agent/v1/me` (README `## Agent API`, and the agent OpenAPI document if F4 publishes one), so `tests/test_readme_api.py` passes.

Interfaces: `api/agent.py` routes `GET|PUT /agent/v1/init-scripts`.

Steps: write `tests/test_agent_init_scripts.py` (auth reuse: no token 401, other cluster's token 403, IP not an agent 403; GET; PUT writes cluster and preset; plugin parity) first, see it fail, implement.

#### Acceptance conditions

- AC1: an agent of the cluster reads its cluster's scripts, status and file paths through GET /agent/v1/init-scripts [evidence: test:tests/test_agent_init_scripts.py::test_agent_get_init_scripts]
- AC2: PUT /agent/v1/init-scripts writes the cluster spec and its source preset and returns preset_updated, with no generation bump [evidence: test:tests/test_agent_init_scripts.py::test_agent_put_writes_cluster_and_preset]
- AC3: no token is 401, another cluster's token or a caller IP that is not a live agent of the cluster is 403 forbidden, and nothing is written [evidence: test:tests/test_agent_init_scripts.py::test_agent_init_scripts_auth]
- AC4: the pinned OrchestratorPlugin init_scripts_get and init_scripts_edit tools work against these routes and the get description names .agent-init/init.sh and next-cluster semantics [evidence: test:tests/test_agent_init_scripts.py::test_plugin_parity]
- AC5: both routes are documented and the README contract test passes [evidence: command:uv run pytest tests/test_readme_api.py -q]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/api/agent.py`
- `tests/test_agent_init_scripts.py`
- `README.md`

#### Interfaces

- `api/agent.py` routes `GET|PUT /agent/v1/init-scripts` (contract orch-agent-init-scripts-api), using hive `require_agent()` and `api/clusters.py::init_scripts_view` / `edit_init_scripts`.

#### Expected outcome

An agent pod reads and edits its cluster's init scripts over the agent socket, and the pinned plugin tools work against these routes.

#### Steps

- Red: write `tests/test_agent_init_scripts.py`; `uv run pytest tests/test_agent_init_scripts.py -q` fails with 404.
- Green: add both routes; document them like `/agent/v1/me`; run the verify command: all pass.

#### Notes

- Follow the test fixtures hive F4 added for `/agent/v1/me` (agent client with token, cluster header and caller IP).

### S8: init scripts kind e2e

- Status: done
- Files: `tests/e2e/test_e2e_kind.py`
- Verify: `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 39a5210d6cc3074d957eabc547aca6215c48560f

#### Requirement

API-only kind e2e for init scripts (user decisions X2, C1, C2, C3; design D8). Path: code/agent-orchestrator/tests/e2e/test_e2e_kind.py. Every step goes through the public API or, for the agent routes, `kubectl exec` into `agent-<slug>-0` with `$ORCH_AGENT_URL` and `$ORCH_AGENT_TOKEN` from the pod env (the pattern of hive's `test_agent_api_identity`; the fake claude cannot call MCP tools).

Tests (each deletes every cluster and preset it creates in its teardown; the Default preset is never edited):
- `test_init_scripts_run_once`: create a preset with `init_scripts: ["echo e2e-init > e2e-init.txt"]`, schedule a 2-replica cluster from it; poll the cluster until `status.init.state == "succeeded"` and every agent has a session; `kubectl exec` in each pod shows `<workdir>/e2e-init.txt` and `.agent-init/init.sh` and `.agent-init/init.log`; there is exactly one Job pod history for `agent-<slug>-init` (the Job is gone after the outcome, so assert status.init.started_at is stable over two reconcile intervals and no `agent-<slug>-init` Job exists).
- `test_init_scripts_edit_writes_cluster_and_preset_without_roll`: PUT `/api/v1/clusters/{id}/init-scripts` with a new list; GET shows it with `edited_since_run: true`; the preset GET shows the new list; agent pod UIDs and `status.init.started_at` are unchanged after two reconcile intervals; then the same through the agent route from inside the pod (`curl -X PUT $ORCH_AGENT_URL/agent/v1/init-scripts -H "Authorization: Bearer $ORCH_AGENT_TOKEN" -H "X-Orch-Cluster: $ORCH_CLUSTER_ID"`), and a GET from the pod returns it.
- `test_init_scripts_failure_starts_sessions_degraded`: a raw-spec cluster with `init_scripts: ["exit 3"]` reaches `status.init.state == "failed"`, `exit_code == 3`, phase `degraded` with `init failed` in the message, and its agent still gets a session.
- `test_cluster_without_init_scripts_skipped`: the shared 1-replica `cluster` fixture shows `status.init.state == "skipped"`.

Kind e2e cannot run inside the task container; verification is collection and lint here, and the PR CI e2e job (or `mise run test:e2e`) runs it.

#### Acceptance conditions

- AC1: the four init e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py -k "init_scripts"]
- AC2: the tests cover run once with files in every pod, edit through the public and the agent route writing cluster and preset with no pod roll and no re-run, failure starting sessions degraded, and skipped, through the API and kubectl exec only [evidence: judgement:tests/e2e/test_e2e_kind.py reviewed against the requirement; executed by the PR CI e2e job]
- AC3: every cluster and preset a new test creates is deleted in its teardown and the Default preset is never edited [evidence: judgement:teardown reviewed]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `tests/e2e/test_e2e_kind.py`

#### Interfaces

- Public routes `GET|PUT /api/v1/clusters/{id}/init-scripts`, agent routes `GET|PUT /agent/v1/init-scripts`, `status.init`.

#### Expected outcome

Four API-only e2e tests cover run once, edit without roll or re-run, failure and skipped; they are collected locally and run in PR CI.

#### Steps

- Add the four tests and their teardown; run `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py -k init_scripts`: four tests listed.
- Run the verify command: collection and lint pass.

#### Ruling

- 2026-10-25 accepted: test-only deliverable (the e2e test is the change); TDD red not applicable to a pure test file; the test is run for real against kind in phase 5

#### Notes

- Check `e2e/values-kind.yaml` `ORCH_MAX_CLUSTERS` against the extra clusters; raise it there only if needed (that file then joins this task's diff).
- Kind e2e cannot run in the task container; verified by collection and lint, run by the PR CI e2e job.

### S9: deploy pin init scripts

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agent-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster" && uv run ruff check . && uv run ruff format --check .`
- Verified head: f161544b29e6212610ab174496076d93f64fc477

#### Requirement

Pin agents-helmfile to the agent-orchestrator build that contains this epic (design D7; precedent docs/plans/done/cluster-presets/tasks/deploy-pin-presets.md). Paths are in code/agents-helmfile.

Release path: this epic changes no chart version and no any-mcp or wrapper pin (hive owns those bumps). The release is the merge of this epic's agent-orchestrator PR to main, after which CI publishes chart `0.1.0-main.<sha7>` and image `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>`. Precondition, checked first: `git -C ../agent-orchestrator fetch origin main` and the main commit that merges this epic exists and `docker manifest inspect harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` (or `helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator --version 0.1.0-main.<sha7>`) succeeds. The orchestrator writes `<sha7>` into this task with `ticket.py amend` once the PR merges; if the merge or the published artifacts do not exist yet, end `blocked` with whoCanClear "orchestrator: merge the agent-orchestrator PR of agent-init-scripts and wait for its main CI".

- `helmfile.yaml.gotmpl`: release `agent-orchestrator` chart version `0.1.0-main.<sha7>`.
- `values/agent-orchestrator/common.yaml`: `image.tag` `<sha7>`. Wrapper image pins, any-mcp settings, ORCH_ALLOWED_ORIGINS and ingress settings stay as they are.
- `tests/test_orchestrator_release.py`: `test_orchestrator_pin_matches_image` asserts the chart version and the image tag both carry `<sha7>`, reading the files as text (runs offline).

#### Acceptance conditions

- AC1: chart version and image tag agree on the orchestrator merge sha and the test runs offline [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the pinned chart version and image exist in Harbor [evidence: judgement:the task notes quote the helm show chart or docker manifest inspect output for the pinned sha]
- AC3: only the orchestrator chart version and image tag change [evidence: judgement:the task diff reviewed against the requirement]
- AC4: the offline release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster" && uv run ruff check . && uv run ruff format --check .]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

- Consumes the published chart `oci://harbor.szymonrichert.pl/charts/agent-orchestrator` `0.1.0-main.<sha7>` and image `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` (contracts agent-orchestrator-chart, agent-orchestrator-image).

#### Expected outcome

`helmfile diff` shows only the agent-orchestrator chart version and image tag changing to this epic's merge.

#### Steps

- Check the precondition (merge commit and published artifacts); otherwise end blocked as the requirement says.
- Red: update the pin test to the new sha; it fails on the old pins.
- Green: bump the chart version and image tag; run the verify command: pass.

#### Notes

- cluster-scaling and hive pin the same two lines; take the sha of the latest orchestrator main merge that contains this epic.

### S10: apply smoke init scripts

- Status: done
- Files: `MEMORY.md`
- Verify: `mise run diff && mise run smoke`
- Verified head: f161544b29e6212610ab174496076d93f64fc477

#### Requirement

Apply the pinned release to the live `agents` namespace and prove it with the smoke (design D7; user-approved scope: releases, bumps and helmfile apply plus smoke are tasks of this epic). Paths are in code/agents-helmfile. Runs only after tasks deploy-pin-init-scripts and smoke-init-scripts are done.

- `mise run diff` first and keep its output in the task notes (expected change: the agent-orchestrator chart version and image tag only; anything else stops the task as `blocked` with the diff, whoCanClear "user").
- `mise run apply` (it runs lint, test and the kube-context guard first; never bypass the guard or set EXPECTED_KUBE_CONTEXT).
- `mise run diff` again: exit 0 (no drift).
- `mise run smoke`: exit 0, including the init scripts check.
- `MEMORY.md`: a dated 2026-10-24 line: applied agent-orchestrator `0.1.0-main.<sha7>` with init scripts, smoke green (quote the smoke's last log line).
- No other file changes. A failing apply is not retried blindly: read the helm error, report it with its tail.

#### Acceptance conditions

- AC1: the live namespace has no drift from the pinned helmfile after the apply [evidence: command:mise run diff]
- AC2: the smoke passes against the live orchestrator, including the init scripts check [evidence: command:mise run smoke]
- AC3: MEMORY.md records the applied version and the smoke result [evidence: command:grep -q "0.1.0-main" MEMORY.md && grep -q "init scripts" MEMORY.md]
- AC4: the pre-apply diff showed only the orchestrator chart version and image tag changing [evidence: judgement:the diff output quoted in the task notes]

#### Files

- `MEMORY.md`

#### Interfaces

- `mise run diff|apply|smoke` in code/agents-helmfile.

#### Expected outcome

The live agents namespace runs the pinned build and the smoke, including the init scripts check, is green.

#### Steps

- `mise run diff`: only the orchestrator chart version and image tag change (exit 2 means changes; quote the output).
- `mise run apply`: exits 0.
- `mise run diff`: exits 0.
- `mise run smoke`: exits 0; quote its last log line into MEMORY.md and the task notes.

#### Ruling

- 2026-10-25 accepted: applied by the orchestrator after user allowed mise run apply: helm rev 11 chart 0.1.0-main.22cf283; post-apply diff 'No affected releases'; mise run smoke 'smoke: OK' incl init scripts succeeded; MEMORY via agents-helmfile PR #15 merged

- 2026-10-25 accepted: applied live by orchestrator after user approval; diff clean, smoke OK, MEMORY PR #15 merged

#### Notes

- No TDD cycle applies: this task runs an apply and writes one MEMORY.md line (doc edit exception).
- Never bypass the kube-context guard.

- 2026-10-25 run agent-init-scripts: dependency-failed on deploy-pin-init-scripts

Pre-apply diff (orchestrator, 2026-10-25, `mise run diff`): `helm.sh/chart: agent-orchestrator-0.1.0-main.22cf283`, `app.kubernetes.io/version "a5b5a75" -> "22cf283"`, `agents, agent-orchestrator-settings, ConfigMap (v1) has changed` (derived checksum), `Affected releases are: agent-orchestrator UPDATED`. Post-apply `mise run diff`: `No affected releases`. Smoke last line: `smoke: OK`.

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none

## Rulings (migrated)

- init-scripts-kind-e2e: accept true, at 2026-10-25T06:35:04Z: test-only deliverable (the e2e test is the change); TDD red not applicable to a pure test file; the test is run for real against kind in phase 5
- apply-smoke-init-scripts: accept true, at 2026-10-25T07:40:31Z: applied by the orchestrator after user allowed mise run apply: helm rev 11 chart 0.1.0-main.22cf283; post-apply diff 'No affected releases'; mise run smoke 'smoke: OK' incl init scripts succeeded; MEMORY via agents-helmfile PR #15 merged
- apply-smoke-init-scripts: accept true, at 2026-10-25T07:40:38Z: applied live by orchestrator after user approval; diff clean, smoke OK, MEMORY PR #15 merged
