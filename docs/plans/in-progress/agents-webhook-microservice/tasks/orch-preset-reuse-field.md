---
title: orch preset reuse field
status: in-progress
repo: agent-orchestrator
value: a preset can opt in to sending new events to the agent still running for them
files: [src/agent_orchestrator/spec.py, openapi.json, README.md, tests/test_spec_config.py, tests/test_api_presets.py]
verify: "uv run pytest tests/test_spec_config.py tests/test_api_presets.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-service-port-docs]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 13
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch preset reuse field

## Requirement

The preset setting for agent reuse (design D17; user clarification 2026-10-25: "(agent reuse is an optional feature, it can be set during preset creation)"). Paths are in code/agent-orchestrator. Additive only (`/api/v1` additive-only rule).

- `src/agent_orchestrator/spec.py`: `ClusterSpec.reuse_running_agent: bool | None = None`, sparse like `autoclose_after_seconds` (unset is not stored or dumped in a preset), with a docstring: read only by trigger services (agents-webhook, agents-schedule) to send a new event to the cluster still running for it; the orchestrator never acts on it, so clusters created by a user ignore it.
- `openapi.json`: regenerated (`uv run python -m agent_orchestrator.api.openapi > openapi.json`).
- `README.md`: the field in the spec field reference and in the presets section (meaning, default false, read by trigger services only, served on the service port through `GET /api/v1/presets/{id}`).
- `tests/test_spec_config.py`: the field accepts true and false, refuses a non-boolean, and is absent from a sparse dump when unset.
- `tests/test_api_presets.py` (API only): `POST /api/v1/presets` with `spec.reuse_running_agent: true` -> `GET /api/v1/presets/{id}` returns it; a preset without it has no such key; `PUT` can clear it; a cluster created from the preset carries it in its spec and is otherwise unchanged.

## Acceptance conditions

- AC1: reuse_running_agent is an optional sparse boolean of the spec [evidence: test:tests/test_spec_config.py::test_reuse_running_agent_sparse_bool]
- AC2: presets store, return and clear the field through the API [evidence: test:tests/test_api_presets.py::test_reuse_running_agent_round_trip]
- AC3: openapi.json and the README match the app [evidence: command:uv run pytest tests/test_readme_api.py -q]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/spec.py`
- `openapi.json`
- `README.md`
- `tests/test_spec_config.py`
- `tests/test_api_presets.py`

## Interfaces

- Owns `preset-reuse-running-agent` (new contract): `ClusterSpec.reuse_running_agent: bool | None` in `src/agent_orchestrator/spec.py`, served in `PresetView.spec` on `GET /api/v1/presets/{id}` (main and service port).

## Expected outcome

A preset can carry `reuse_running_agent: true`; the orchestrator stores and returns it and otherwise ignores it.

## Steps

- Red: add the two tests; run `uv run pytest tests/test_spec_config.py tests/test_api_presets.py -q`: fail.
- Green: the field, then `uv run python -m agent_orchestrator.api.openapi > openapi.json`, then the README; run the verify command.

## Notes

- Sparse like `autoclose_after_seconds` (`spec.py` L377, the `_cap` validator keeps presets sparse).
- Additive-only `/api/v1` (`code/agent-orchestrator/MEMORY.md`).

- 2026-10-25 in-progress: re-plan 2026-10-25: added; not started
