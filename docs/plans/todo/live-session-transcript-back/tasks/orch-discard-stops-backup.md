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

## Acceptance conditions

- AC1: discarding a session whose sessions_backup is running records it failed with reason superseded_by_discard, deletes Job `agent-<slug>-sessions-backup`, and creates the final sessions save Job only once neither that Job nor a pod carrying the `sessions-backup` cache label of the session exists [evidence: test:tests/test_sessions_backup.py::test_discard_stops_running_backup_before_final_save]
- AC2: the final sessions save runs whenever save_skip allows it, whatever the sessions_backup record says (absent, saved, failed, skipped, running) [evidence: test:tests/test_sessions_backup.py::test_final_save_runs_whatever_the_live_backup]
- AC3: a crash after the superseded record is written and before the Job delete: the next discard tick deletes the backup Job and still waits for its pods before the final save [evidence: test:tests/test_sessions_backup.py::test_discard_backup_stop_crash_safe]
- AC4: when the backup pods outlive discard_quiesce_timeout_seconds from the supersede, the final save runs anyway and a warning names the session [evidence: test:tests/test_sessions_backup.py::test_backup_stop_wait_is_bounded]
- AC5: end to end: a live backup saves and PUTs the session's transcripts object, a turn completes, a second backup is running when the discard starts, the discard stops it, the final save PUTs the same object last, and a session created again with the same cache name restores (GET) exactly that object [evidence: test:tests/test_sessions_backup.py::test_live_backup_then_discard_final_save_restores]
- AC6: the discard never starts a live backup [evidence: test:tests/test_sessions_backup.py::test_discard_never_starts_a_live_backup]
- AC7: README states that the discard stops a running live backup before the final save, the whole sessions backup suite passes and lint passes [evidence: command:grep -q "superseded_by_discard" README.md && uv run --frozen pytest -q -p no:cacheprovider tests/test_sessions_backup.py tests/test_sessions_live_backup.py && mise run lint]

## Files

- `src/agents_orchestrator/reconciler/loop.py`
- `src/agents_orchestrator/reconciler/live_backup.py`
- `src/agents_orchestrator/reconciler/cache.py`
- `tests/test_sessions_backup.py`
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
