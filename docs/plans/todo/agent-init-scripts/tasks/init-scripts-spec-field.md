---
title: init scripts spec field
status: todo
repo: agent-orchestrator
value: clusters and presets can carry init scripts that never roll pods
files: [src/agent_orchestrator/spec.py, tests/test_spec_init_scripts.py, tests/test_render.py, openapi.json, frontend/src/api/schema.d.ts, README.md]
verify: "uv run pytest tests/test_spec_init_scripts.py tests/test_render.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [orch-cluster-spec-init-scripts]
uses: []
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

# init scripts spec field

## Requirement

Add init scripts to ClusterSpec, and so to presets (user decision C1; design D1). Paths are in code/agent-orchestrator. Precondition: the hive-mode-leadership-handove foundation tasks (F3 spec/render, F4 agent API) are on main; this task builds on that code.

- `src/agent_orchestrator/spec.py`: `ClusterSpec.init_scripts: list[str] = []`. Field validator: at most 20 entries; each entry is a string that is non-empty after strip and at most 16384 characters; the message names the offending index. `extra="forbid"` stays. Add the module constant `INIT_DIR = ".agent-init"` and `init_scripts_hash(scripts: list[str]) -> str` = sha256 hex of `json.dumps(scripts, separators=(",", ":"))` (defined for the empty list too). These two are the only shared definitions the reconciler, the api and the views use for the directory and the hash.
- Render: `init_scripts` never reaches any rendered object (ConfigMap, Secret, Service, PVC, StatefulSet template). Extend the hive hash pin test `tests/test_render.py::test_runtime_fields_change_only_statefulset_replicas` (contract "Hash invariant", owned by hive) so two specs that differ only in `init_scripts` render byte-identical objects, StatefulSet included. If that test does not exist under that name on main, add `test_init_scripts_never_rendered` in the same file with the same assertion.
- Presets: a preset POST/PUT body carrying `init_scripts` stores it sparse (only when set, as the existing `exclude_unset` dump does) and rejects an invalid list with 422 `invalid_request`; creating a cluster from a preset snapshots `init_scripts` into the cluster spec (the existing `_create_from_preset` path; no code change expected there, the test pins it).
- Docs and generated files: document the field (limits, run once per cluster, edits apply to the next cluster, never rendered into pods) where README.md documents ClusterSpec fields; regenerate `openapi.json` (`uv run python -m agent_orchestrator.api.openapi > openapi.json`) and `frontend/src/api/schema.d.ts` (`npm --prefix frontend run gen:api`) so `tests/test_readme_api.py` passes.

Interfaces: `spec.py::ClusterSpec.init_scripts`, `spec.py::INIT_DIR`, `spec.py::init_scripts_hash` (contract orch-cluster-spec-init-scripts).

Steps: write `tests/test_spec_init_scripts.py` (model limits, hash, preset round trip through the API client fixture, create-from-preset snapshot) and the render pin first, see them fail, then add the field.

## Acceptance conditions

- AC1: ClusterSpec accepts up to 20 non-empty scripts of at most 16384 characters and rejects an empty entry, a 21st entry and an oversize entry with a message naming the index [evidence: test:tests/test_spec_init_scripts.py::test_init_scripts_limits]
- AC2: init_scripts_hash is the sha256 of the compact JSON list and differs when any script changes [evidence: test:tests/test_spec_init_scripts.py::test_init_scripts_hash]
- AC3: two specs that differ only in init_scripts render byte-identical objects [evidence: command:uv run pytest tests/test_render.py -q -k "runtime_fields_change_only_statefulset_replicas or init_scripts_never_rendered"]
- AC4: a preset created and updated with init_scripts returns them sparse, an invalid list is 422 invalid_request [evidence: test:tests/test_spec_init_scripts.py::test_preset_round_trips_init_scripts]
- AC5: a cluster created from a preset carries the preset's init_scripts in its spec [evidence: test:tests/test_spec_init_scripts.py::test_cluster_from_preset_snapshots_init_scripts]
- AC6: README documents the field and openapi.json and schema.d.ts match the code [evidence: command:uv run pytest tests/test_readme_api.py -q]
- AC7: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/spec.py`
- `tests/test_spec_init_scripts.py`
- `tests/test_render.py`
- `openapi.json`
- `frontend/src/api/schema.d.ts`
- `README.md`

## Interfaces

- `src/agent_orchestrator/spec.py::ClusterSpec.init_scripts`, `spec.py::INIT_DIR`, `spec.py::init_scripts_hash` (contract orch-cluster-spec-init-scripts).
- Keeps the hive hash invariant test green and extends it to `init_scripts`.

## Expected outcome

A preset or cluster spec carries `init_scripts`; nothing rendered for pods changes with it; README, openapi.json and schema.d.ts describe it.

## Steps

- Red: write `tests/test_spec_init_scripts.py` and the render pin; `uv run pytest tests/test_spec_init_scripts.py tests/test_render.py -q` fails on the missing field.
- Green: add the field, constant and hash helper; regenerate openapi.json and schema.d.ts; document in README; run the verify command: all pass.

## Notes

- Presets dump `exclude_unset` (`api/presets.py:42-54`), so an unset `init_scripts` stays absent from the stored preset.
- `extra="forbid"` means older orchestrator builds reject a spec with the field; this build only moves forward.
