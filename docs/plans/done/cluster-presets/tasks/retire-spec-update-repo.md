---
title: retire spec update repo
status: done
repo: agent-orchestrator
value: no dead live-edit code is left to mislead the next change
files: [src/agent_orchestrator/db/clusters.py, src/agent_orchestrator/spec.py, tests/test_clusters_repo.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_clusters_repo.py tests/test_api_clusters.py tests/test_api_messages.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [retire-cluster-patch-route]
model: ""
review: ""
verified_head: 79cc4d6836fbbe378c988ce7cd24ffdcd5b4950d
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 7
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# retire spec update repo

## Requirement

Remove the dead code live edit leaves behind (design D5; user N2), test-first.

- `src/agent_orchestrator/db/clusters.py`: delete `update_spec` and `ClusterDeleting` (its only user); the module docstring stays accurate.
- `src/agent_orchestrator/spec.py`: `validate_spec(spec, settings, stored=None)` keeps its `stored` parameter, which the preset PUT uses (a stored model or effort outside the settings lists is accepted only when unchanged); it is not deleted and the docstring says why it stays.
- `tests/test_clusters_repo.py`: delete `test_update_bumps_generation_and_notifies` and the `update_spec`/`ClusterDeleting` lines of `test_delete_marks_deleting`; add the retirement test `test_live_edit_code_retired`: `agent_orchestrator.db.clusters` has no `update_spec` and no `ClusterDeleting`, and `inspect.signature(validate_spec)` still has the `stored` parameter; add `test_validate_spec_stored_exception_kept`: an unchanged stored model outside the settings list passes and a changed one is rejected.
- No `update_spec` or `ClusterDeleting` reference remains in `src/` or `tests/`, and no cluster route passes a stored spec to `validate_spec` (only the preset PUT does).

## Acceptance conditions

- AC1: update_spec and ClusterDeleting are gone and validate_spec keeps its stored parameter [evidence: test:tests/test_clusters_repo.py::test_live_edit_code_retired]
- AC2: validate_spec accepts a model or effort outside the settings lists only when unchanged from stored, and rejects a changed one [evidence: test:tests/test_clusters_repo.py::test_validate_spec_stored_exception_kept]
- AC3: no reference to the removed symbols remains [evidence: command:! grep -rnE 'update_spec|ClusterDeleting' src tests --include=*.py]
- AC4: targeted tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_clusters_repo.py tests/test_api_clusters.py tests/test_api_messages.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/db/clusters.py`
- `src/agent_orchestrator/spec.py`
- `tests/test_clusters_repo.py`

## Interfaces

- `spec.validate_spec(spec: ClusterSpec, settings: Settings, stored: ClusterSpec | None = None) -> None` (unchanged signature).
- `db/clusters.py` without `update_spec` and `ClusterDeleting`.

## Expected outcome

The repository and spec module carry no code that only live edit used.

## Steps

- Add `test_live_edit_code_retired` and `test_validate_spec_stored_exception_kept`, drop the update tests; run `uv run pytest -q -p no:cacheprovider tests/test_clusters_repo.py`: the retirement test fails.
- Delete `update_spec` and `ClusterDeleting`; run the verify command: passes.

## Notes

- Deletion pinned by a retirement test (`test_live_edit_code_retired`).
- The api no longer passes `stored` from a cluster route after retire-cluster-patch-route; the preset PUT does (ruling 2).
- Builder check ruling 2 (2026-10-23): PUT of a preset accepts a stored model, effort or image that is no longer in the settings lists only when that value is unchanged from the stored preset (the legacy rule PATCH used); changing to an unknown value is 422. validate_spec keeps its `stored` parameter (and check_spec its `stored` parameter) for this; retire-spec-update-repo must not delete it, it still deletes update_spec and ClusterDeleting if unused. Scheduling always validates fully (no `stored`) and returns 422 with the reason and the preset name. The editor's Model/Effort select shows a stored out-of-list value as an extra option labelled "<value> (not available)".

- 2026-10-23 amended: builder check ruling 2: validate_spec keeps stored (AC1, AC2 rewritten)
