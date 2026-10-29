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

(review fix) Interrogate Act on 2: the change signal is an agent of the session `busy` now or its `agent_status.free_since`
(database `now()`) later than `last_saved.started_at`, never the wrapper-clock `turns.completed_at`, so long running turns are backed up too; still at most once per interval. Act on 1: `_converge` reloads the session (`_reload`) right before the backup step, so no backup write merges a stale `status.cache`. Acts: orch-sessions-live-backup.

### D2: Its own status record and Job name; the discard save stays one-shot

`status.cache.sessions_backup {state, started_at, finished_at, bytes, reason, job}` and Job name
`agent-<slug>-sessions-backup` (`CacheOp` action `backup`). Reusing `sessions_save` is rejected: it is
final (`cache.py:330-341`) and its Job name is adopted (`:377`), so the discard would skip its final save
or adopt a live Job. The run reuses the crash-safe `_begin/_start/_observe/_finish` pattern and
`render_cache_job(..., "save", url, "sessions")`; each new run replaces the previous record once the
previous Job is deleted. A failed run records `failed` with its reason and retries after the interval.

Amended 2026-10-29 by the planner (my call): a replaced record would hide the latest successful backup
after a failed run (against G4) and a failed or skipped run would reset the change signal, so idle
unbacked changes would never be retried. So `sessions_backup` also carries `last_saved {started_at,
finished_at, bytes}`, set from a run that ends `saved` and carried forward unchanged by every later run
until the next `saved`. The interval counts from the latest run's `started_at` (any outcome, so a
failure or a `shared_name` skip retries after the interval); the change signal is a turn of the
session's agents completed after `last_saved.started_at` (with no `last_saved`, any completed turn).
Acts: orch-sessions-live-backup, orch-backup-view-latest.

(review fix) Interrogate Act on 5: `CacheOp.action` stays `save` (one Job action contract: read-only mount, PUT, `saved`); the live run differs only in status key `sessions_backup`, Job name suffix `-sessions-backup` and cache label `sessions-backup` (my call, so neither run lists the other's pods). The change signal sentence above is replaced by D1's review fix. Acts: orch-sessions-live-backup AC19.

### D3: Discard removes a running backup first

In `_discard`, before the sessions save step, a running backup Job is deleted (foreground) and its record
marked `failed` with reason `superseded_by_discard`; the final save then runs as today. The quiesce
already stops the pods, so the final save carries the latest state. Alternative: wait for the backup
(bounded by `cache_timeout_seconds`, delays every discard). Direct PUT means a killed backup leaves the
previous object intact (`transfer.py:208`).

Amended 2026-10-29 by the planner (my call): `KubeApi.delete` deletes a Job with background
propagation (`k8s/kube.py:182-190`), so "foreground" is enforced by the discard itself: the record is
written `failed`/`superseded_by_discard` first, then the Job is deleted, and the final sessions save
starts only when neither the backup Job nor a pod carrying its cache label exists, so a killed backup's
PUT can never land after the final one. A crash between the record and the delete is redone by the next
tick (a non-running record whose Job still exists). The wait is bounded by
`discard_quiesce_timeout_seconds` from the supersede (the record's `finished_at`), after which the final
save runs and a warning is logged (anti-goal: no unbounded delay). Acts: orch-discard-stops-backup.

(review fix) Interrogate Act on 1: `_discard` reloads the session between the stop step and the final save, so the final save keeps `superseded_by_discard`. Consider 1 (my call): the bounded wait stays; the live run's presign expires `cache_timeout_seconds + 60` (covers its `activeDeadlineSeconds`), every other presign keeps `+ 600`; residual risk in Assumptions. Builder Q10: the stop step also handles a leftover `running` record when the interval is 0. Acts: orch-discard-stops-backup AC8-AC10.

### D4: Object name and the decouple migration

A live backup presigns exactly what the discard save would: `status.cache.sessions_object` when pinned.
While a session's decouple migration is pending or failed (decouple D7/D9) the backup does not run (reason
not recorded; it simply waits), so it never writes the legacy name the migration is about to copy. The
decouple migration's "no copy while a save run is `running`" guard (decouple interrogate item 4) also
counts a running live backup (fix-as-ac).

(review fix) Interrogate Act on 4: "reason not recorded; it simply waits" is replaced: while the migration is pending or failed the backup records `skipped` with reason `migration_pending`, written only on change (no churn), keeping `last_saved` and the previous `started_at` (my call: it never restarts the interval). Acts: orch-sessions-live-backup AC8.

### D5: Shared names

With a shared literal template, several live sessions pin one transcripts object; each live backup would
overwrite the others' with only its own pod dirs. A live backup is skipped (record `skipped`, reason
`shared_name`) while another live session (not discarded) pins the same `sessions_object`; the discard save
keeps today's last-writer-wins semantics (decouple Q1/Q10) (my call; Q4).

(review fix) Interrogate Act on 3 (builder Q9 overridden): the guard compares effective transcripts objects (pinned `sessions_object`, else the name the session will pin from its rendered `spec.cache.key`) against every row not yet purged, deleting and unconverged rows included. Consider 2: a backup already running when a peer row appears can still overwrite the shared object once, bounded by one backup's duration after the peer's row exists. Acts: orch-sessions-live-backup AC10, AC18.

### D6: Archive reads safe for live files

`cache/archive.py:_add` opens a regular file first and builds its tar header from the open descriptor
(`gettarinfo(fileobj=...)`, fstat), so an atomic replace (`os.replace`, the wrapper's events compaction,
settings rewrites) archives the old inode instead of failing the whole save (today `OSError: unexpected end
of data`, archive.py:116, `upload_failed: archive`). A `*.jsonl` member is cut at its last newline so an
in-progress append never leaves a torn final line (Claude Code's tolerance on `--resume` is unknown). This
applies to every save, discard included (my call: identical semantics for quiescent files).

Amended 2026-10-29 by the planner, pending open question Q6 (the plan follows its recommended answer):
"identical semantics for quiescent files" does not hold for a quiescent workspace `*.jsonl` file whose
last line has no trailing newline: the cut would silently drop that line from the user's workspace. So
the descriptor-based header (fstat, opened with `O_NOFOLLOW`, regular files only) applies to every save,
and the JSONL cut only to the transcripts archive: only the sessions Job carries `CACHE_TRIM_JSONL=true`
(absent means no cut, so the workdir Job env stays as it is), and `transfer.save` passes it to
`archive.pack(..., trim_jsonl=...)`. A "no" to Q6 drops the env variable and applies the cut to every save as first
written. Acts: orch-archive-live-files.

(review fix) Interrogate Act on 6: the open adds `O_NONBLOCK`, so a FIFO swapped in after the lstat never blocks the pack; it fails the fstat check and is skipped. Builder Q3 (my call): a file shrunk below its fstat size mid-read still fails the pack; the old object stays and the next interval retries. Acts: orch-archive-live-files AC5.

### D7: Visibility

`SessionView.backup.last_transcripts_backup` (`api/sessions.py:64-90`) becomes the newer saved record of
`sessions_save` and `sessions_backup`, with a field naming which (`final` or `live`). The discard dialog
(`agents-web/src/sessions/DiscardSessionDialog.tsx:105,136-139`) says the transcripts were last backed up at
that time and that the discard writes a final backup. openapi.json and the web's vendored schema follow.

Planner detail 2026-10-29 (my call): the naming field is `BackupRun.kind`, `"final"` (from
`sessions_save` in state `saved`) or `"live"` (from `sessions_backup.last_saved`); the newer by
`finished_at` wins, a tie goes to `final`. Acts: orch-backup-view-latest, web-discard-latest-backup.

### D8: Settings and deploy

`ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS` (default 1800; 0 disables live backups) in settings.py and README;
the chart passes it through `.Values.env`. agents-helmfile pins the new orchestrator and web images; no
value change needed for the default. Live check: after the apply, a running session gets a
`sessions_backup` record `saved` and the object's LastModified in S3 is recent (HEAD with the reconciler's
credentials is not available to agents; the check reads `status.cache` and the API field) (my call).

Planner detail 2026-10-29: decouple-s3-session-cache-fr has no agents-helmfile task (its Non-goals), so
this epic's orchestrator and web pins are the first to deploy its changes too, including its copy
migration of every pre-epic session at the first converge (open question Q7; the plan follows its
recommended answer). The live check therefore also reads each live session's `status.cache.migration`.
Apply order: orchestrator first, then web (the web reads the new required `BackupRun.kind`). The apply
runs under the deploy Lease `agents/agents-helmfile-apply` (user decision). Acts: helmfile-backup-pins,
helmfile-backup-live-check.

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

Retro proposals of the most recently done epics that bear on this epic (`ticket.py retro --history`),
recurring workflow ones first:

- Recurring (matrix-connector-agent-initi, deploy-safe-agent-sessions, parked-epic-stage): task files
  created with empty Steps. Every task here carries written Interfaces, Expected outcome, Steps and Notes
  before the gate. Acts: all tasks.
- Recurring (matrix-connector-agent-initi, deploy-safe-agent-sessions, file-editor-with-tabs-and-hi):
  defects passing per-task review, found only at the epic review; check the headline promise end to end
  and run the security checklist per task. Acts: orch-discard-stops-backup AC5 (live backup, discard,
  final save and restore in one test); every orchestrator task's Notes carry the per-task security check
  (no credential or presigned query in a log, reason or status; S3 only from the reconciler).
- Recurring (matrix-connector-agent-initi, deploy-safe-agent-sessions, file-editor-with-tabs-and-hi,
  file-download-in-file-browse): no Docker in the pod makes DB-backed tests CI-only. Acts:
  orch-archive-live-files runs fully locally; the DB-backed verifies of orch-sessions-live-backup,
  orch-discard-stops-backup and orch-backup-view-latest say so, and their reviewers read CI.
- Recurring (deploy-safe-agent-sessions, matrix-connector-agent-initi): a live apply surfaced defects
  tests did not; read `mise run diff` and render before the apply. Acts: helmfile-backup-live-check
  step 3.
- Recurring (deploy-safe-agent-sessions, file-editor-with-tabs-and-hi, matrix-connector-agent-initi):
  live apply and proof tasks run far over their seed. Acts: helmfile-backup-live-check points (5) and
  Notes.
- Recurring (file-editor-with-tabs-and-hi, markdown-rendering-in-chat): save the failing test name and
  the output tail before any rerun. Acts: all tasks' Notes.
- file-editor-with-tabs-and-hi: Harbor prunes image tags; check the pinned tags exist before the
  apply. Acts: helmfile-backup-live-check step 2.
- deploy-safe-agent-sessions: deploy-order coupling, the web must deploy after the orchestrator when it
  reads a new required field. Acts: helmfile-backup-live-check (orchestrator first, then web).
- matrix-connector-agent-initi: web `openapi/orchestrator.source` pinned an epic-branch commit, so the
  orchestrator PR needed a merge commit. Acts: web-discard-latest-backup Notes.
- deploy-safe-agent-sessions: `test_lightkube_default_client_uses_env_config` fails in-cluster,
  unrelated. Acts: orchestrator tasks' Notes, so it is not read as a regression.
- matrix-connector-agent-initi: render each container's env against the Settings pair checks. Not
  needed: the one new setting has a default and no pair; noted in orch-sessions-live-backup Notes.

Brief plan inputs (`.scratchpad/live-backup/brief-cartographer.md`):

- One-shot `sessions_save` and Job adoption (cache.py:330-341, :377) - own record and Job name (D2).
  fix-as-ac: orch-sessions-live-backup AC2.
- Discard must handle a running live Job - D3. fix-as-ac: orch-discard-stops-backup AC1, AC3.
- `last_transcripts_backup` reads only `sessions_save` (api/sessions.py:64-90) - D7. fix-as-ac:
  orch-backup-view-latest AC1, AC2.
- Decouple migration guard must include the live run; live run waits while migration pending - D4.
  fix-as-ac: orch-sessions-live-backup AC8 (waits while pending), AC9 (guard counts the live run).
- Archive fails on a file shrunk/replaced mid-read (archive.py:116) - D6. fix-as-ac:
  orch-archive-live-files AC1, AC2.
- reuse: `CacheRunner` `_begin/_start/_observe/_finish`, `render_cache_job(..., "save", url,
  "sessions")`, `save_skip(..., "sessions")`, the `pre_discard` DB-clock pattern, chart `.Values.env`
  (no chart change). Acts: orch-sessions-live-backup.
- do-not-build: S3 credentials outside the reconciler, a new archive format or temp object, wrapper
  changes, pre-roll gating. Placed in Non-goals, Anti-goals and task Notes.
- ideas rejected: "back up now" button and MCP tool (Non-goal, Q3); turn-end trigger (D1).

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 periodic, change-driven trigger | orch-sessions-live-backup |
| D2 own status record and Job name | orch-sessions-live-backup, orch-backup-view-latest |
| D3 discard removes a running backup first | orch-discard-stops-backup |
| D4 object name and the decouple migration | orch-sessions-live-backup |
| D5 shared names | orch-sessions-live-backup |
| D6 archive reads safe for live files | orch-archive-live-files |
| D7 visibility | orch-backup-view-latest, web-discard-latest-backup |
| D8 settings and deploy | orch-sessions-live-backup, helmfile-backup-pins, helmfile-backup-live-check |

## Review focus

- The discard path: the final save always runs after a live backup Job is gone; crash between delete and
  save.
- Status-guarded, crash-safe records: a reconciler restart mid-backup adopts or cleans the backup Job and
  never the save Job.
- The change signal and interval use the database clock; no backup storm for idle sessions.
- Archive change keeps every existing archive test green (symlink escape, excludes, size cap).

## Left to the builder

- Module placement (cache.py vs a new `reconciler/live_backup.py`), helper names, the SQL for the
  busy-or-`free_since` check (review fix of D1), test file split, within D1-D8.
- Builder questions settled (`.scratchpad/live-backup/builder-check.md`, my call): Q1 orch-archive-live-files may
  start before the blockers land, the rest waits; Q2 superseded by D1's review fix; Q3 yes (D6); Q4 the pins
  are the 7-character short merge sha; Q5 the orchestrator session amends the placeholders via `ticket.py amend`
  after both PRs merge; Q6 one agents-orchestrator PR for all four orch tasks, merged before the web task; Q7
  the web AC5 commands are the real check and its verify matches; Q8 helmfile-backup-live-check is
  orchestrator-session work; Q9 overridden, deleting rows count (D5); Q10 yes to both (D3, orch-sessions-live-backup AC7).

## Assumptions and unknown facts

- Claude Code's `--resume` tolerance of a torn final JSONL line: unknown; D6 removes the case.
- Backup Job cost: one Job pod with a 5 GiB emptyDir per changed session per interval; acceptable at the
  current session count (a handful) (my call).
- (review fix) Residual late PUT (interrogate Consider 1, my call): a backup pod still terminating after the
  bounded discard wait can PUT after the final save only while its URL is valid, within
  `cache_timeout_seconds + 60` of its presign; accepted rather than delaying every discard up to 40 min.
- (review fix) `free_since` also moves on a booting-to-idle transition, so a pod roll can make one extra backup
  due after the interval; accepted, bounded by the interval (my call).
- (review fix) Builder Q3: a file shrunk mid-read fails that pack; retried next interval (my call).

## Open questions

- Q1: Back up each live session's transcripts every 30 minutes, only when a turn completed since the last backup? [recommended: yes]
- Q2: Transcripts only, the workspace keeps its discard-time save? [recommended: yes]
- Q3: No "back up now" button or tool in this epic? [recommended: yes]
- Q4: Skip the live backup while another live session shares the same cache name? [recommended: yes]
- Q5: Close the "row stays sent after its turn failed" item as by design (sent is final, the turn shows the outcome, the cause was the wrapper wedge fixed in 0.3.3)? [recommended: yes]
- Q6: Cut a torn last JSONL line only in the Claude transcripts archive, never in the workspace archive, so a workspace .jsonl file without a trailing newline is never truncated? (D6 amendment) [recommended: yes]
- Q7: The helmfile pins of this epic also deploy decouple-s3-session-cache-fr, which has no deploy task of its own, so its copy migration of every existing session runs at this apply; deploy both together and check the migration records in the live check? (D8) [recommended: yes]

## Irreversible operations in scope

- Live backups overwrite each session's S3 transcripts object (the same object the discard writes); a
  failed backup leaves the old object (direct PUT after a full pack).
- Releases: orchestrator and web images; helmfile apply under the deploy lease.
