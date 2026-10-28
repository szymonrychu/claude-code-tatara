---
title: orch sessions backup save
status: in-progress
repo: agents-orchestrator
value: "a discarded session's Claude conversations are saved to S3 with its workdir"
files: [src/agents_orchestrator/reconciler/cache.py, src/agents_orchestrator/cache/presign.py, src/agents_orchestrator/reconciler/loop.py, tests/test_sessions_backup.py, tests/test_cache_jobs_render.py, MEMORY.md]
verify: "uv run pytest -q tests/test_sessions_backup.py tests/test_cache_jobs_render.py tests/test_cache_save.py tests/test_cache_restore.py tests/test_cache_presign.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
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

# orch sessions backup save

## Requirement

Design D7, user decision verbatim: "Transcript backup: reuse the cache Job/runner/archive/transfer/presign (parameterised, no second S3 client). At discard, after the workdir save, save the PVC `sessions/` subtree as its own S3 object for that session; at create, when the object exists for the same slug, restore it before agent pods start; the bootstrapper then adopts the restored wrapper session of each ordinal (pod names are stable per slug) and resumes it instead of creating a new one. Only when the session cache (spec.cache) is configured; otherwise nothing is backed up and the API/web say so. Status exposes the last sessions backup (finished_at, bytes)."

This task delivers the save half. Design D7 (my call), verbatim: "Object `<cache_s3_prefix>sessions/<slug>.tar.zst`: cache keys match `^[a-z0-9][a-z0-9._-]{0,62}$` (`spec.py:173`, no `/`), so it never collides with a workspace key. Jobs `agent-<slug>-sessions-save|restore`, label `agents.szymonrichert.pl/cache: sessions-save|sessions-restore`, mount PVC subPath `sessions`, no excludes, the same `cache_max_bytes` cap and hardening. Status `status.cache.sessions_save|sessions_restore` in the existing run shape (`state`, `started_at`, `finished_at`, `bytes`, `reason`, `job`)." and "A save runs only after a sessions restore in `restored`, `miss` or `reset` (the workdir rule, `SAVE_OK_RESTORE_STATES`); a session whose StatefulSet already existed when the feature arrived records the restore `skipped` with reason `pods_exist` and still saves at discard."

Goal G6, verbatim: "Claude transcripts (/sessions) are backed up to S3 with the workdir at discard and restored on recreate, and a recreated session resumes the restored conversation."

Scope (agents-orchestrator):
- `reconciler/cache.py`: `render_cache_job` and `CacheRunner` take a target (workdir or sessions) instead of hard-coding the workdir: mount (`workdir_mount` or the PVC subPath `sessions`, read-only for a save), `CACHE_DIR`, `CACHE_EXCLUDE` (`[]` for sessions), object name, Job name, cache label and status key. No copy of the runner: one parameterised implementation.
- `cache/presign.py`: the object name per target (`object_name` for a workspace key, `<cache_s3_prefix>sessions/<slug>.tar.zst` for sessions); one `_client`, one `presign`.
- `reconciler/loop.py` `_discard`: after `cache.save_step` (workdir) has finished, the sessions save step runs, then `pre_discard` and the prunes. Like the workdir save it never holds the discard on failure or timeout; while running it holds the discard.
- Sessions save condition: `spec.cache` set and `settings.cache_available`; skipped (recorded `skipped` with the reason, no Job) when `status.cache.sessions_restore` exists with a state other than `restored`, `miss`, `reset` or `skipped` with reason `pods_exist`. An absent sessions restore record (a session older than this feature) saves.
- `status.cache.sessions_save` records `finished_at` and `bytes` on success (the CLI outcome line, parsed as for the workdir).

Interfaces: `render_cache_job(session, settings, action, url, target=...)` or an equivalent parameter object; `status.cache.sessions_save` run dict as above; the CLI `orch cache save|restore` is unchanged (it already reads `CACHE_DIR`).

Steps: tests first in `tests/test_sessions_backup.py` (fake kube and real Postgres, as `tests/test_cache_save.py`), seen failing; then the parameterisation; `tests/test_cache_jobs_render.py` and `tests/test_cache_restore.py` keep passing unchanged (workdir behaviour is unchanged); `tests/test_cache_save.py` is no longer accurate in one assumption (the discard ends one tick after the workdir save, which no longer holds once a sessions save follows it): only its session setup helper changes, giving each session a sessions restore record whose state skips the sessions save, so it keeps testing the workdir save alone with no assertion changed; run the verify.

Notes: reuse.md do-not-build: "A second S3 client or credential path - presign.py (Job gets one URL, no Secret)". The Job never gets a Secret, `spec.env` or a service account token (module docstring D4). DB tests need Docker: PR CI is the evidence. MEMORY.md: dated entry on the object name and the save condition.

## Acceptance conditions

- AC1: the sessions save Job mounts only the PVC subPath sessions read-only, sets CACHE_DIR to it, carries one presigned PUT URL for <prefix>sessions/<slug>.tar.zst and the workdir Job's hardening [evidence: test:tests/test_sessions_backup.py::test_sessions_save_job_render]
- AC2: at discard the sessions save runs after the workdir save has finished and before pre_discard and the prunes [evidence: test:tests/test_sessions_backup.py::test_discard_saves_sessions_after_workdir]
- AC3: a successful sessions save records finished_at and bytes in status.cache.sessions_save [evidence: test:tests/test_sessions_backup.py::test_sessions_save_status_records_bytes]
- AC4: a failed or timed-out sessions save is recorded and never holds the discard [evidence: test:tests/test_sessions_backup.py::test_sessions_save_failure_does_not_hold_discard]
- AC5: without spec.cache or with the cache unavailable no sessions Job is created [evidence: test:tests/test_sessions_backup.py::test_no_sessions_save_without_session_cache]
- AC6: a sessions restore state that does not allow a save skips it with the reason; an absent record or skipped pods_exist saves [evidence: test:tests/test_sessions_backup.py::test_sessions_save_skip_rules]
- AC7: the sessions save carries CACHE_MAX_BYTES and an emptyDir scratch sized to it, as the workdir save [evidence: test:tests/test_sessions_backup.py::test_sessions_save_respects_max_bytes]
- AC8: the sessions object name never equals a workspace key's object and both are signed by the one presign client [evidence: test:tests/test_sessions_backup.py::test_sessions_object_name_distinct_from_cache_keys]
- AC9: the workdir cache suites pass, unchanged except the tests/test_cache_save.py session setup helper (sessions restore record that skips the sessions save; no assertion changed) [evidence: command:uv run pytest -q tests/test_cache_jobs_render.py tests/test_cache_save.py tests/test_cache_restore.py tests/test_cache_presign.py]
- AC10: MEMORY.md records the decision [evidence: command:grep -q "sessions/<slug>.tar.zst" MEMORY.md]
- AC11: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/reconciler/cache.py`
- `src/agents_orchestrator/cache/presign.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `tests/test_sessions_backup.py`
- `tests/test_cache_jobs_render.py`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_sessions_backup.py tests/test_cache_jobs_render.py tests/test_cache_save.py tests/test_cache_restore.py tests/test_cache_presign.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_sessions_backup.py tests/test_cache_jobs_render.py tests/test_cache_save.py tests/test_cache_restore.py tests/test_cache_presign.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 amended: test_cache_save.py assumes discard ends one tick after the workdir save; the required sessions save (absent restore record saves) contradicts 'unchanged'. Setup-helper-only change accepted (supervisor, standing approval).
