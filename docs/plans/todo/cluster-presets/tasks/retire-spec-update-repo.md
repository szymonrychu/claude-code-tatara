---
title: retire spec update repo
status: todo
repo: agent-orchestrator
value: no dead live-edit code is left to mislead the next change
files: [src/agent_orchestrator/db/clusters.py, src/agent_orchestrator/spec.py, tests/test_clusters_repo.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_clusters_repo.py tests/test_api_clusters.py tests/test_api_messages.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [retire-cluster-patch-route]
owns: []
uses: []
model: ""
estimate: 5
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

# retire spec update repo

## Requirement

Remove the dead code live edit leaves behind (design D5; user N2), test-first.

- `src/agent_orchestrator/db/clusters.py`: delete `update_spec` and `ClusterDeleting` (its only user); the module docstring stays accurate.
- `src/agent_orchestrator/spec.py`: `validate_spec(spec, settings)` loses the `stored` parameter; model and effort are always checked against the settings lists; the docstring says so.
- `tests/test_clusters_repo.py`: delete `test_update_bumps_generation_and_notifies` and the `update_spec`/`ClusterDeleting` lines of `test_delete_marks_deleting`; add the retirement test `test_live_edit_code_retired`: `agent_orchestrator.db.clusters` has no `update_spec` and no `ClusterDeleting`, and `inspect.signature(validate_spec)` has no `stored` parameter; add `test_validate_spec_always_checks_model_and_effort`.
- No `update_spec` or `ClusterDeleting` reference remains in `src/` or `tests/`, and no caller passes a stored spec to `validate_spec`.

## Acceptance conditions

- AC1: update_spec, ClusterDeleting and the stored parameter are gone [evidence: test:tests/test_clusters_repo.py::test_live_edit_code_retired]
- AC2: validate_spec rejects a model or effort outside the settings lists with no exception for a stored value [evidence: test:tests/test_clusters_repo.py::test_validate_spec_always_checks_model_and_effort]
- AC3: no reference to the removed symbols remains [evidence: command:! grep -rnE 'update_spec|ClusterDeleting' src tests --include=*.py]
- AC4: targeted tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_clusters_repo.py tests/test_api_clusters.py tests/test_api_messages.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/db/clusters.py`
- `src/agent_orchestrator/spec.py`
- `tests/test_clusters_repo.py`

## Interfaces

- `spec.validate_spec(spec: ClusterSpec, settings: Settings) -> None`.
- `db/clusters.py` without `update_spec` and `ClusterDeleting`.

## Expected outcome

The repository and spec module carry no code that only live edit used.

## Steps

- Add `test_live_edit_code_retired` and `test_validate_spec_always_checks_model_and_effort`, drop the update tests; run `uv run pytest -q -p no:cacheprovider tests/test_clusters_repo.py`: the retirement test fails.
- Delete `update_spec`, `ClusterDeleting` and the `stored` parameter; run the verify command: passes.

## Notes

- Deletion pinned by a retirement test (`test_live_edit_code_retired`).
- The api stopped passing `stored` in retire-cluster-patch-route.
