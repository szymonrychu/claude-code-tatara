---
title: orch discard stops backup
status: todo
repo: agents-orchestrator
value: "A discard always writes the final transcripts backup, never raced or replaced by a live one"
files: [src/agents_orchestrator/reconciler/loop.py, src/agents_orchestrator/reconciler/live_backup.py, src/agents_orchestrator/reconciler/cache.py, tests/test_sessions_backup.py, README.md]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_sessions_backup.py tests/test_sessions_live_backup.py && mise run lint"
depends_on: [orch-sessions-live-backup]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 8
expected_tokens: 1003544
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch discard stops backup

## Requirement

User request (mx-34 #234, 2026-10-28, relaying the user's priorities), verbatim: "The live-session backup trigger: yes, take it after the paste-.env bug, as a small start-development epic. The user lost sessions in the incident, so a live backup is worth having." Origin (mx-34 #232), verbatim: "there's no backup trigger for a live session (last_transcripts_backup=null)".

README Goal G2, verbatim: "a live backup never corrupts or blocks the discard: a running backup Job is removed before the discard's final save, the final save is never skipped because a live backup exists, and a failed or partial live backup leaves the previous object intact."

Design D3, verbatim: "In `_discard`, before the sessions save step, a running backup Job is deleted (foreground) and its record marked `failed` with reason `superseded_by_discard`; the final save then runs as today. The quiesce already stops the pods, so the final save carries the latest state. Alternative: wait for the backup (bounded by `cache_timeout_seconds`, delays every discard). Direct PUT means a killed backup leaves the previous object intact (`transfer.py:208`)."

Design D3 amendment (planner, 2026-10-29, my call), verbatim: "`KubeApi.delete` deletes a Job with background propagation (`k8s/kube.py:182-190`), so "foreground" is enforced by the discard itself: the record is written `failed`/`superseded_by_discard` first, then the Job is deleted, and the final sessions save starts only when neither the backup Job nor a pod carrying its cache label exists, so a killed backup's PUT can never land after the final one. A crash between the record and the delete is redone by the next tick (a non-running record whose Job still exists). The wait is bounded by `discard_quiesce_timeout_seconds` from the supersede (the record's `finished_at`), after which the final save runs and a warning is logged (anti-goal: no unbounded delay)."

Brief fix-as-ac, verbatim: "Discard must wait for or delete a running live Job before its final save."

Review fix (interrogate 2026-10-29, Act on 1, stale `status.cache` writes): `CacheRunner._write` merges from `session.status["cache"]` and replaces the whole key (reconciler/cache.py:541-544), so a final sessions save run on the session read before the stop step would revert the stop step's `superseded_by_discard` record. `_discard` reloads the session (`_reload`) between the stop step and the final sessions save, and the final save's writes leave `sessions_backup` `failed`/`superseded_by_discard`.

Review decision (interrogate 2026-10-29, Consider 1, late PUT after the bounded discard wait; lead's call, no user question): the bounded wait stays. A backup pod stuck terminating past `discard_quiesce_timeout_seconds` keeps its presigned PUT valid and could land after the final save, so the live run's presign gets the shortest expiry that still covers its own `activeDeadlineSeconds` (`cache_timeout_seconds`): `cache_timeout_seconds + 60` seconds (my call: the 60 s cover the gap between the presign in `_start` and the Job's start, from which the deadline counts), instead of `cache_timeout_seconds + 600`. The discard sessions save, the workdir save and every restore keep `cache_timeout_seconds + 600`. The residual risk is recorded in design Assumptions.

Builder question Q10 (my call: yes): with `ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS` 0 the stop step still handles a leftover `running` `sessions_backup` record before the final save.

## Acceptance conditions

- AC1: discarding a session whose sessions_backup is running records it failed with reason superseded_by_discard, deletes Job `agent-<slug>-sessions-backup`, and creates the final sessions save Job only once neither that Job nor a pod carrying the `sessions-backup` cache label of the session exists [evidence: test:tests/test_sessions_backup.py::test_discard_stops_running_backup_before_final_save]
- AC2: the final sessions save runs whenever save_skip allows it, whatever the sessions_backup record says (absent, saved, failed, skipped, running) [evidence: test:tests/test_sessions_backup.py::test_final_save_runs_whatever_the_live_backup]
- AC3: a crash after the superseded record is written and before the Job delete: the next discard tick deletes the backup Job and still waits for its pods before the final save [evidence: test:tests/test_sessions_backup.py::test_discard_backup_stop_crash_safe]
- AC4: when the backup pods outlive discard_quiesce_timeout_seconds from the supersede, the final save runs anyway and a warning names the session [evidence: test:tests/test_sessions_backup.py::test_backup_stop_wait_is_bounded]
- AC5: end to end: a live backup saves and PUTs the session's transcripts object, a turn completes, a second backup is running when the discard starts, the discard stops it, the final save PUTs the same object last, and a session created again with the same cache name restores (GET) exactly that object [evidence: test:tests/test_sessions_backup.py::test_live_backup_then_discard_final_save_restores]
- AC6: the discard never starts a live backup [evidence: test:tests/test_sessions_backup.py::test_discard_never_starts_a_live_backup]
- AC7: README states that the discard stops a running live backup before the final save, the whole sessions backup suite passes and lint passes [evidence: command:grep -q "superseded_by_discard" README.md && uv run --frozen pytest -q -p no:cacheprovider tests/test_sessions_backup.py tests/test_sessions_live_backup.py && mise run lint]
- AC8: after the stop step marks the backup failed with reason superseded_by_discard, the final sessions save's writes leave status.cache.sessions_backup failed with reason superseded_by_discard (the discard reloads the session between the two; interrogate Act on 1) [evidence: test:tests/test_sessions_backup.py::test_final_save_keeps_superseded_record]
- AC9: the live backup Job's presigned PUT expires cache_timeout_seconds + 60 seconds after signing (X-Amz-Expires), covering its activeDeadlineSeconds, while the discard sessions save, the workdir save and the restores keep cache_timeout_seconds + 600 (interrogate Consider 1) [evidence: test:tests/test_sessions_backup.py::test_live_backup_presign_expiry_covers_deadline_only]
- AC10: with ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS 0 a leftover running sessions_backup record is still marked superseded_by_discard and its Job removed before the final save (builder Q10) [evidence: test:tests/test_sessions_backup.py::test_discard_stops_leftover_backup_when_disabled]

## Files

- `src/agents_orchestrator/reconciler/loop.py`
- `src/agents_orchestrator/reconciler/live_backup.py`
- `src/agents_orchestrator/reconciler/cache.py`
- `tests/test_sessions_backup.py`
- `README.md`

## Interfaces

- `reconciler/loop.py:_discard`: after the workdir save and `_reload`, before `self.cache.save_step(session, "sessions")`, a call (for example `CacheRunner.stop_live_backup(session) -> bool`, True when the final save may start) that: marks a `running` `sessions_backup` record `failed` with reason `superseded_by_discard` and `finished_at` (database clock), keeping `job` and `last_saved`; deletes the owned Job `agent-<slug>-sessions-backup`; returns False (the discard writes `phase: deleting`, message `stopping the live transcripts backup`) while that Job or an owned pod labelled `agents.szymonrichert.pl/cache: sessions-backup` of the session exists, until `discard_quiesce_timeout_seconds` after the record's `finished_at`, then logs a warning naming the session and returns True.
- A non-running record whose Job still exists (crash between the record write and the delete) takes the same delete-and-wait path.
- `CacheRunner.save_step(session, "sessions")` is unchanged: it never reads `sessions_backup`.

## Expected outcome

Discarding a session while its live backup runs: the backup Job is killed, the discard waits a few seconds for its pod to go, then the final transcripts save runs as before and writes the last state; the S3 object ends with the final save's content. A discard with no live backup running behaves exactly as today.

## Steps

- Read `reconciler/loop.py` (`_discard`, `_quiesce`, `_reload`, `_db_now`), the live backup step from orch-sessions-live-backup (`reconciler/cache.py` or `reconciler/live_backup.py`), `reconciler/cache.py:_delete_job`, `k8s/kube.py:delete`, `tests/fakes/fake_kube.py` (`delete`, `list_pods`, `get_job`), `tests/test_sessions_backup.py` and `tests/test_sessions_live_backup.py` (helpers), and the README discard paragraph in one pass.
- Red: add the tests named in AC1-AC6 to tests/test_sessions_backup.py; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_sessions_backup.py`; expect them to fail (DB tests: on CI, `DockerException` locally).
- Green: add the stop step and wire it into `_discard`; rerun the verify; expect every test passed on CI and the existing sessions backup tests unchanged.
- Add the README sentence (the discard stops a running live backup, `superseded_by_discard`, then saves); `mise run lint`; expect exit 0.

## Notes

- Order: write the `failed` record first, then delete. Either crash point is safe because the step acts on any `running` record (mark it, then delete; an absent Job is fine) and on any non-running record whose Job still exists (delete and wait); `_converge`, which would observe a running record, never runs for a deleting session.
- AC5 is the headline promise end to end (retro, recurring): live backup, discard, final save and recreate in one test, asserting the order of the PUT Jobs and the restore's GET object, not separate pieces.
- The quiesce already scales the StatefulSet to zero; backup Job pods are not agent pods (`rollout.agent_pods` matches only `agent-<slug>-<ordinal>`), so the quiesce never waits for them; this task's wait is the only one.
- Base: this epic builds after decouple-s3-session-cache-fr, hive decoupling and slash commands from chat have landed on main; rebase onto main first and use the decouple names as they landed (`presign.sessions_object_name`, `status.cache.sessions_object`, the `cache_migration` pending predicate, `CacheRunner._begin` pinning). No SQL migration is planned; if one proves necessary it takes the next free number on main at build time (`<MIGRATION>`), and the builder raises it as a question first.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST); it is not a regression.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Per-task security check (retro, recurring): S3 is reached only through one presigned URL per Job, signed by the reconciler; no credential or presigned query string in a log line, a status `reason` or an error message; the api imports neither `reconciler` nor `k8s`.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: interrogate 2026-10-29 act on 1; consider 1 (live presign expiry); builder Q10 yes
