---
title: init scripts public api
status: todo
repo: agent-orchestrator
value: "people and scripts can read a cluster's init run and edit its scripts for the next cluster through the documented API"
files: [src/agent_orchestrator/db/clusters.py, src/agent_orchestrator/api/clusters.py, src/agent_orchestrator/api/schemas.py, tests/test_api_init_scripts.py, openapi.json, frontend/src/api/schema.d.ts, README.md]
verify: "uv run pytest tests/test_api_init_scripts.py tests/test_api_clusters.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [init-scripts-spec-field]
owns: [orch-cluster-init-scripts-api]
uses: [orch-cluster-spec-init-scripts, orch-spec-runtime-mutable]
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

# init scripts public api

## Requirement

Public, documented API to read and edit a cluster's init scripts, writing the cluster's stored spec AND its source preset (user decisions C3, X2; design D4, D5). Paths are in code/agent-orchestrator.

- `src/agent_orchestrator/db/clusters.py`: `set_init_scripts(conn, cluster_id, scripts) -> tuple[Cluster, bool]`. One transaction: lock the clusters row (`FOR UPDATE`), raise `ClusterNotFound` when absent; set `spec = jsonb_set(spec, '{init_scripts}', <list>)` with no `generation` bump; when `preset_id` is not null and that preset row exists, lock it (`FOR UPDATE`, clusters row first, then presets, always in that order) and set its sparse `spec.init_scripts` to the same list, bumping `presets.updated_at`; NOTIFY `cluster_changed` as the other clusters writes do. Returns the updated cluster and whether a preset was written. The Default preset is written like any other preset when it is the source (C3 to the letter). Writer stays the api process (README single-writer table unchanged; hive's README `## API` Versioning text already names `spec.init_scripts` as mutable in place, contract owned by hive; if that sentence is absent on main, add it).
- Shared api helpers in `src/agent_orchestrator/api/clusters.py`, used by these routes and by the agent routes (task init-scripts-agent-api): `init_scripts_view(conn, cluster, settings, preset_updated=False) -> schemas.InitScriptsView` and `edit_init_scripts(conn, cluster_id, scripts, settings) -> schemas.InitScriptsView`. Validation reuses the ClusterSpec field validator (422 `invalid_request` through the existing error shape); a cluster with `desired == deleting` is 409 `conflict`; unknown is 404 `not_found`.
- `src/agent_orchestrator/api/schemas.py`: `InitScriptsIn {scripts: list[str]}`; `InitStatus {state: Literal[skipped, running, succeeded, failed], scripts_hash, started_at, finished_at, exit_code, log_tail, reason}` (all but state and scripts_hash nullable); `InitScriptsView {cluster_id, scripts, preset_id, preset_name, status: InitStatus | None, edited_since_run: bool, script_path, log_path, preset_updated: bool}`. `edited_since_run` is true when `status.init` exists, its state is not `skipped`, and its `scripts_hash != init_scripts_hash(spec.init_scripts)`. `script_path` / `log_path` are `<workdir_path(spec)>/.agent-init/init.sh` and `init.log` built from `spec.INIT_DIR` and the workdir root constant (import the path helper without importing `k8s`: the api import boundary test `tests/test_api_clusters.py::test_api_never_imports_k8s_or_wrapper` must stay green, so compute from `spec.workdir` and a constant in spec.py or settings if `WORKDIR_ROOT` lives in k8s). `ClusterView` gains `init_edited_since_run: bool` with the same rule, so the list, get and status stream frames carry it.
- Routes: `GET /api/v1/clusters/{cluster_id}/init-scripts` -> 200 InitScriptsView; `PUT /api/v1/clusters/{cluster_id}/init-scripts` body InitScriptsIn -> 200 InitScriptsView with `preset_updated`. Behind the existing SourceAllowlist like every `/api/v1` route.
- README `## API`: one H3 per route (request, response, errors, the preset write-back, "the running cluster never re-runs; the next cluster from the preset runs the new list", no pod roll); regenerate `openapi.json` and `frontend/src/api/schema.d.ts`.

Interfaces: `db/clusters.py::set_init_scripts`, `api/clusters.py::init_scripts_view`, `api/clusters.py::edit_init_scripts`, `api/schemas.py::InitScriptsView`, `api/schemas.py::InitStatus` (contract orch-cluster-init-scripts-api).

Steps: write `tests/test_api_init_scripts.py` first (repo function and both routes), see it fail, implement.

## Acceptance conditions

- AC1: PUT writes the cluster spec and the source preset in one transaction, returns preset_updated true, and generation is unchanged [evidence: test:tests/test_api_init_scripts.py::test_put_writes_cluster_and_preset]
- AC2: PUT on a cluster whose preset was deleted or that was created from a raw spec writes only the cluster and returns preset_updated false [evidence: test:tests/test_api_init_scripts.py::test_put_without_preset]
- AC3: a cluster created from the Default preset writes the Default preset's init_scripts [evidence: test:tests/test_api_init_scripts.py::test_put_writes_default_preset]
- AC4: GET returns scripts, preset, status from status.init, script_path and log_path under the workdir, and edited_since_run true only after an edit following a run [evidence: test:tests/test_api_init_scripts.py::test_get_view_and_edited_since_run]
- AC5: an invalid list is 422 invalid_request, an unknown cluster 404 not_found, a deleting cluster 409 conflict, and nothing is written [evidence: test:tests/test_api_init_scripts.py::test_put_errors]
- AC6: ClusterView carries init_edited_since_run in the list, get and stream snapshot [evidence: test:tests/test_api_init_scripts.py::test_cluster_view_edited_flag]
- AC7: the api still imports neither k8s nor the wrapper [evidence: test:tests/test_api_clusters.py::test_api_never_imports_k8s_or_wrapper]
- AC8: README documents both routes and openapi.json and schema.d.ts match [evidence: command:uv run pytest tests/test_readme_api.py -q]
- AC9: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/db/clusters.py`
- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/api/schemas.py`
- `tests/test_api_init_scripts.py`
- `openapi.json`
- `frontend/src/api/schema.d.ts`
- `README.md`

## Interfaces

- `db/clusters.py::set_init_scripts`, `api/clusters.py::init_scripts_view`, `api/clusters.py::edit_init_scripts`, `api/schemas.py::InitScriptsIn`, `InitStatus`, `InitScriptsView`, `ClusterView.init_edited_since_run` (contract orch-cluster-init-scripts-api).

## Expected outcome

`GET|PUT /api/v1/clusters/{id}/init-scripts` work and are documented; a PUT updates the cluster and its preset in one transaction with no pod roll.

## Steps

- Red: write `tests/test_api_init_scripts.py`; `uv run pytest tests/test_api_init_scripts.py -q` fails with 404 on the routes.
- Green: repo function, helpers, schemas, routes; regenerate openapi.json and schema.d.ts; README H3s; run the verify command: all pass.

## Notes

- The clusters single-writer is the api process; `presets` too. Lock clusters then presets in every path that takes both.
- `preset_id` is null after the preset was deleted (`ON DELETE SET NULL`).
