---
title: spec cap static
status: in-progress
repo: agent-orchestrator
value: "a cluster declares its replica cap and whether it may scale, and hive mode follows from it"
files: [src/agent_orchestrator/spec.py, tests/test_spec_hive.py, README.md, openapi.json, frontend/src/api/schema.d.ts]
verify: "uv run pytest tests/test_spec_hive.py tests/test_api_clusters.py tests/test_api_presets.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [orch-spec-cap-static]
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/hive-mode-leadership-handove-spec-cap-static/agent-orchestrator
branch: hive-mode-leadership-handove-spec-cap-static
verified_head: ""
run: ""
provides: []
---

# spec cap static

## Requirement

Foundation part F3, spec fields (Q8, Q12, S2, S3 vocabulary owned here). In `src/agent_orchestrator/spec.py`:

- `ClusterSpec.max_replicas: int | None = None`, resolved to `replicas` when unset (model validator); a stored spec without the key loads as `max_replicas == replicas`.
- `ClusterSpec.static: bool = False`.
- Derived properties: `hive = max_replicas > 1` (every multi-agent-capable cluster is a hive, no switch), `alone = not hive`, `scalable = hive and not static`. The default preset `{"replicas": 1}` stays alone: no behaviour change.
- Model validation: `1 <= replicas <= max_replicas <= 16`; `static` requires `max_replicas == replicas`.
- `validate_spec`: `max_replicas <= settings.max_replicas` (422 `invalid_request` naming the field); an `any_mcp_config.plugins` entry named `orchestrator` or with namespace `orchestrator` is rejected (reserved for the rendered plugin).
- Presets stay sparse: a preset that does not set `max_replicas` or `static` stores neither (`exclude_unset`).
- README `## API` ClusterSpec field list documents both fields and the derived hive rule; `openapi.json` and `frontend/src/api/schema.d.ts` regenerated (`tests/test_readme_api.py` drift checks).
- Interrogate item 7: the in-memory fallback (a stored spec without the key loads as `max_replicas == replicas`) stays only as a defence; the migration-0003-hive backfill writes the key into stored specs, so editing `replicas` in place later never moves the cap.

## Acceptance conditions

- AC1: max_replicas defaults to replicas, including for a stored spec without the key [evidence: test:tests/test_spec_hive.py::test_max_replicas_defaults_to_replicas]
- AC2: replicas above max_replicas, max_replicas above 16 or above settings.max_replicas are rejected [evidence: test:tests/test_spec_hive.py::test_cap_bounds]
- AC3: static with max_replicas different from replicas is rejected [evidence: test:tests/test_spec_hive.py::test_static_requires_fixed_size]
- AC4: hive, alone and scalable follow max_replicas and static [evidence: test:tests/test_spec_hive.py::test_derived_properties]
- AC5: a user any-mcp plugin entry named or namespaced orchestrator is rejected with 422 [evidence: test:tests/test_spec_hive.py::test_orchestrator_plugin_name_reserved]
- AC6: a preset without the new fields stays sparse [evidence: test:tests/test_spec_hive.py::test_preset_stays_sparse]
- AC7: README, openapi.json and schema.d.ts agree [evidence: command:uv run pytest tests/test_readme_api.py tests/test_api_clusters.py tests/test_api_presets.py -q]
- AC8: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]
- AC9: a stored spec loaded after the backfill keeps its cap when replicas is edited in place [evidence: test:tests/test_spec_hive.py::test_cap_stable_after_backfill]

## Files

- `src/agent_orchestrator/spec.py`
- `tests/test_spec_hive.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`

## Interfaces

- Owns part `orch-spec-cap-static` (cross-epic contract): `ClusterSpec.max_replicas`, `ClusterSpec.static`, properties `hive`, `alone`, `scalable` in `src/agent_orchestrator/spec.py`.

## Expected outcome

Clusters and presets accept the two fields; every reader can ask `spec.hive` and `spec.scalable`.

## Steps

- Red: write `tests/test_spec_hive.py` for AC1-AC6; run `uv run pytest tests/test_spec_hive.py -q`: fails.
- Green: add the fields, validator and properties; regenerate `openapi.json` (`uv run python -m agent_orchestrator.api.openapi > openapi.json`) and `schema.d.ts` (`npm --prefix frontend run gen:api`); run the verify command: passes.

## Notes

- `ClusterSpec` at `spec.py:119-176` (`extra="forbid"`), `validate_spec` at `:207-268`, any-mcp config check at `:260-266`.
- Presets dump with `exclude_unset` (`api/presets.py:42-54`): resolve the default without marking the field set.

- 2026-10-24 amended: interrogate verdict 2026-10-24 item 7
