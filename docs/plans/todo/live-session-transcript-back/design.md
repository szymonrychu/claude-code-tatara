# Live session transcript backup design

## Summary

The reconciler backs up each live session's Claude transcripts to S3 on a timer, not only at discard.
For a converged session whose conversation changed since its last backup (a turn completed after it),
at most every `ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS` (default 1800), it runs a backup Job that tars
`/sessions` from the ReadWriteMany PVC beside the running pods and overwrites the session's transcripts
object (the one the decouple epic pins in `status.cache.sessions_object`). The run has its own status
record `status.cache.sessions_backup` and Job name, so the one-shot discard save stays untouched and final;
the discard removes a running backup Job first. Archive reads become safe for live files (read through the
open file, trim a torn last JSONL line). The API's `last_transcripts_backup` shows the newer of the live and
final backups. Discovery: `.scratchpad/live-backup/brief-cartographer.md`.

## Intent and why

mx-34 #234 (2026-10-28): "The live-session backup trigger: yes ... The user lost sessions in the incident,
so a live backup is worth having." Origin #232: "there's no backup trigger for a live session
(last_transcripts_backup=null)". The PVC survives pod rolls but is not a backup; the S3 object is written
only by the discard (`reconciler/cache.py:315 save_step`, one-shot by `sessions_save`).

The bundled item "message row stays status='sent' after its turn failed" (#234 point 3) was investigated:
`sent` is final by design (`0001_init.sql:51`, README.md:575), the ingester records the turn as
`interrupted` and never touches message rows (`ingester/loop.py:250-267`), and the case was the wrapper
queued_command wedge fixed in wrapper 0.3.3 (`.scratchpad/live-backup/sent-row-root-cause.md`). No orchestrator
change; closed by open question Q5.

## Goals

As in README.md G1-G5.

## Non-goals

As in README.md: no live workspace backup, no versioned objects or retention, no on-demand trigger, no
pre-roll gating, no message status change, no wrapper/plugins/common change.

## Anti-goals

- The discard's final save skipped, delayed without bound or overwritten by a later live backup.
- A failed or partial live backup replacing a good object.
- A live backup that pauses, scales or restarts the session's pods.
- S3 credentials outside the reconciler, or the api calling S3 (`test_api_never_imports_k8s_or_wrapper`).
- A live backup writing a transcripts name the decouple migration has not settled (the timing trap of
  decouple D7/D9).
- Unbounded Job churn: idle sessions backed up again and again.

## Constraints

- AGENTS.md: services over HTTP; one writer per table (the reconciler is the only writer of
  `sessions.status`); Python and TypeScript; no compatibility shims.
- The reconciler is the singleton S3 credential holder and Job creator (`chart/.../deployment.yaml:82-91`,
  `role.yaml:24-26`).
- PVC `ReadWriteMany` (`k8s/render.py:297`), so a Job can mount `sessions` read-only beside running pods,
  exactly as the discard save Job does (`render_cache_job`, cache.py:126-151).
- Blocker: decouple-s3-session-cache-fr (approved, unbuilt) changes the same cache files and pins
  `sessions_object`; this epic builds after it lands on main and uses its names. No SQL migration is planned
  here (status is jsonb); if a builder finds one is needed, it takes the next free number at build time
  (0010, 0012 and the decouple epic's number are claimed).
- The DB-backed reconciler tests need Docker (CI only in agent pods); the archive and render tests run
  locally (`test_cache_archive.py`, `test_cache_jobs_render.py`).

## Decisions

### D1: Trigger: periodic and change-driven, in the reconciler

In `_converge`, after the bootstrap step, a new `CacheRunner.sessions_backup_step` starts a backup when all
hold: the cache is configured, `save_skip(..., "sessions")` is None (the same eligibility as the discard
save), the session's transcripts name is settled (D4), no backup run is `running`, the interval since the
last backup run's `started_at` has passed (database clock, like `pre_discard`'s `next_at`), and a turn of
the session's agents completed after that `started_at` (or there was no backup yet and a turn completed).
Alternatives: on demand only (needs an api-to-reconciler signal and UI; the user asked for safety, not a
button; Q3); before pod rolls (the PVC survives rolls, low value); at every turn end (Job bursts on busy
sessions). Interval default 1800 s (my call; Q1).

### D2: Its own status record and Job name; the discard save stays one-shot

`status.cache.sessions_backup {state, started_at, finished_at, bytes, reason, job}` and Job name
`agent-<slug>-sessions-backup` (`CacheOp` action `backup`). Reusing `sessions_save` is rejected: it is
final (`cache.py:330-341`) and its Job name is adopted (`:377`), so the discard would skip its final save
or adopt a live Job. The run reuses the crash-safe `_begin/_start/_observe/_finish` pattern and
`render_cache_job(..., "save", url, "sessions")`; each new run replaces the previous record once the
previous Job is deleted. A failed run records `failed` with its reason and retries after the interval.

### D3: Discard removes a running backup first

In `_discard`, before the sessions save step, a running backup Job is deleted (foreground) and its record
marked `failed` with reason `superseded_by_discard`; the final save then runs as today. The quiesce
already stops the pods, so the final save carries the latest state. Alternative: wait for the backup
(bounded by `cache_timeout_seconds`, delays every discard). Direct PUT means a killed backup leaves the
previous object intact (`transfer.py:208`).

### D4: Object name and the decouple migration

A live backup presigns exactly what the discard save would: `status.cache.sessions_object` when pinned.
While a session's decouple migration is pending or failed (decouple D7/D9) the backup does not run (reason
not recorded; it simply waits), so it never writes the legacy name the migration is about to copy. The
decouple migration's "no copy while a save run is `running`" guard (decouple interrogate item 4) also
counts a running live backup (fix-as-ac).

### D5: Shared names

With a shared literal template, several live sessions pin one transcripts object; each live backup would
overwrite the others' with only its own pod dirs. A live backup is skipped (record `skipped`, reason
`shared_name`) while another live session (not discarded) pins the same `sessions_object`; the discard save
keeps today's last-writer-wins semantics (decouple Q1/Q10) (my call; Q4).

### D6: Archive reads safe for live files

`cache/archive.py:_add` opens a regular file first and builds its tar header from the open descriptor
(`gettarinfo(fileobj=...)`, fstat), so an atomic replace (`os.replace`, the wrapper's events compaction,
settings rewrites) archives the old inode instead of failing the whole save (today `OSError: unexpected end
of data`, archive.py:116, `upload_failed: archive`). A `*.jsonl` member is cut at its last newline so an
in-progress append never leaves a torn final line (Claude Code's tolerance on `--resume` is unknown). This
applies to every save, discard included (my call: identical semantics for quiescent files).

### D7: Visibility

`SessionView.backup.last_transcripts_backup` (`api/sessions.py:64-90`) becomes the newer saved record of
`sessions_save` and `sessions_backup`, with a field naming which (`final` or `live`). The discard dialog
(`agents-web/src/sessions/DiscardSessionDialog.tsx:105,136-139`) says the transcripts were last backed up at
that time and that the discard writes a final backup. openapi.json and the web's vendored schema follow.

### D8: Settings and deploy

`ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS` (default 1800; 0 disables live backups) in settings.py and README;
the chart passes it through `.Values.env`. agents-helmfile pins the new orchestrator and web images; no
value change needed for the default. Live check: after the apply, a running session gets a
`sessions_backup` record `saved` and the object's LastModified in S3 is recent (HEAD with the reconciler's
credentials is not available to agents; the check reads `status.cache` and the API field) (my call).

## Research

| Lens | Ran / skipped | Adopted | Rejected |
|---|---|---|---|
| start-discovery (codebase-cartographer, opus) | ran 2026-10-29, `.scratchpad/live-backup/brief-cartographer.md`, on top of `.scratchpad/s3-cache/brief-cartographer.md` | CacheRunner run pattern, Job render, own status key, discard removal, archive fstat fix | pre-roll gating; reusing `sessions_save` |
| research-code-internal | covered by the cartographer's Plan inputs (one repo, reuse listed); no separate reuse-hunter (my call: the change extends one module family it mapped) | reuse list above | - |
| research-docs | skipped: no new library or platform API; tarfile `gettarinfo(fileobj=)` is stdlib behaviour already used | - | - |
| research-code-external | skipped: no open fork that prior art would settle | - | - |
| research-papers | skipped: no scientific core | - | - |
| start-debugging (sent-row item, opus) | ran read-only, `.scratchpad/live-backup/sent-row-root-cause.md`: no orchestrator root cause | close as by design (Q5) | a new `answered`/`failed` message status |

## Research inputs

- One-shot `sessions_save` and Job adoption (cache.py:330-341, :377) - own record and Job name (D2).
- Discard must handle a running live Job - D3.
- `last_transcripts_backup` reads only `sessions_save` (api/sessions.py:64-90) - D7.
- Decouple migration guard must include the live run; live run waits while migration pending - D4.
- Archive fails on a file shrunk/replaced mid-read (archive.py:116) - D6.

## Decision coverage

Filled by the planner from the task slugs.

## Review focus

- The discard path: the final save always runs after a live backup Job is gone; crash between delete and
  save.
- Status-guarded, crash-safe records: a reconciler restart mid-backup adopts or cleans the backup Job and
  never the save Job.
- The change signal and interval use the database clock; no backup storm for idle sessions.
- Archive change keeps every existing archive test green (symlink escape, excludes, size cap).

## Left to the builder

- Module placement (cache.py vs a new `reconciler/live_backup.py`), helper names, the SQL for the "turn
  completed since" check, test file split, within D1-D8.

## Assumptions and unknown facts

- Claude Code's `--resume` tolerance of a torn final JSONL line: unknown; D6 removes the case.
- Backup Job cost: one Job pod with a 5 GiB emptyDir per changed session per interval; acceptable at the
  current session count (a handful) (my call).

## Open questions

- Q1: Back up each live session's transcripts every 30 minutes, only when a turn completed since the last backup? [recommended: yes]
- Q2: Transcripts only, the workspace keeps its discard-time save? [recommended: yes]
- Q3: No "back up now" button or tool in this epic? [recommended: yes]
- Q4: Skip the live backup while another live session shares the same cache name? [recommended: yes]
- Q5: Close the "row stays sent after its turn failed" item as by design (sent is final, the turn shows the outcome, the cause was the wrapper wedge fixed in 0.3.3)? [recommended: yes]

## Irreversible operations in scope

- Live backups overwrite each session's S3 transcripts object (the same object the discard writes); a
  failed backup leaves the old object (direct PUT after a full pack).
- Releases: orchestrator and web images; helmfile apply under the deploy lease.
