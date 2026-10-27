---
title: orch sessions backup restore
status: todo
repo: agents-orchestrator
value: recreating a discarded session brings its Claude conversations back
files: [src/agents_orchestrator/reconciler/cache.py, src/agents_orchestrator/reconciler/loop.py, src/agents_orchestrator/reconciler/wrapper_sessions.py, tests/test_sessions_restore.py, tests/fakes/fake_wrapper.py, tests/test_wrapper_session_bootstrap.py, MEMORY.md]
verify: "uv run pytest -q tests/test_sessions_restore.py tests/test_wrapper_session_bootstrap.py tests/test_cache_restore.py tests/test_cache_save.py tests/test_reconciler.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-sessions-backup-save]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch sessions backup restore

## Requirement

Design D7, user decision verbatim: "Transcript backup: reuse the cache Job/runner/archive/transfer/presign (parameterised, no second S3 client). At discard, after the workdir save, save the PVC `sessions/` subtree as its own S3 object for that session; at create, when the object exists for the same slug, restore it before agent pods start; the bootstrapper then adopts the restored wrapper session of each ordinal (pod names are stable per slug) and resumes it instead of creating a new one. Only when the session cache (spec.cache) is configured; otherwise nothing is backed up and the API/web say so. Status exposes the last sessions backup (finished_at, bytes)."

This task delivers the restore half. Design D7 (my call), verbatim: "A save runs only after a sessions restore in `restored`, `miss` or `reset` (the workdir rule, `SAVE_OK_RESTORE_STATES`); a session whose StatefulSet already existed when the feature arrived records the restore `skipped` with reason `pods_exist` and still saves at discard. A restore never runs once a pod of the session exists." and ""Before agent pods start": while the sessions restore is pending the StatefulSet is applied with `replicas: 0`."

Goal G6, verbatim: "Claude transcripts (/sessions) are backed up to S3 with the workdir at discard and restored on recreate, and a recreated session resumes the restored conversation."

Scope (agents-orchestrator):
- `reconciler/cache.py`: a sessions restore step on the parameterised runner of task orch-sessions-backup-save (Job `agent-<slug>-sessions-restore`, PVC subPath `sessions`, presigned GET of `<cache_s3_prefix>sessions/<slug>.tar.zst`), recorded in `status.cache.sessions_restore` (`restored` with bytes, `miss` when the object does not exist, `reset`, `failed`, or `skipped` with reason `pods_exist`).
- `reconciler/loop.py` `_converge`: on a session's first converge with `spec.cache` set and the cache available, the StatefulSet is applied with `replicas: 0` until the sessions restore has an outcome; a session whose StatefulSet or any pod already exists records `skipped`/`pods_exist` and never restores. A failed restore starts the pods anyway with a degraded message (as the workdir restore does).
- `reconciler/wrapper_sessions.py`: a new agent row of a recreated session adopts the restored wrapper session of its pod (the wrapper lists it from `/sessions/<pod>/`) and resumes it; it is never replaced by `create_session` while a restored session with a transcript is listed. Change the code only where the existing `_pick` order does not already do this; the test pins it either way.
- `tests/fakes/fake_wrapper.py`: the fake can start with a persisted stopped session (as the real wrapper's `load_persisted` lists one).

Interfaces: `status.cache.sessions_restore` run dict (same shape as `status.cache.restore`); `WrapperSessionBootstrapper._bootstrap` / `_pick` keep their signatures.

Steps: tests first in `tests/test_sessions_restore.py` and the adoption test in `tests/test_wrapper_session_bootstrap.py`, seen failing; then the code; run the verify.

Notes: the workdir restore keeps running as today; the two restores are independent Jobs. The wrapper refuses a resume whose config dir, transcript or workdir is missing (`_check_resumable`); the workdir path is the same per slug. DB tests need Docker: PR CI is the evidence. MEMORY.md: dated entry on the replicas-0 hold and `pods_exist`.

## Acceptance conditions

- AC1: a new cache-enabled session whose sessions object exists runs the sessions restore before any agent pod exists: the StatefulSet stays at replicas 0 until the restore has an outcome [evidence: test:tests/test_sessions_restore.py::test_restore_runs_before_agent_pods_start]
- AC2: the sessions restore Job mounts the PVC subPath sessions and carries one presigned GET URL for <prefix>sessions/<slug>.tar.zst [evidence: test:tests/test_sessions_restore.py::test_sessions_restore_job_render]
- AC3: a missing object records miss and the pods start [evidence: test:tests/test_sessions_restore.py::test_sessions_restore_miss_starts_pods]
- AC4: a failed restore starts the pods with a degraded message and the later sessions save is skipped [evidence: test:tests/test_sessions_restore.py::test_sessions_restore_failure_starts_pods_and_skips_save]
- AC5: a session whose StatefulSet or pod already exists never restores, records skipped pods_exist and still saves at discard [evidence: test:tests/test_sessions_restore.py::test_existing_session_skips_restore_and_still_saves]
- AC6: status.cache.sessions_restore records the outcome, finished_at and bytes [evidence: test:tests/test_sessions_restore.py::test_sessions_restore_status_recorded]
- AC7: without spec.cache or with the cache unavailable no sessions restore runs and the pods start at once [evidence: test:tests/test_sessions_restore.py::test_no_sessions_restore_without_session_cache]
- AC8: each new agent adopts and resumes the restored stopped wrapper session of its pod and create_session is never called [evidence: test:tests/test_wrapper_session_bootstrap.py::test_restored_stopped_session_resumed_not_created]
- AC9: the bootstrap and cache suites pass [evidence: command:uv run pytest -q tests/test_wrapper_session_bootstrap.py tests/test_cache_restore.py tests/test_cache_save.py tests/test_reconciler.py]
- AC10: MEMORY.md records the decision [evidence: command:grep -q "pods_exist" MEMORY.md]
- AC11: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/reconciler/cache.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `src/agents_orchestrator/reconciler/wrapper_sessions.py`
- `tests/test_sessions_restore.py`
- `tests/fakes/fake_wrapper.py`
- `tests/test_wrapper_session_bootstrap.py`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
