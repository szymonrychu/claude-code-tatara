---
title: cache save on discard
status: todo
repo: agents-orchestrator
value: "the workspace is uploaded under the same name when a session ends, without ever blocking the discard"
files: [src/agents_orchestrator/reconciler/cache.py, src/agents_orchestrator/reconciler/loop.py, tests/test_cache_save.py, tests/fakes/fake_kube.py]
verify: "uv run pytest -q tests/test_cache_save.py tests/test_discard_hook.py tests/test_reconciler.py tests/test_autoclose.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [cache-restore-runner]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 14
expected_tokens: 1860143
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# cache save on discard

## Requirement

Save the workspace at session end, under the same object name, before the PVC is deleted (design D3, D4, D11). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

- `CacheRunner.save_step(session) -> bool` in `src/agents_orchestrator/reconciler/cache.py` (True: the discard may go on). No `spec.cache`: True. Skip rules, each writing `status.cache.save = {state: "skipped", reason}` and returning True with no Job: the restore is absent or `running` (`restore_running`); the restore failed with a reason starting `download_failed`, `timeout`, `job_missing`, `foreign_object`, `job_create_failed` or `not_configured` (that reason's head word); the cache is unavailable now (`not_configured`). After `extract_failed` the save runs, so a corrupt archive is replaced.
- Otherwise: write `save {state: "running", ...}`, create the save Job (task cache-job-render) with `presign(settings, "PUT", key)` for the same `object` as the restore, return False; observe as the restore does: `saved` with `bytes`, `skipped` with the CLI reason (`no_workdir`), `failed` with `too_large`, `upload_failed: ...`, `timeout`, `job_missing`, `foreign_object` or `job_create_failed: ...`. After any outcome: delete the Job and return True. A failed save logs a warning naming the session slug, the key and the reason; it never holds the discard.
- `src/agents_orchestrator/reconciler/loop.py`: `_quiesce` scales the StatefulSet to zero and waits for the agent pods when a hook is owed or a save is owed (`spec.cache` set and no save outcome yet); after `discard_quiesce_timeout_seconds` it goes on with pods still running, logged. `_discard` order: cancel checks, quiesce, `save_step` (phase `deleting`, message "saving the workspace cache" while it returns False), `pre_discard`, prune. `DISCARD_ORDER` still deletes any leftover cache Job.
- Every deletion path goes through `_discard`: explicit delete, idle autoclose (`close_expired`), a trigger service's delete.

## Acceptance conditions

- AC1: deleting a cached session scales the StatefulSet to zero, creates the save Job only after the agent pods are gone, and keeps the PVC until the save outcome [evidence: test:tests/test_cache_save.py::test_save_runs_after_quiesce_before_prune]
- AC2: a saved outcome records bytes, then the discard deletes the objects and purges the row [evidence: test:tests/test_cache_save.py::test_saved_then_purged]
- AC3: too_large, upload_failed and timeout are recorded, logged, and the discard still completes [evidence: test:tests/test_cache_save.py::test_failed_save_does_not_block_discard]
- AC4: a restore that is running, failed with download_failed or timeout, or a cache now unavailable skips the save with that reason and creates no Job [evidence: test:tests/test_cache_save.py::test_save_skipped_when_restore_did_not_finish]
- AC5: after an extract_failed restore the save runs [evidence: test:tests/test_cache_save.py::test_save_after_extract_failed]
- AC6: an idle autoclose saves the workspace [evidence: test:tests/test_cache_save.py::test_autoclose_saves]
- AC7: a quiesce timeout with pods still running saves anyway [evidence: test:tests/test_cache_save.py::test_quiesce_timeout_saves_anyway]
- AC8: a crash between the running write and the create creates the save Job exactly once [evidence: test:tests/test_cache_save.py::test_save_crash_safety]
- AC9: the save URL is a presigned PUT for the restore's object name [evidence: test:tests/test_cache_save.py::test_same_object_name]
- AC10: the discard hook, reconciler and autoclose tests stay green [evidence: command:uv run pytest -q tests/test_discard_hook.py tests/test_reconciler.py tests/test_autoclose.py]
- AC11: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/reconciler/cache.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `tests/test_cache_save.py`
- `tests/fakes/fake_kube.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
