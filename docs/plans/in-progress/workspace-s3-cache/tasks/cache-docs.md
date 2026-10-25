---
title: cache docs
status: in-progress
repo: agents-orchestrator
value: users and operators can read how the workspace cache behaves and is configured
files: [README.md, MEMORY.md, tests/test_readme_api.py]
verify: "uv run pytest -q tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [cache-save-on-discard, cache-chart-values]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 689196
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# cache docs

## Requirement

Document the workspace cache (design D4, D11, D12). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

- `README.md`: a `## Workspace cache` section: the `spec.cache` field and the key derivation (`default_cache_key`, raw spec needs a key); the lifecycle (restore Job before init and the sessions, save Job during the discard before the PVC goes; nothing on pod restart or node loss); `status.cache` with every restore and save state and the save skip rules; last writer wins for sessions sharing a key; credentials only in the reconciler, Jobs get one presigned URL; a table of every `ORCH_CACHE_*` setting; the Job CLI env (`CACHE_URL`, `CACHE_DIR`, `CACHE_MAX_BYTES`, `CACHE_EXCLUDE`, `CACHE_SCRATCH`) and its JSON outcome line; `GET /api/v1/meta` `cache`.
- `MEMORY.md`: dated 2026 lines for D1 (Jobs, not the agent pod), D2 (presigned URLs), D4 (last writer wins), D11 (save skip rules), each with the why.
- `tests/test_readme_api.py`: `test_readme_documents_workspace_cache` asserts the section and each `ORCH_CACHE_*` name the settings define.

## Acceptance conditions

- AC1: the README section names every ORCH_CACHE_* setting the code defines [evidence: test:tests/test_readme_api.py::test_readme_documents_workspace_cache]
- AC2: the section exists [evidence: doc-section:README.md#Workspace cache]
- AC3: MEMORY.md records the cache decisions [evidence: command:grep -q "presigned" MEMORY.md && grep -q "last writer wins" MEMORY.md]
- AC4: the README route and openapi tests stay green [evidence: command:uv run pytest -q tests/test_readme_api.py]
- AC5: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `README.md`
- `MEMORY.md`
- `tests/test_readme_api.py`

## Interfaces

- `README.md#Workspace cache`; contracts `orch-session-spec-cache`, `orch-session-status-cache`, `orch-cache-settings-env`, `orch-cache-job-cli`, `orch-meta-cache` documented there.

## Expected outcome

A reader of the README can enable the cache on a preset, configure any S3 store, and read `status.cache`.

## Steps

- Red: add `test_readme_documents_workspace_cache` to `tests/test_readme_api.py` (collect the `ORCH_CACHE_*` names from `Settings.model_fields`); run it: fails.
- Green: write the README section and the MEMORY.md lines; run the verify command.

## Notes

- Match the README's existing style for settings tables and status fields (see the init scripts section).
