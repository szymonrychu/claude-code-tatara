---
title: smoke workspace cache
status: todo
repo: agents-helmfile
value: the deployed smoke proves a workspace written in one session is restored in the next
files: [scripts/smoke.sh, tests/test_smoke_script.py, README.md]
verify: "uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# smoke workspace cache

## Requirement

Prove the workspace cache in the deployed smoke (design D9, D12; goal G8). Paths are in code/agents-helmfile; post-rename API paths (`/api/v1/sessions`; if the rename epic chose other paths, the orchestrator amends this task first).

`scripts/smoke.sh`, after the existing checks, a workspace cache check:
- `GET /api/v1/meta`: `cache.available` must be true, else fail "workspace cache is not configured".
- A random run id `RUN_ID`. Session A: raw spec, 1 replica, `cache: {key: "smoke-workspace-cache"}`, init script `printf '%s\n' "$RUN_ID" > cache-marker`. Wait (bounded by `SMOKE_TIMEOUT_S`) for its init to succeed and `status.cache.restore.state` to be `restored` or `miss`. Delete A and wait until `GET` returns 404 (its save ran in the discard).
- Session B: the same cache key, init script `grep -qx "$RUN_ID" cache-marker`. Wait for `status.cache.restore.state` `restored` and the init `succeeded`; a failed init fails the smoke with "workspace cache did not carry the marker" and the init log tail. Delete B and wait for 404.
- The object `workspace-cache/smoke-workspace-cache.tar.zst` stays and is overwritten on each run (one fixed key). Both sessions are deleted by the existing cleanup trap on any failure.
- `tests/test_smoke_script.py` (fake API): the happy path passes; an unavailable cache fails; a B init failure fails with the marker message; both sessions are deleted on failure. `README.md`: the smoke list names the cache check.

## Acceptance conditions

- AC1: the smoke happy path including the cache check exits 0 against the fake API [evidence: test:tests/test_smoke_script.py::test_workspace_cache_round_trip_passes]
- AC2: an orchestrator without the cache fails the smoke [evidence: test:tests/test_smoke_script.py::test_workspace_cache_unavailable_fails]
- AC3: a second session without the marker fails with the marker message [evidence: test:tests/test_smoke_script.py::test_workspace_cache_marker_missing_fails]
- AC4: both cache sessions are deleted when the check fails [evidence: test:tests/test_smoke_script.py::test_workspace_cache_sessions_cleaned_up]
- AC5: the existing smoke tests stay green [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py]
- AC6: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
