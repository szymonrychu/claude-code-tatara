---
title: orch sessions live backup
status: todo
repo: agents-orchestrator
value: "Each changed live session's Claude transcripts reach S3 every 30 minutes, not only at discard"
files: [src/agents_orchestrator/reconciler/live_backup.py, src/agents_orchestrator/reconciler/cache.py, src/agents_orchestrator/reconciler/loop.py, src/agents_orchestrator/reconciler/cache_migration.py, src/agents_orchestrator/settings.py, tests/test_sessions_live_backup.py, README.md, MEMORY.md]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_sessions_live_backup.py tests/test_cache_save.py tests/test_cache_migration.py tests/test_settings.py && mise run lint"
depends_on: [orch-archive-live-files]
model: opus
review: ""
verified_head: ""
points: 8
expected_minutes: 27
expected_tokens: 4757438
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch sessions live backup

## Requirement

User request (mx-34 #234, 2026-10-28, relaying the user's priorities), verbatim: "The live-session backup trigger: yes, take it after the paste-.env bug, as a small start-development epic. The user lost sessions in the incident, so a live backup is worth having." Origin (mx-34 #232), verbatim: "there's no backup trigger for a live session (last_transcripts_backup=null)".

README Goal G1, verbatim: "every converged live session whose conversation changed since its last backup gets its Claude transcripts saved to its S3 transcripts object at least every `ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS` (default 1800), by a reconciler-run Job, without stopping or pausing its pods."

README Goal G4 (the status part), verbatim: "the live backup state is visible in `status.cache`."

Design D1, verbatim: "In `_converge`, after the bootstrap step, a new `CacheRunner.sessions_backup_step` starts a backup when all hold: the cache is configured, `save_skip(..., "sessions")` is None (the same eligibility as the discard save), the session's transcripts name is settled (D4), no backup run is `running`, the interval since the last backup run's `started_at` has passed (database clock, like `pre_discard`'s `next_at`), and a turn of the session's agents completed after that `started_at` (or there was no backup yet and a turn completed). [...] Interval default 1800 s (my call; Q1)."

Design D2, verbatim: "`status.cache.sessions_backup {state, started_at, finished_at, bytes, reason, job}` and Job name `agent-<slug>-sessions-backup` (`CacheOp` action `backup`). Reusing `sessions_save` is rejected: it is final (`cache.py:330-341`) and its Job name is adopted (`:377`), so the discard would skip its final save or adopt a live Job. The run reuses the crash-safe `_begin/_start/_observe/_finish` pattern and `render_cache_job(..., "save", url, "sessions")`; each new run replaces the previous record once the previous Job is deleted. A failed run records `failed` with its reason and retries after the interval."

Design D2 amendment (planner, 2026-10-29, my call), verbatim: "`sessions_backup` also carries `last_saved {started_at, finished_at, bytes}`, set from a run that ends `saved` and carried forward unchanged by every later run until the next `saved`. The interval counts from the latest run's `started_at` (any outcome, so a failure or a `shared_name` skip retries after the interval); the change signal is a turn of the session's agents completed after `last_saved.started_at` (with no `last_saved`, any completed turn)."

Design D4, verbatim: "A live backup presigns exactly what the discard save would: `status.cache.sessions_object` when pinned. While a session's decouple migration is pending or failed (decouple D7/D9) the backup does not run (reason not recorded; it simply waits), so it never writes the legacy name the migration is about to copy. The decouple migration's "no copy while a save run is `running`" guard (decouple interrogate item 4) also counts a running live backup (fix-as-ac)."

Design D5, verbatim: "With a shared literal template, several live sessions pin one transcripts object; each live backup would overwrite the others' with only its own pod dirs. A live backup is skipped (record `skipped`, reason `shared_name`) while another live session (not discarded) pins the same `sessions_object`; the discard save keeps today's last-writer-wins semantics (decouple Q1/Q10) (my call; Q4)."

Design D8 (the orchestrator part), verbatim: "`ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS` (default 1800; 0 disables live backups) in settings.py and README; the chart passes it through `.Values.env`."

Brief fix-as-ac, verbatim: "Live run must not write `sessions_save` nor share Job name `agent-<slug>-sessions-save` (one-shot save, Job adoption cache.py:377)." and "Decouple migration guard (item 4: no copy while a save is running) must include the live run; live run must use the legacy `sessions/<slug>` while migration pending." (the second half is superseded by D4: the live run does not run while the migration is pending.)

## Acceptance conditions

- AC1: a converged session (sessions restore `restored`, pods running) with a completed turn and no sessions_backup record gets Job `agent-<slug>-sessions-backup` (cache label `sessions-backup`, command `orch cache save`, PVC subPath `sessions` read-only) presigning a PUT of status.cache.sessions_object; status.cache.sessions_backup goes running then saved with bytes and last_saved; the StatefulSet replicas and the agent pods are unchanged throughout [evidence: test:tests/test_sessions_live_backup.py::test_converged_session_backed_up_beside_running_pods]
- AC2: a live backup never writes status.cache.sessions_save and never creates, adopts or deletes Job `agent-<slug>-sessions-save`, even when a Job of that name exists [evidence: test:tests/test_sessions_live_backup.py::test_backup_never_touches_sessions_save]
- AC3: after a saved backup no new run starts before ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS have passed since its started_at (database clock), nor after that while no turn of the session's agents completed after last_saved.started_at; once both hold a new run starts, and an idle session gets no Job across many ticks past the interval [evidence: test:tests/test_sessions_live_backup.py::test_interval_and_change_gate]
- AC4: a failed run (Job create failure, failed Job, timeout) records failed with its reason, keeps the previous last_saved, and the next run starts only after the interval, even with no new turn [evidence: test:tests/test_sessions_live_backup.py::test_failed_backup_keeps_last_saved_and_retries_after_interval]
- AC5: a new run starts only once the previous run's Job is gone: a finished record whose Job still exists gets that Job deleted and no new run in that tick [evidence: test:tests/test_sessions_live_backup.py::test_new_run_waits_for_previous_job_deleted]
- AC6: crash safety: a running record with no Job (crash before the create) creates the backup Job; an existing backup Job with job unset (crash after the create) is adopted; neither path touches the sessions save Job [evidence: test:tests/test_sessions_live_backup.py::test_backup_crash_safety]
- AC7: no backup Job and no record when spec.cache is unset, the cache is not configured, the interval setting is 0, or save_skip(..., "sessions") returns a reason (never converged, restore running, restore failed) [evidence: test:tests/test_sessions_live_backup.py::test_backup_eligibility]
- AC8: while the session's decouple migration is pending or failed (cache_migration pending predicate) no backup Job is created and no sessions_backup record is written; once sessions_object is pinned the backup presigns exactly that object [evidence: test:tests/test_sessions_live_backup.py::test_backup_waits_for_pending_migration]
- AC9: while a sessions_backup run is running the decouple migration copies and repoints nothing, as for a running save [evidence: test:tests/test_sessions_live_backup.py::test_migration_waits_for_running_backup]
- AC10: while another session row pins the same sessions_object the backup records skipped with reason shared_name, keeps last_saved and creates no Job; it is checked again after the interval and runs once that row is gone [evidence: test:tests/test_sessions_live_backup.py::test_shared_name_skipped]
- AC11: Settings has sessions_backup_interval_seconds from ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS, default 1800, 0 accepted (disables), a negative value refused [evidence: test:tests/test_sessions_live_backup.py::test_backup_interval_setting]
- AC12: README documents ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS [evidence: test:tests/test_settings.py::test_env_names_documented_in_readme]
- AC13: README documents status.cache.sessions_backup and its last_saved, and MEMORY.md records the live backup decisions [evidence: command:grep -q "sessions_backup" README.md && grep -q "last_saved" README.md && grep -q "sessions_backup" MEMORY.md]
- AC14: the existing save, migration and settings suites and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_save.py tests/test_cache_migration.py tests/test_settings.py && mise run lint]

## Files

- `src/agents_orchestrator/reconciler/live_backup.py`
- `src/agents_orchestrator/reconciler/cache.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `src/agents_orchestrator/reconciler/cache_migration.py`
- `src/agents_orchestrator/settings.py`
- `tests/test_sessions_live_backup.py`
- `README.md`
- `MEMORY.md`

## Interfaces

- `settings.py:Settings.sessions_backup_interval_seconds: int` (env `ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS`), default 1800, `ge=0`; 0 disables live backups.
- `CacheRunner.sessions_backup_step(session) -> None` (in `reconciler/cache.py`, or in a new `reconciler/live_backup.py` the runner delegates to; the builder's choice, design "Left to the builder"), called by `Reconciler._converge` after `_bootstrap_wrapper_sessions` on every converge tick; never called from `_discard`.
- Job: `agent-<slug>-sessions-backup`, labels `session_labels(slug)` plus `agents.szymonrichert.pl/cache: sessions-backup`, rendered from `render_cache_job(session, settings, "save", url, "sessions")` with only the name and cache label changed (command stays `orch cache save`); the presigned PUT names exactly the object the discard sessions save would presign at that moment (`status.cache.sessions_object`, pinned through the same `_begin` code path when unpinned and no migration is pending).
- `status.cache.sessions_backup`: `{state: "running"|"saved"|"failed"|"skipped", started_at, finished_at, bytes, reason, job, last_saved: {started_at, finished_at, bytes} | null}`; written through the runner's `_write` (the reconciler is the only writer of `sessions.status`). Contract change for `orch-session-status-cache` recorded by the orchestrator.
- Change signal: a row in `turns` of an agent of this session with `completed_at` later than `last_saved.started_at` (any `completed_at` when there is no `last_saved`); the SQL is the builder's (design "Left to the builder").
- Shared name: another `sessions` row (any `desired`; a purged row no longer exists) whose `status.cache.sessions_object` equals this session's.
- Decouple migration guard: `reconciler/cache_migration.py` treats `status.cache.sessions_backup.state == "running"` like a running `save` or `sessions_save` (returns without copying or repointing).

## Expected outcome

After deploy, each converged live session whose agents completed a turn gets a `sessions_backup` Job within one reconcile tick when it has no backup yet, then at most once per interval and only after new turns; its transcripts object in S3 is overwritten with the current `/sessions` tree while its pods keep running. Idle sessions, sessions sharing a transcripts name and sessions whose decouple migration is pending get no backup Job.

## Steps

- Read `reconciler/cache.py` (all of `CacheRunner`, `CacheOp`, `render_cache_job`), `reconciler/loop.py` (`_converge`, `_discard`, `_db_now`, the `pre_discard` `next_at` pattern), `reconciler/cache_migration.py` (the running-save guard and the pending predicate), `cache/save_rule.py`, `cache/presign.py`, `settings.py`, `db/sessions.py`, `db/migrations/0001_init.sql` (`turns`, `agents`), `tests/test_cache_save.py` (`SaveEnv`), `tests/test_sessions_backup.py` and `tests/test_cache_migration.py` (helpers) and README `## Workspace cache` in one pass.
- Red: write tests/test_sessions_live_backup.py with the tests named in AC1-AC11 (fake kube and the existing env helpers; the database clock moved by the same means `test_cache_save.py` uses for timeouts); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_sessions_live_backup.py`; expect failures on the missing step and setting (DB tests: on CI, `DockerException` locally; AC11 runs locally).
- Green: add the setting, the `backup` operation, the step, the `last_saved` carry-forward, the shared-name and pending checks, the `_converge` call and the migration guard; rerun the verify; expect every test passed on CI and the existing save, migration and settings suites unchanged.
- Document `ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS` in the README settings table and `status.cache.sessions_backup` (with `last_saved`) in README `## Workspace cache`; add the MEMORY.md entry (dated, with the why: own record and Job name because `sessions_save` is final and its Job adopted; `last_saved` so G4 survives a failed run); `mise run lint`; expect exit 0.

## Notes

- `CacheAction` is `Literal["restore", "save"]` and `render_cache_job` puts the action in the command; the backup is a third operation that renders as a save. Keep `job_name`, the cache label, `status_key` and the pod listing in `_outcome` keyed by the backup operation, so the backup never lists, adopts or deletes the save Job or its pods (AC2).
- `_begin` today writes a fresh run dict; for the backup it must carry `last_saved` forward from the previous record, and set it only when a run ends `saved` (`_finish_from_log`).
- The previous run's Job must be gone before a new run starts (AC5): `_finish` keeps `job` in the record and `_outcome` deletes the Job after, so a crash in between leaves a finished record whose Job still exists; deterministic Job names mean `_start` would adopt that stale Job otherwise.
- Interval and change signal use the database clock (`SELECT now()`), never the reconciler's wall clock.
- No chart change: the chart passes any `ORCH_*` through `.Values.env` (`chart/.../templates/configmap.yaml:4-6`), and the setting has a default and no paired setting, so the per-container Settings pair check proposed by the matrix retro does not apply.
- Job cost: one Job pod with a `cache_max_bytes` emptyDir per changed session per interval (design Assumptions).
- Base: this epic builds after decouple-s3-session-cache-fr, hive decoupling and slash commands from chat have landed on main; rebase onto main first and use the decouple names as they landed (`presign.sessions_object_name`, `status.cache.sessions_object`, the `cache_migration` pending predicate, `CacheRunner._begin` pinning). No SQL migration is planned; if one proves necessary it takes the next free number on main at build time (`<MIGRATION>`), and the builder raises it as a question first.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST); it is not a regression.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Per-task security check (retro, recurring): S3 is reached only through one presigned URL per Job, signed by the reconciler; no credential or presigned query string in a log line, a status `reason` or an error message; the api imports neither `reconciler` nor `k8s`.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.
