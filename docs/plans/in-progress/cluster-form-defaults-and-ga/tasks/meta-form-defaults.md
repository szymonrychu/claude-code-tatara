---
title: meta form defaults
status: in-progress
repo: agent-orchestrator
value: the form and the pods agree on one set of defaults
files: [src/agent_orchestrator/settings.py, src/agent_orchestrator/api/clusters.py, src/agent_orchestrator/api/schemas.py, src/agent_orchestrator/spec.py, src/agent_orchestrator/k8s/render.py, openapi.json, frontend/src/api/schema.d.ts, README.md]
verify: "uv run pytest tests/test_settings.py tests/test_api_clusters.py tests/test_render.py tests/test_readme_api.py -q -p no:cacheprovider && mise run lint"
depends_on: []
owns: []
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

# meta form defaults

## Requirement

Settings and /meta carry every cluster-form default. settings.py: models default [claude-opus-5-5, claude-sonnet-5-5, claude-haiku-5-5, claude-fable-5-1] (ORCH_MODELS), default_model claude-opus-5-5 (ORCH_DEFAULT_MODEL), efforts [low, medium, high, xhigh, max] (ORCH_EFFORTS), default_effort stays configurable (ORCH_DEFAULT_EFFORT, empty = Claude Code default), default resources cpu request 500m / limit 4, memory request 1Gi / limit 8Gi (ORCH_DEFAULT_CPU_REQUEST, ORCH_DEFAULT_CPU_LIMIT, ORCH_DEFAULT_MEMORY_REQUEST, ORCH_DEFAULT_MEMORY_LIMIT), validated as Kubernetes quantities. GET /api/v1/meta returns models, efforts and defaults for every ClusterSpec field the form edits (model, effort, replicas, pvc_size, storage_class, workdir, max_attempts, auto_compact_pct, resources requests/limits, any_mcp_config, discard hook). k8s/render.py applies the default resources to agent containers when the spec leaves a value empty (explicit spec values win per key). Spec validation rejects a model not in settings.models and an effort not in settings.efforts (empty effort allowed). Regenerate openapi.json and frontend/src/api/schema.d.ts (npm run gen:api) and update the README configuration table.

## Acceptance conditions

- AC1: settings expose the model, effort and resource defaults with env overrides [evidence: test:tests/test_settings.py::test_form_defaults_and_overrides]
- AC2: /meta returns models, efforts and a default for every form field [evidence: test:tests/test_api_clusters.py::test_meta_returns_all_form_defaults]
- AC3: agent pods get default resources when the spec leaves them empty, spec values win per key [evidence: test:tests/test_render.py::test_default_resources_applied_per_key]
- AC4: spec rejects unknown model or effort [evidence: test:tests/test_api_clusters.py::test_spec_rejects_unknown_model_and_effort]
- AC5: frontend API types match openapi.json [evidence: test:tests/test_readme_api.py::test_frontend_schema_matches_openapi]

## Files

- `src/agent_orchestrator/settings.py`
- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/api/schemas.py`
- `src/agent_orchestrator/spec.py`
- `src/agent_orchestrator/k8s/render.py`
- `openapi.json`
- `frontend/src/api/schema.d.ts`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The requirement holds, pinned by the acceptance tests.

What is true and observable when the task is done.

## Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
