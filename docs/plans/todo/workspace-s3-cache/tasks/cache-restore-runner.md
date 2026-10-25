---
title: cache restore runner
status: todo
repo: agents-orchestrator
value: "a cached session starts from the previous session's workspace before init and Claude run"
files: [src/agents_orchestrator/reconciler/cache.py, src/agents_orchestrator/reconciler/loop.py, tests/test_cache_restore.py, tests/fakes/fake_kube.py]
verify: "uv run pytest -q tests/test_cache_restore.py tests/test_init_runner.py tests/test_reconciler.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [cache-key-on-create, cache-presign, cache-job-render]
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

# cache restore runner

## Requirement

Restore the workspace at session start, before init and the Claude sessions (design D1, D3, D11; contract orch-session-status-cache). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

- `src/agents_orchestrator/reconciler/cache.py`: `CacheRunner(pool, kube, settings, *, write_status)` with `restore_step(session) -> CacheGate`, the same crash-safe shape as `InitRunner` (`reconciler/init.py`). No `spec.cache`: no status, gate clear. First step: write `status.cache = {key, object, restore: {state: "running", started_at (database clock), finished_at: null, bytes: null, reason: null, job: null}}`; when `not settings.cache_available`, finish `failed` with reason `not_configured`; else create the restore Job (task cache-job-render) with `presign(settings, "GET", key)` and then write `job`. Observe: Complete: read the last JSON line of the pod log tail (`checks.log_tail`): `restored` with `bytes`, or `miss`. Failed: `failed` with the JSON line's `reason`, else `exit <code>`. DeadlineExceeded, or older than the cache timeout plus `DEADLINE_GRACE_SECONDS`: `failed` `timeout`. A Job that vanished after its create: `failed` `job_missing`; a crash between the running write and the create: create it. A foreign Job: `failed` `foreign_object`. A create error: `failed` `job_create_failed: <error>`. The Job is deleted after the outcome is written; a later tick deletes a leftover one.
- `CacheGate {hold, degraded, message}`: `running` holds with "cache restore running"; `failed` is degraded with "cache restore failed: <reason>"; `restored` and `miss` are clear.
- `src/agents_orchestrator/reconciler/loop.py`: `_converge` runs `restore_step` before `init.step`; while the restore holds, `init.step` is not called and no Claude session is bootstrapped (phase pending); a failed restore lets init and the sessions run, phase degraded, its message joined. `_rebootstrap` holds while the restore holds. The Reconciler calls `settings.require_cache()` at construction when `settings.cache_available`.

## Acceptance conditions

- AC1: a session without cache gets no status.cache and no cache Job [evidence: test:tests/test_cache_restore.py::test_no_cache_no_job]
- AC2: the first converge writes restore running, creates the restore Job with a presigned GET URL, and starts no init Job [evidence: test:tests/test_cache_restore.py::test_restore_job_created_before_init]
- AC3: a restored outcome records bytes, deletes the Job, and the next converge starts the init Job [evidence: test:tests/test_cache_restore.py::test_restored_then_init_runs]
- AC4: a miss lets init and the sessions start without degrading the phase [evidence: test:tests/test_cache_restore.py::test_miss_is_not_degraded]
- AC5: a failed restore records the CLI reason and the sessions start with phase degraded [evidence: test:tests/test_cache_restore.py::test_failed_restore_degrades]
- AC6: timeout, job_missing and foreign_object are recorded as failed with that reason [evidence: test:tests/test_cache_restore.py::test_restore_timeout_missing_foreign]
- AC7: a cache spec while the cache is unavailable records failed not_configured and creates no Job [evidence: test:tests/test_cache_restore.py::test_not_configured]
- AC8: a crash between the running write and the create creates the Job exactly once on the next tick [evidence: test:tests/test_cache_restore.py::test_crash_safety]
- AC9: a rebootstrap command is held while the restore runs [evidence: test:tests/test_cache_restore.py::test_rebootstrap_held_during_restore]
- AC10: the reconciler refuses to start with a bucket but no credentials [evidence: test:tests/test_cache_restore.py::test_reconciler_requires_cache_credentials]
- AC11: the existing init and reconciler tests stay green [evidence: command:uv run pytest -q tests/test_init_runner.py tests/test_reconciler.py tests/test_agent_init_scripts.py]
- AC12: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/reconciler/cache.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `tests/test_cache_restore.py`
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
