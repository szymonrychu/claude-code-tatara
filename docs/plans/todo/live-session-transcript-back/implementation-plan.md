# Live session transcript backup implementation plan

## Agreed rung

Not agreed yet: a draft migrated from the epic's tasks; the plan-writer revises it after the gate.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: orch archive live files

- Status: todo
- Files: `src/agents_orchestrator/cache/archive.py`, `src/agents_orchestrator/cache/transfer.py`, `src/agents_orchestrator/reconciler/cache.py`, `tests/test_cache_archive.py`, `tests/test_cache_cli.py`, `tests/test_sessions_backup.py`, `MEMORY.md`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_archive.py tests/test_cache_cli.py tests/test_cache_jobs_render.py tests/test_sessions_backup.py::test_sessions_save_job_render && mise run lint`
- Verified head: none

#### Requirement

User request (mx-34 #234, 2026-10-28, relaying the user's priorities), verbatim: "The live-session backup trigger: yes, take it after the paste-.env bug, as a small start-development epic. The user lost sessions in the incident, so a live backup is worth having." Origin (mx-34 #232), verbatim: "there's no backup trigger for a live session (last_transcripts_backup=null)".

README Goal G3, verbatim: "a live backup taken while files are appended or atomically replaced succeeds and restores into a session that resumes (no torn final JSONL line, no failure on a replaced file)."

Design D6, verbatim: "`cache/archive.py:_add` opens a regular file first and builds its tar header from the open descriptor (`gettarinfo(fileobj=...)`, fstat), so an atomic replace (`os.replace`, the wrapper's events compaction, settings rewrites) archives the old inode instead of failing the whole save (today `OSError: unexpected end of data`, archive.py:116, `upload_failed: archive`). A `*.jsonl` member is cut at its last newline so an in-progress append never leaves a torn final line (Claude Code's tolerance on `--resume` is unknown). This applies to every save, discard included (my call: identical semantics for quiescent files)."

Design D6 amendment (planner, 2026-10-29, open question Q6, planned on its recommended answer), verbatim: "the descriptor-based header (fstat, opened with `O_NOFOLLOW`, regular files only) applies to every save, and the JSONL cut only to the transcripts archive: only the sessions Job carries `CACHE_TRIM_JSONL=true` (absent means no cut, so the workdir Job env stays as it is), and `transfer.save` passes it to `archive.pack(..., trim_jsonl=...)`. A "no" to Q6 drops the env variable and applies the cut to every save as first written."

Test no longer accurate and changed: tests/test_sessions_backup.py::test_sessions_save_job_render asserts that the sessions Job env equals the workdir Job env except `CACHE_DIR` and `CACHE_EXCLUDE`; `CACHE_TRIM_JSONL` now differs by target by design (D6 amendment), so it joins the compared-out keys and the test asserts `true` for the sessions Job and its absence from the workdir Job.

Review fix (interrogate 2026-10-29, Act on 6, FIFO swap hangs the pack): `os.open(..., O_RDONLY | O_NOFOLLOW)` blocks on a FIFO swapped in after the lstat, before the fstat type check. The open adds `O_NONBLOCK` (`os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK`), so a FIFO or other non-regular entry swapped in is opened without blocking, fails the fstat regular-file check and is skipped; the pack completes.

#### Acceptance conditions

- AC1: a regular file atomically replaced (os.replace) after the walk listed it and before its content is read is archived with the content of the inode that was opened, and the pack succeeds [evidence: test:tests/test_cache_archive.py::test_replaced_file_archives_opened_inode]
- AC2: a file that grows while it is packed is archived with exactly the size its open descriptor reported at open, and the pack succeeds [evidence: test:tests/test_cache_archive.py::test_growing_file_archived_at_open_size]
- AC3: with trim_jsonl=True a member whose name ends in `.jsonl` and whose content does not end in a newline is cut after its last newline (a file with no newline gives an empty member), a `.jsonl` file ending in a newline and every other file are archived byte for byte [evidence: test:tests/test_cache_archive.py::test_trim_jsonl_cuts_torn_last_line]
- AC4: with trim_jsonl=False a `.jsonl` file without a trailing newline is archived byte for byte [evidence: test:tests/test_cache_archive.py::test_workspace_jsonl_never_trimmed]
- AC5: a path that is a symlink, a FIFO or otherwise not a regular file at open time (swapped in after the lstat) is never followed or read, the open of a FIFO swapped in never blocks (O_NONBLOCK) and the pack completes, and a file removed before its open is skipped as before (interrogate Act on 6) [evidence: test:tests/test_cache_archive.py::test_open_never_follows_or_blocks_on_swapped_in_entry]
- AC6: the sessions save Job carries CACHE_TRIM_JSONL `true`, the workdir save Job has no CACHE_TRIM_JSONL, every other env entry unchanged [evidence: test:tests/test_sessions_backup.py::test_sessions_save_job_render]
- AC7: `orch cache save` passes CACHE_TRIM_JSONL `true` to archive.pack as trim_jsonl=True, an absent CACHE_TRIM_JSONL as trim_jsonl=False, and any other value fails before any request [evidence: test:tests/test_cache_cli.py::test_save_trim_jsonl_env]
- AC8: every archive and CLI test passes, MEMORY.md records the descriptor-based pack and the transcripts-only cut, and lint passes [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_archive.py tests/test_cache_cli.py && grep -q "CACHE_TRIM_JSONL" MEMORY.md && mise run lint]

#### Files

- `src/agents_orchestrator/cache/archive.py`
- `src/agents_orchestrator/cache/transfer.py`
- `src/agents_orchestrator/reconciler/cache.py`
- `tests/test_cache_archive.py`
- `tests/test_cache_cli.py`
- `tests/test_sessions_backup.py`
- `MEMORY.md`

#### Interfaces

- `cache/archive.py:pack(workdir, out, *, exclude, max_bytes, trim_jsonl: bool) -> Packed`: `trim_jsonl` is keyword-only and required (no default: both callers pass it).
- `cache/archive.py:_add`: lstat classifies the entry as today (directory, regular file, symlink with the escape check, others skipped); a regular file is then opened with `os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)` (`O_NONBLOCK`: review fix, interrogate Act on 6, so a FIFO swapped in never blocks the open), `os.fstat` must still say regular (else closed and skipped), and the tar header comes from `tar.gettarinfo(arcname=rel, fileobj=<the open file>)`; `FileNotFoundError` (and `ELOOP` from a symlink swapped in) skip the entry as today.
- JSONL cut: with `trim_jsonl`, a member whose name ends in `.jsonl` gets `size` set to the offset just after the last `\n` within the fstat size (0 when there is none) and exactly those bytes are written.
- `cache/transfer.py:save`: reads `CACHE_TRIM_JSONL`: absent means false; present it parses like `CACHE_VERIFY_TLS` (`true` or `false`, case-insensitive, stripped; anything else is a bad env that fails before any request) and passes it to `archive.pack`.
- `reconciler/cache.py:render_cache_job`: env `CACHE_TRIM_JSONL` `"true"` is added to the sessions save Job only (a restore does not pack); every other Job env is unchanged, so `tests/test_cache_jobs_render.py::test_job_env_has_no_credentials` (the exact workdir env list) stays as it is.

#### Expected outcome

A transcripts save that runs while the wrapper compacts `events.jsonl` with `os.replace` or rewrites its settings, or while Claude appends to a JSONL transcript, succeeds; every transcripts JSONL member ends at a newline. A workspace save archives every file byte for byte, as before. Symlinks are never followed.

#### Steps

- Read `cache/archive.py`, `cache/transfer.py` (`save`, the `CACHE_VERIFY_TLS` parsing), `reconciler/cache.py:render_cache_job`, `tests/test_cache_archive.py`, `tests/test_cache_cli.py` (`test_save_saved`, `test_bad_verify_tls_fails_before_any_request`) and `tests/test_sessions_backup.py::test_sessions_save_job_render` in one pass.
- Red: add the tests named in AC1-AC5 to tests/test_cache_archive.py (simulate the replace, the growth and the FIFO swap (`os.mkfifo` in place of the file after the lstat, no writer) deterministically, for example by monkeypatching `os.open` or `tarfile.TarFile.gettarinfo` to act between the lstat and the read, never with sleeps), AC7 to tests/test_cache_cli.py, and change `test_sessions_save_job_render` as the Requirement names (AC6); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_archive.py tests/test_cache_cli.py tests/test_sessions_backup.py::test_sessions_save_job_render`; expect the new tests to fail (AC1 with `OSError: unexpected end of data`, the others on the missing parameter or env).
- Green: change `_add`, `pack`, `transfer.save` and `render_cache_job`; rerun the verify; expect every test passed (all of these run locally, no Docker needed) and lint exit 0.
- Add the MEMORY.md entry (dated, with the why: an atomic replace failed the whole save; the cut is transcripts-only so a workspace file is never truncated, Q6); `mise run lint`; expect exit 0.

#### Notes

- (my call, builder Q1) this task needs none of the blockers (decouple-s3-session-cache-fr, hive-decoupling, slash-commands-from-chat) and may start before they land on main; every other task of the epic waits until they have landed.
- (my call, builder Q3) a file truncated below its fstat size mid-read still makes tarfile raise and the whole pack fail, as today; only growth and replace are made safe; the old object stays and the next interval retries (design Assumptions).
- Existing archive tests must stay green unchanged: symlink escape, excludes, size cap (`TooLarge`), unpack safety (design Review focus).
- Reading a large JSONL into memory to find the last newline is not needed: scan backwards from the fstat size with `os.pread` in chunks; the builder picks the chunk size.
- The wrapper tolerates a torn final line in its own `turns.jsonl` (brief section 2); Claude Code's own tolerance on `--resume` is unknown, hence the cut.
- Q6 is open; the plan follows its recommended answer. A "no" removes `CACHE_TRIM_JSONL` and applies the cut to every save (this task is amended before it starts).
- Base: this epic builds after decouple-s3-session-cache-fr, hive decoupling and slash commands from chat have landed on main; rebase onto main first and use the decouple names as they landed (`presign.sessions_object_name`, `status.cache.sessions_object`, the `cache_migration` pending predicate, `CacheRunner._begin` pinning). No SQL migration is planned; if one proves necessary it takes the next free number on main at build time (`<MIGRATION>`), and the builder raises it as a question first.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST); it is not a regression.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Per-task security check (retro, recurring): S3 is reached only through one presigned URL per Job, signed by the reconciler; no credential or presigned query string in a log line, a status `reason` or an error message; the api imports neither `reconciler` nor `k8s`.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner: CACHE_TRIM_JSONL only on the sessions save Job, absent means no cut, so the exact workdir env test stays accurate

- 2026-10-29 amended: interrogate 2026-10-29 act on 6

### S2: orch sessions live backup

- Status: todo
- Files: `src/agents_orchestrator/reconciler/live_backup.py`, `src/agents_orchestrator/reconciler/cache.py`, `src/agents_orchestrator/reconciler/loop.py`, `src/agents_orchestrator/reconciler/cache_migration.py`, `src/agents_orchestrator/settings.py`, `tests/test_sessions_live_backup.py`, `README.md`, `MEMORY.md`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_sessions_live_backup.py tests/test_cache_save.py tests/test_cache_migration.py tests/test_settings.py && mise run lint`
- Verified head: none

#### Requirement

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

Review fix (interrogate 2026-10-29, Act on 1, stale `status.cache` writes): `CacheRunner._write` merges from `session.status["cache"]` and replaces the whole key (reconciler/cache.py:541-544), and `_converge` discards `restore_step`'s result (loop.py:266), so a backup write from a stale session could put back a finished restore as `running`, undo a decouple repoint or revert another run's record. `_converge` reloads the session (`_reload`, as `_discard` does at loop.py:442) immediately before `sessions_backup_step`, so every backup write merges into the `status.cache` the database holds.

Review fix (interrogate 2026-10-29, Act on 2, change signal in database time, covering running turns): `turns.completed_at` is the wrapper's timestamp (ingester/loop.py:261) and a turn running for hours never completes, so the change signal no longer reads `turns`. It replaces "a turn of the session's agents completed after `last_saved.started_at`" in D1 and the D2 amendment: a backup is due when an agent of the session is `busy` now (`agent_status.state`), or an agent went idle after the last backup, that is its `agent_status.free_since` (set from the database `now()`, db/status.py:96,136) is later than `last_saved.started_at` (with no `last_saved`: an agent `busy` now or any agent with `free_since` set). Still at most once per interval from the latest run's `started_at`. This supersedes builder question Q2.

Review fix (interrogate 2026-10-29, Act on 3, shared-name guard misses peers; builder Q9 overridden): the guard compares this session's effective transcripts object (its pinned `status.cache.sessions_object`, else the name it will pin, derived from its rendered `spec.cache.key` by the decouple naming function) with the effective transcripts object of every other `sessions` row not yet purged, rows with `desired` deleting and unconverged rows (no `sessions_object` yet) included. This replaces "another live session (not discarded) pins the same `sessions_object`" in D5.

Review fix (interrogate 2026-10-29, Act on 4, silent wait on a failed migration): while the session's decouple migration is pending or failed, the backup records `sessions_backup` `skipped` with reason `migration_pending` instead of waiting without a record (this replaces "reason not recorded; it simply waits" in D4). The record is written only when it changes (a record already `skipped`/`migration_pending` is not rewritten, so no status churn); it keeps `last_saved` and the previous record's `started_at` (null when there was none), so it never restarts the interval (my call).

Review fix (interrogate 2026-10-29, Act on 5, one Job action contract): `render_cache_job`, `_start` and `_finish_from_log` key on `action == "save"` (read-only mount, PUT, `saved`), so `CacheOp.action` stays `save` for the live run (this replaces "`CacheOp` action `backup`" in D2). The live run differs from the discard sessions save only in its status key `sessions_backup`, its Job name suffix `-sessions-backup` and, so neither run lists, adopts or deletes the other's pods, its cache label `sessions-backup` (my call, as AC1 and AC2 already require).

Builder question Q10 (my call: yes to both): with `ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS` 0 an existing `sessions_backup` record is left as it is (no cleanup); the discard's stop step (orch-discard-stops-backup) still handles a leftover `running` record.

#### Acceptance conditions

- AC1: a converged session (sessions restore `restored`, pods running) with an agent that went idle (agent_status.free_since set) and no sessions_backup record gets Job `agent-<slug>-sessions-backup` (cache label `sessions-backup`, command `orch cache save`, PVC subPath `sessions` read-only) presigning a PUT of status.cache.sessions_object; status.cache.sessions_backup goes running then saved with bytes and last_saved; the StatefulSet replicas and the agent pods are unchanged throughout [evidence: test:tests/test_sessions_live_backup.py::test_converged_session_backed_up_beside_running_pods]
- AC2: a live backup never writes status.cache.sessions_save and never creates, adopts or deletes Job `agent-<slug>-sessions-save`, even when a Job of that name exists [evidence: test:tests/test_sessions_live_backup.py::test_backup_never_touches_sessions_save]
- AC3: after a saved backup no new run starts before ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS have passed since the latest run's started_at (database clock); after that a new run starts only while an agent of the session is busy now or an agent's agent_status.free_since is later than last_saved.started_at; an idle session (every agent idle, free_since before last_saved.started_at) gets no Job across many ticks past the interval [evidence: test:tests/test_sessions_live_backup.py::test_interval_and_change_gate]
- AC4: a failed run (Job create failure, failed Job, timeout) records failed with its reason, keeps the previous last_saved, and the next run starts only after the interval, even with no new turn [evidence: test:tests/test_sessions_live_backup.py::test_failed_backup_keeps_last_saved_and_retries_after_interval]
- AC5: a new run starts only once the previous run's Job is gone: a finished record whose Job still exists gets that Job deleted and no new run in that tick [evidence: test:tests/test_sessions_live_backup.py::test_new_run_waits_for_previous_job_deleted]
- AC6: crash safety: a running record with no Job (crash before the create) creates the backup Job; an existing backup Job with job unset (crash after the create) is adopted; neither path touches the sessions save Job [evidence: test:tests/test_sessions_live_backup.py::test_backup_crash_safety]
- AC7: no backup Job and no record when spec.cache is unset, the cache is not configured, the interval setting is 0, or save_skip(..., "sessions") returns a reason (never converged, restore running, restore failed); with the interval 0 an existing sessions_backup record is left as it is (builder Q10) [evidence: test:tests/test_sessions_live_backup.py::test_backup_eligibility]
- AC8: while the session's decouple migration is pending or failed (cache_migration pending predicate) no backup Job is created and sessions_backup records skipped with reason migration_pending, keeping last_saved and the previous started_at; the record is written once and not rewritten on later ticks while it stays so; once sessions_object is pinned the backup presigns exactly that object (interrogate Act on 4) [evidence: test:tests/test_sessions_live_backup.py::test_backup_waits_for_pending_migration]
- AC9: while a sessions_backup run is running the decouple migration copies and repoints nothing, as for a running save [evidence: test:tests/test_sessions_live_backup.py::test_migration_waits_for_running_backup]
- AC10: while another session row not yet purged has the same effective transcripts object (its pinned sessions_object, else the name it will pin from its rendered spec.cache.key) the backup records skipped with reason shared_name, keeps last_saved and creates no Job; it is checked again after the interval and runs once no such row remains [evidence: test:tests/test_sessions_live_backup.py::test_shared_name_skipped]
- AC11: Settings has sessions_backup_interval_seconds from ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS, default 1800, 0 accepted (disables), a negative value refused [evidence: test:tests/test_sessions_live_backup.py::test_backup_interval_setting]
- AC12: README documents ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS [evidence: test:tests/test_settings.py::test_env_names_documented_in_readme]
- AC13: README documents status.cache.sessions_backup and its last_saved, and MEMORY.md records the live backup decisions [evidence: command:grep -q "sessions_backup" README.md && grep -q "last_saved" README.md && grep -q "sessions_backup" MEMORY.md]
- AC14: the existing save, migration and settings suites and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_save.py tests/test_cache_migration.py tests/test_settings.py && mise run lint]
- AC15: a tick in which the sessions restore turns restored and a backup then starts leaves status.cache.sessions_restore restored and every other status.cache key as the database holds it after the backup's writes (_converge reloads the session before the backup step; interrogate Act on 1) [evidence: test:tests/test_sessions_live_backup.py::test_backup_start_keeps_fresh_status_cache]
- AC16: a turn that stays running (an agent busy, no turn completed) across several intervals gets one backup run per interval while it runs (interrogate Act on 2) [evidence: test:tests/test_sessions_live_backup.py::test_long_running_turn_backed_up_each_interval]
- AC17: the change signal reads only database-clock values: an agent whose free_since is later than last_saved.started_at triggers a run even when its turns.completed_at (wrapper clock) is earlier, and a turns.completed_at later than last_saved.started_at with every free_since earlier and no agent busy triggers none (interrogate Act on 2) [evidence: test:tests/test_sessions_live_backup.py::test_change_signal_uses_database_clock]
- AC18: the shared-name skip also counts a row with desired deleting not yet purged and an unconverged row with no sessions_object whose rendered spec.cache.key gives the same transcripts name (interrogate Act on 3) [evidence: test:tests/test_sessions_live_backup.py::test_shared_name_counts_deleting_and_unconverged_peers]
- AC19: the live run is a save action: its Job mounts the sessions subPath read-only, its URL is a presigned PUT, and a finished run records saved; only its status key (sessions_backup), Job name suffix (-sessions-backup) and cache label (sessions-backup) differ from the discard sessions save (interrogate Act on 5) [evidence: test:tests/test_sessions_live_backup.py::test_live_run_is_a_save_action]

#### Files

- `src/agents_orchestrator/reconciler/live_backup.py`
- `src/agents_orchestrator/reconciler/cache.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `src/agents_orchestrator/reconciler/cache_migration.py`
- `src/agents_orchestrator/settings.py`
- `tests/test_sessions_live_backup.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

- `settings.py:Settings.sessions_backup_interval_seconds: int` (env `ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS`), default 1800, `ge=0`; 0 disables live backups.
- `CacheRunner.sessions_backup_step(session) -> None` (in `reconciler/cache.py`, or in a new `reconciler/live_backup.py` the runner delegates to; the builder's choice, design "Left to the builder"), called by `Reconciler._converge` after `_bootstrap_wrapper_sessions` on every converge tick, on a session reloaded (`_reload`) immediately before the call (review fix, interrogate Act on 1); never called from `_discard`.
- Job: `agent-<slug>-sessions-backup`, labels `session_labels(slug)` plus `agents.szymonrichert.pl/cache: sessions-backup`, rendered from `render_cache_job(session, settings, "save", url, "sessions")` with only the name and cache label changed (command stays `orch cache save`); `CacheOp.action` stays `save` (review fix, interrogate Act on 5): a live marker on `CacheOp` (the builder names it) changes only `status_key` (`sessions_backup`), `job_name` (`-sessions-backup`) and `label` (`sessions-backup`), so the read-only mount, the PUT presign and the `saved` outcome are the save's own code paths; the presigned PUT names exactly the object the discard sessions save would presign at that moment (`status.cache.sessions_object`, pinned through the same `_begin` code path when unpinned and no migration is pending).
- `status.cache.sessions_backup`: `{state: "running"|"saved"|"failed"|"skipped", started_at, finished_at, bytes, reason, job, last_saved: {started_at, finished_at, bytes} | null}`; written through the runner's `_write` (the reconciler is the only writer of `sessions.status`). Contract change for `orch-session-status-cache` recorded by the orchestrator.
- Change signal (review fix, interrogate Act on 2): an `agent_status` row of an agent of this session with `state = 'busy'` now, or with `free_since` later than `last_saved.started_at` (with no `last_saved`: `busy` now or any non-null `free_since`); both sides are database-clock values; `turns.completed_at` (wrapper clock) is never read; the SQL is the builder's (design "Left to the builder").
- Shared name (review fix, interrogate Act on 3; builder Q9 overridden): the effective transcripts object of a session is its `status.cache.sessions_object` when pinned, else the name it will pin, derived from its rendered `spec.cache.key` by the decouple naming function as landed; the backup is skipped while any other `sessions` row not yet purged (any `desired`, deleting and unconverged rows included) has the same effective object.
- Migration pending (review fix, interrogate Act on 4): `sessions_backup` `{state: "skipped", reason: "migration_pending", started_at: <previous record's or null>, finished_at, last_saved: <kept>}`, written only when the stored record differs (no write on later ticks while it stays so).
- Decouple migration guard: `reconciler/cache_migration.py` treats `status.cache.sessions_backup.state == "running"` like a running `save` or `sessions_save` (returns without copying or repointing).

#### Expected outcome

After deploy, each converged live session with an agent busy now or gone idle since its last backup (database clock) gets a `sessions_backup` Job within one reconcile tick when it has no backup yet, then at most once per interval and only while an agent is busy or after one went idle since the last backup; its transcripts object in S3 is overwritten with the current `/sessions` tree while its pods keep running. Idle sessions, sessions sharing a transcripts name and sessions whose decouple migration is pending get no backup Job (the last two record `skipped` with reason `shared_name` or `migration_pending`).

#### Steps

- Read `reconciler/cache.py` (all of `CacheRunner`, `CacheOp`, `render_cache_job`), `reconciler/loop.py` (`_converge`, `_discard`, `_db_now`, the `pre_discard` `next_at` pattern), `reconciler/cache_migration.py` (the running-save guard and the pending predicate), `cache/save_rule.py`, `cache/presign.py`, `settings.py`, `db/sessions.py`, `db/status.py` (`free_since`, one clock), `db/migrations/0001_init.sql` (`agent_status`, `agents`), `tests/test_cache_save.py` (`SaveEnv`), `tests/test_sessions_backup.py` and `tests/test_cache_migration.py` (helpers) and README `## Workspace cache` in one pass.
- Red: write tests/test_sessions_live_backup.py with the tests named in AC1-AC11 and AC15-AC19 (fake kube and the existing env helpers; the database clock moved by the same means `test_cache_save.py` uses for timeouts); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_sessions_live_backup.py`; expect failures on the missing step and setting (DB tests: on CI, `DockerException` locally; AC11 runs locally).
- Green: add the setting, the live marker on the `save` operation, the step, the `_reload` before it, the `last_saved` carry-forward, the shared-name and pending checks, the `_converge` call and the migration guard; rerun the verify; expect every test passed on CI and the existing save, migration and settings suites unchanged.
- Document `ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS` in the README settings table and `status.cache.sessions_backup` (with `last_saved`) in README `## Workspace cache`; add the MEMORY.md entry (dated, with the why: own record and Job name because `sessions_save` is final and its Job adopted; `last_saved` so G4 survives a failed run); `mise run lint`; expect exit 0.

#### Notes

- `CacheAction` is `Literal["restore", "save"]` and stays so: the live run is a `save` (review fix, interrogate Act on 5). Key `job_name`, the cache label, `status_key` and the pod listing in `_outcome` on the live marker, so the backup never lists, adopts or deletes the save Job or its pods (AC2, AC19).
- `_begin` today writes a fresh run dict; for the backup it must carry `last_saved` forward from the previous record, and set it only when a run ends `saved` (`_finish_from_log`).
- The previous run's Job must be gone before a new run starts (AC5): `_finish` keeps `job` in the record and `_outcome` deletes the Job after, so a crash in between leaves a finished record whose Job still exists; deterministic Job names mean `_start` would adopt that stale Job otherwise.
- Interval and change signal use the database clock (`SELECT now()`, `agent_status.free_since`), never the reconciler's wall clock nor the wrapper's `turns.completed_at`.
- (my call) `free_since` moves on every transition into idle, booting to idle included, so a pod roll can make one extra backup due after the interval; accepted (bounded by the interval; design Assumptions).
- (my call, builder Q2) superseded by the review fix of interrogate Act on 2: the signal is an agent busy now or `free_since` after the last backup, not a completed turn.
- (my call, builder Q10) with the interval 0 an existing `sessions_backup` record is left as it is; orch-discard-stops-backup still stops a leftover `running` record.
- No chart change: the chart passes any `ORCH_*` through `.Values.env` (`chart/.../templates/configmap.yaml:4-6`), and the setting has a default and no paired setting, so the per-container Settings pair check proposed by the matrix retro does not apply.
- Job cost: one Job pod with a `cache_max_bytes` emptyDir per changed session per interval (design Assumptions).
- Base: this epic builds after decouple-s3-session-cache-fr, hive decoupling and slash commands from chat have landed on main; rebase onto main first and use the decouple names as they landed (`presign.sessions_object_name`, `status.cache.sessions_object`, the `cache_migration` pending predicate, `CacheRunner._begin` pinning). No SQL migration is planned; if one proves necessary it takes the next free number on main at build time (`<MIGRATION>`), and the builder raises it as a question first.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST); it is not a regression.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Per-task security check (retro, recurring): S3 is reached only through one presigned URL per Job, signed by the reconciler; no credential or presigned query string in a log line, a status `reason` or an error message; the api imports neither `reconciler` nor `k8s`.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: interrogate 2026-10-29 act on 1, 2, 3, 4, 5; builder Q2 superseded, Q9 overridden, Q10 yes

### S3: orch discard stops backup

- Status: todo
- Files: `src/agents_orchestrator/reconciler/loop.py`, `src/agents_orchestrator/reconciler/live_backup.py`, `src/agents_orchestrator/reconciler/cache.py`, `src/agents_orchestrator/cache/presign.py`, `tests/test_sessions_backup.py`, `README.md`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_sessions_backup.py tests/test_sessions_live_backup.py && mise run lint`
- Verified head: none

#### Requirement

User request (mx-34 #234, 2026-10-28, relaying the user's priorities), verbatim: "The live-session backup trigger: yes, take it after the paste-.env bug, as a small start-development epic. The user lost sessions in the incident, so a live backup is worth having." Origin (mx-34 #232), verbatim: "there's no backup trigger for a live session (last_transcripts_backup=null)".

README Goal G2, verbatim: "a live backup never corrupts or blocks the discard: a running backup Job is removed before the discard's final save, the final save is never skipped because a live backup exists, and a failed or partial live backup leaves the previous object intact."

Design D3, verbatim: "In `_discard`, before the sessions save step, a running backup Job is deleted (foreground) and its record marked `failed` with reason `superseded_by_discard`; the final save then runs as today. The quiesce already stops the pods, so the final save carries the latest state. Alternative: wait for the backup (bounded by `cache_timeout_seconds`, delays every discard). Direct PUT means a killed backup leaves the previous object intact (`transfer.py:208`)."

Design D3 amendment (planner, 2026-10-29, my call), verbatim: "`KubeApi.delete` deletes a Job with background propagation (`k8s/kube.py:182-190`), so "foreground" is enforced by the discard itself: the record is written `failed`/`superseded_by_discard` first, then the Job is deleted, and the final sessions save starts only when neither the backup Job nor a pod carrying its cache label exists, so a killed backup's PUT can never land after the final one. A crash between the record and the delete is redone by the next tick (a non-running record whose Job still exists). The wait is bounded by `discard_quiesce_timeout_seconds` from the supersede (the record's `finished_at`), after which the final save runs and a warning is logged (anti-goal: no unbounded delay)."

Brief fix-as-ac, verbatim: "Discard must wait for or delete a running live Job before its final save."

Review fix (interrogate 2026-10-29, Act on 1, stale `status.cache` writes): `CacheRunner._write` merges from `session.status["cache"]` and replaces the whole key (reconciler/cache.py:541-544), so a final sessions save run on the session read before the stop step would revert the stop step's `superseded_by_discard` record. `_discard` reloads the session (`_reload`) between the stop step and the final sessions save, and the final save's writes leave `sessions_backup` `failed`/`superseded_by_discard`.

Review decision (interrogate 2026-10-29, Consider 1, late PUT after the bounded discard wait; lead's call, no user question): the bounded wait stays. A backup pod stuck terminating past `discard_quiesce_timeout_seconds` keeps its presigned PUT valid and could land after the final save, so the live run's presign gets the shortest expiry that still covers its own `activeDeadlineSeconds` (`cache_timeout_seconds`): `cache_timeout_seconds + 60` seconds (my call: the 60 s cover the gap between the presign in `_start` and the Job's start, from which the deadline counts), instead of `cache_timeout_seconds + 600`. The discard sessions save, the workdir save and every restore keep `cache_timeout_seconds + 600`. The residual risk is recorded in design Assumptions.

Builder question Q10 (my call: yes): with `ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS` 0 the stop step still handles a leftover `running` `sessions_backup` record before the final save.

#### Acceptance conditions

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

#### Files

- `src/agents_orchestrator/reconciler/loop.py`
- `src/agents_orchestrator/reconciler/live_backup.py`
- `src/agents_orchestrator/reconciler/cache.py`
- `src/agents_orchestrator/cache/presign.py`
- `tests/test_sessions_backup.py`
- `README.md`

#### Interfaces

- `reconciler/loop.py:_discard`: after the workdir save and `_reload`, before `self.cache.save_step(session, "sessions")`, a call (for example `CacheRunner.stop_live_backup(session) -> bool`, True when the final save may start) that: marks a `running` `sessions_backup` record `failed` with reason `superseded_by_discard` and `finished_at` (database clock), keeping `job` and `last_saved`; deletes the owned Job `agent-<slug>-sessions-backup`; returns False (the discard writes `phase: deleting`, message `stopping the live transcripts backup`) while that Job or an owned pod labelled `agents.szymonrichert.pl/cache: sessions-backup` of the session exists, until `discard_quiesce_timeout_seconds` after the record's `finished_at`, then logs a warning naming the session and returns True.
- A non-running record whose Job still exists (crash between the record write and the delete) takes the same delete-and-wait path.
- `reconciler/loop.py:_discard` reloads the session (`_reload`) after the stop step returns True and before `self.cache.save_step(session, "sessions")` (review fix, interrogate Act on 1).
- `CacheRunner.save_step(session, "sessions")` is unchanged: it never reads `sessions_backup`.
- `cache/presign.py:presign` gains a keyword-only expiry override (the builder names it); the live backup run passes `cache_timeout_seconds + 60` (a named constant beside `EXPIRY_MARGIN_SECONDS`); every other caller keeps `cache_timeout_seconds + EXPIRY_MARGIN_SECONDS` (600) (review decision, interrogate Consider 1).

#### Expected outcome

Discarding a session while its live backup runs: the backup Job is killed, the discard waits a few seconds for its pod to go, then the final transcripts save runs as before and writes the last state; the S3 object ends with the final save's content. A discard with no live backup running behaves exactly as today.

#### Steps

- Read `reconciler/loop.py` (`_discard`, `_quiesce`, `_reload`, `_db_now`), `cache/presign.py` (`presign`, `EXPIRY_MARGIN_SECONDS`), `tests/test_cache_presign.py`, the live backup step from orch-sessions-live-backup (`reconciler/cache.py` or `reconciler/live_backup.py`), `reconciler/cache.py:_delete_job`, `k8s/kube.py:delete`, `tests/fakes/fake_kube.py` (`delete`, `list_pods`, `get_job`), `tests/test_sessions_backup.py` and `tests/test_sessions_live_backup.py` (helpers), and the README discard paragraph in one pass.
- Red: add the tests named in AC1-AC6 and AC8-AC10 to tests/test_sessions_backup.py; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_sessions_backup.py`; expect them to fail (DB tests: on CI, `DockerException` locally).
- Green: add the stop step and wire it into `_discard`; rerun the verify; expect every test passed on CI and the existing sessions backup tests unchanged.
- Add the README sentence (the discard stops a running live backup, `superseded_by_discard`, then saves); `mise run lint`; expect exit 0.

#### Notes

- Order: write the `failed` record first, then delete. Either crash point is safe because the step acts on any `running` record (mark it, then delete; an absent Job is fine) and on any non-running record whose Job still exists (delete and wait); `_converge`, which would observe a running record, never runs for a deleting session.
- (my call, interrogate Consider 1) residual risk: a backup pod still terminating after the bounded wait can PUT only while its URL is valid, that is within `cache_timeout_seconds + 60` of its presign; recorded in design Assumptions, no user question.
- (my call, builder Q10) with the interval 0 a leftover `running` `sessions_backup` record still takes the stop path (AC10).
- AC5 is the headline promise end to end (retro, recurring): live backup, discard, final save and recreate in one test, asserting the order of the PUT Jobs and the restore's GET object, not separate pieces.
- The quiesce already scales the StatefulSet to zero; backup Job pods are not agent pods (`rollout.agent_pods` matches only `agent-<slug>-<ordinal>`), so the quiesce never waits for them; this task's wait is the only one.
- Base: this epic builds after decouple-s3-session-cache-fr, hive decoupling and slash commands from chat have landed on main; rebase onto main first and use the decouple names as they landed (`presign.sessions_object_name`, `status.cache.sessions_object`, the `cache_migration` pending predicate, `CacheRunner._begin` pinning). No SQL migration is planned; if one proves necessary it takes the next free number on main at build time (`<MIGRATION>`), and the builder raises it as a question first.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST); it is not a regression.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Per-task security check (retro, recurring): S3 is reached only through one presigned URL per Job, signed by the reconciler; no credential or presigned query string in a log line, a status `reason` or an error message; the api imports neither `reconciler` nor `k8s`.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: interrogate 2026-10-29 act on 1; consider 1 (live presign expiry); builder Q10 yes

### S4: orch backup view latest

- Status: todo
- Files: `src/agents_orchestrator/api/sessions.py`, `src/agents_orchestrator/api/schemas.py`, `openapi.json`, `README.md`, `MEMORY.md`, `tests/test_api_session_safety.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_api_session_safety.py tests/test_readme_api.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint`
- Verified head: none

#### Requirement

User request (mx-34 #234, 2026-10-28, relaying the user's priorities), verbatim: "The live-session backup trigger: yes, take it after the paste-.env bug, as a small start-development epic. The user lost sessions in the incident, so a live backup is worth having." Origin (mx-34 #232), verbatim: "there's no backup trigger for a live session (last_transcripts_backup=null)".

README Goal G4, verbatim: "the API's `last_transcripts_backup` and the discard dialog show the latest successful backup, live or final, and the live backup state is visible in `status.cache`."

Design D7 (the API part), verbatim: "`SessionView.backup.last_transcripts_backup` (`api/sessions.py:64-90`) becomes the newer saved record of `sessions_save` and `sessions_backup`, with a field naming which (`final` or `live`). [...] openapi.json and the web's vendored schema follow."

Design D7 planner detail (2026-10-29, my call), verbatim: "the naming field is `BackupRun.kind`, `"final"` (from `sessions_save` in state `saved`) or `"live"` (from `sessions_backup.last_saved`); the newer by `finished_at` wins, a tie goes to `final`."

Brief fix-as-ac, verbatim: "`last_transcripts_backup` must reflect live backups (today reads only `sessions_save`)."

Test no longer accurate and changed: tests/test_api_session_safety.py::test_backup_view_last_transcripts_backup asserts `set(last) == {"finished_at", "bytes"}`; `BackupRun` gains `kind` by design D7, so the expected key set gains `kind` (value `final` for that test's `sessions_save`).

#### Acceptance conditions

- AC1: with sessions_save saved and sessions_backup.last_saved both present, last_transcripts_backup is the one with the later finished_at, kind `live` or `final` accordingly, and a tie gives `final` [evidence: test:tests/test_api_session_safety.py::test_last_transcripts_backup_newest_of_live_and_final]
- AC2: a live session with only a live backup shows it (kind live, its finished_at and bytes), also while its latest run is running, failed or skipped (last_saved kept) [evidence: test:tests/test_api_session_safety.py::test_last_transcripts_backup_live_only]
- AC3: with neither a saved sessions_save nor a last_saved it is null, and a final-only backup carries kind final [evidence: test:tests/test_api_session_safety.py::test_backup_view_last_transcripts_backup]
- AC4: openapi.json is regenerated and matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC5: the api still imports neither reconciler nor k8s [evidence: test:tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper]
- AC6: README documents kind and the live source of last_transcripts_backup, MEMORY.md records it, and lint passes [evidence: command:grep -q "sessions_backup.last_saved" README.md && grep -q "BackupRun.kind" MEMORY.md && mise run lint]

#### Files

- `src/agents_orchestrator/api/sessions.py`
- `src/agents_orchestrator/api/schemas.py`
- `openapi.json`
- `README.md`
- `MEMORY.md`
- `tests/test_api_session_safety.py`

#### Interfaces

- `api/schemas.py:BackupRun`: `finished_at: datetime`, `bytes: int`, `kind: Literal["final", "live"]` (required).
- `api/sessions.py:_backup`: `last_transcripts_backup` is the newer by `finished_at` of `status.cache.sessions_save` in state `saved` (`kind="final"`) and `status.cache.sessions_backup.last_saved` (`kind="live"`); a tie gives `final`; neither gives null. Malformed or non-dict values read as absent, as `_last_backup` does today.
- `openapi.json` regenerated with `uv run python -m agents_orchestrator.api.openapi > openapi.json`.
- The api reads `status` only; it never imports `reconciler` or `k8s`.

#### Expected outcome

`GET /api/v1/sessions/<id>` for a live session that had a live backup shows `backup.last_transcripts_backup` `{finished_at, bytes, kind: "live"}` instead of null; after the discard's final save the view (while the row exists) shows the final one.

#### Steps

- Read `api/sessions.py` (`_last_backup`, `_backup`), `api/schemas.py` (`BackupRun`, `SessionBackup`), `tests/test_api_session_safety.py` (`_backup`, `SAVED`, `RESTORED`, `CACHED`), `tests/test_readme_api.py::test_openapi_json_matches_app`, README (the `backup` paragraph of the session view and `## Workspace cache`) and MEMORY.md (the 2026-10-28 API session safety entry) in one pass.
- Red: add the tests named in AC1 and AC2 and change `test_backup_view_last_transcripts_backup` as the Requirement names; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_api_session_safety.py`; expect them to fail (DB tests: on CI, `DockerException` locally).
- Green: change `BackupRun` and `_backup`; regenerate openapi.json; rerun the verify; expect every test passed on CI, and `tests/test_readme_api.py` and the import guard passed locally.
- Update README (the session view `backup` paragraph and the transcripts paragraph: `kind`, the live source `status.cache.sessions_backup.last_saved`) and the MEMORY.md entry (dated, `BackupRun.kind`, why the newer of the two); `mise run lint`; expect exit 0.

#### Notes

- The MEMORY.md line of 2026-10-28 says `last_transcripts_backup` is `sessions_save` only; add a dated entry that supersedes it rather than rewriting history.
- After the orchestrator PR merges, agents-web syncs the schema from the merge commit (task web-discard-latest-backup); pinning an epic-branch commit instead forced a merge commit in matrix-connector-agent-initi (retro).
- Base: this epic builds after decouple-s3-session-cache-fr, hive decoupling and slash commands from chat have landed on main; rebase onto main first and use the decouple names as they landed (`presign.sessions_object_name`, `status.cache.sessions_object`, the `cache_migration` pending predicate, `CacheRunner._begin` pinning). No SQL migration is planned; if one proves necessary it takes the next free number on main at build time (`<MIGRATION>`), and the builder raises it as a question first.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST); it is not a regression.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Per-task security check (retro, recurring): S3 is reached only through one presigned URL per Job, signed by the reconciler; no credential or presigned query string in a log line, a status `reason` or an error message; the api imports neither `reconciler` nor `k8s`.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

### S5: web discard latest backup

- Status: todo
- Files: `src/sessions/DiscardSessionDialog.tsx`, `src/sessions/DiscardSessionDialog.test.tsx`, `src/api/schema.d.ts`, `openapi/orchestrator.json`, `openapi/orchestrator.source`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/sessions/DiscardSessionDialog.test.tsx && npm run check:api && npm run build && npm run lint`
- Verified head: none

#### Requirement

User request (mx-34 #234, 2026-10-28, relaying the user's priorities), verbatim: "The live-session backup trigger: yes, take it after the paste-.env bug, as a small start-development epic. The user lost sessions in the incident, so a live backup is worth having." Origin (mx-34 #232), verbatim: "there's no backup trigger for a live session (last_transcripts_backup=null)".

README Goal G4, verbatim: "the API's `last_transcripts_backup` and the discard dialog show the latest successful backup, live or final, and the live backup state is visible in `status.cache`."

Design D7 (the web part), verbatim: "The discard dialog (`agents-web/src/sessions/DiscardSessionDialog.tsx:105,136-139`) says the transcripts were last backed up at that time and that the discard writes a final backup. openapi.json and the web's vendored schema follow."

Design D7 planner detail (2026-10-29, my call), verbatim: "the naming field is `BackupRun.kind`, `"final"` (from `sessions_save` in state `saved`) or `"live"` (from `sessions_backup.last_saved`); the newer by `finished_at` wins, a tie goes to `final`."

Wording (planner, my call): when `backup.transcripts` is true and `last_transcripts_backup` is set, the dialog shows `Claude transcripts last backed up at <finished_at> (<live backup|final backup>, <formatBytes(bytes)>); the discard writes a final backup.` This replaces `The last transcripts backup finished at <finished_at> (<bytes>); a new one replaces it.`

Tests no longer accurate and changed: src/sessions/DiscardSessionDialog.test.tsx `states what is backed up when the session cache is configured` (its `last_transcripts_backup` fixture lacks the now required `kind`, and it matches the removed `last transcripts backup finished` wording); the `NO_BACKUP` fixture type follows the regenerated schema.

#### Acceptance conditions

- AC1: with last_transcripts_backup kind live the dialog says the Claude transcripts were last backed up at its finished_at by a live backup, with its size, and that the discard writes a final backup [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "names the latest live backup"]
- AC2: with kind final the dialog names a final backup with the same sentence [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "names the latest final backup"]
- AC3: the old wording is gone from src [evidence: command:! grep -rn "a new one replaces it" src]
- AC4: openapi/orchestrator.json, openapi/orchestrator.source and src/api/schema.d.ts are synced from the orchestrator commit carrying BackupRun.kind and agree [evidence: command:grep -q '"kind"' openapi/orchestrator.json && npm run check:api]
- AC5: the whole dialog suite, the type check of the build and lint pass [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx && npm run build && npm run lint]

#### Files

- `src/sessions/DiscardSessionDialog.tsx`
- `src/sessions/DiscardSessionDialog.test.tsx`
- `src/api/schema.d.ts`
- `openapi/orchestrator.json`
- `openapi/orchestrator.source`

#### Interfaces

- `src/api/schema.d.ts`: `BackupRun` gains `kind: "final" | "live"`, generated by `npm run sync:api -- orchestrator` from the orchestrator commit carrying it (`openapi/orchestrator.source` names that commit).
- `src/sessions/DiscardSessionDialog.tsx`: with `backup.transcripts` and `last_transcripts_backup` set, one Typography reading `Claude transcripts last backed up at ${finished_at} (${kind === 'live' ? 'live backup' : 'final backup'}, ${formatBytes(bytes)}); the discard writes a final backup.`

#### Expected outcome

Opening the discard dialog of a live session that had a live backup shows when the transcripts were last backed up, that it was a live backup and its size, and that the discard writes a final backup.

#### Steps

- Read src/sessions/DiscardSessionDialog.tsx, src/sessions/DiscardSessionDialog.test.tsx (`existing`, `wrap`, `NO_BACKUP`), scripts/sync-api.mjs and openapi/orchestrator.source in one pass.
- `npm ci --no-audit --no-fund`; `npm run sync:api -- orchestrator` against the orchestrator merge commit of orch-backup-view-latest; `npm run check:api`; expect exit 0.
- Red: change `states what is backed up when the session cache is configured` as the Requirement names and add the two tests named in AC1 and AC2; run `npx vitest run src/sessions/DiscardSessionDialog.test.tsx`; expect them to fail.
- Green: change DiscardSessionDialog.tsx; rerun; expect all passed; `npm run build` and `npm run lint`; expect exit 0.

#### Notes

- (my call, builder Q6) the four orchestrator tasks ship as one agents-orchestrator epic PR, merged to main before this task starts; this task syncs the schema from that merge commit.
- (my call, builder Q7) AC5's commands are the real check; the verify runs `npm run build` too.
- The dialog's workspace and transcripts lines were reworded by decouple-s3-session-cache-fr (web-discard-effective-name, effective cache name); keep that wording, change only the last-backup sentence.
- Sync from the orchestrator merge commit on main, not an epic-branch commit: an epic-branch pin forced a merge commit in matrix-connector-agent-initi (retro).
- Tree state: `npm test` had test files failing to import `@codemirror/*` with a stale node_modules, so the verify runs `npm ci --no-audit --no-fund` first.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring vitest load flake).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims (no fallback for a missing `kind`; the orchestrator deploys first).

### S6: helmfile backup pins

- Status: todo
- Files: `helmfile.yaml.gotmpl`, `values/agents-orchestrator/common.yaml`, `values/agents-web/common.yaml`, `tests/test_orchestrator_release.py`, `tests/test_web_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint`
- Verified head: none

#### Requirement

User request (mx-34 #234, 2026-10-28, relaying the user's priorities), verbatim: "The live-session backup trigger: yes, take it after the paste-.env bug, as a small start-development epic. The user lost sessions in the incident, so a live backup is worth having." Origin (mx-34 #232), verbatim: "there's no backup trigger for a live session (last_transcripts_backup=null)".

README Goal G5, verbatim: "released and deployed (orchestrator image, web image, helmfile pins), and proven live: a running session's transcripts object appears in S3 with a recent `last_transcripts_backup`."

Design D8 (the deploy part), verbatim: "agents-helmfile pins the new orchestrator and web images; no value change needed for the default."

User decision (repos), verbatim: "agents-helmfile (pins plus a live check after the apply under the deploy lease [...])".

Scope (agents-helmfile): pin agents-orchestrator to the merge commit `<ORCH_SHA>` of its epic PR (chart `0.1.0-main.<ORCH_SHA>` in helmfile.yaml.gotmpl, `image.tag` `<ORCH_SHA>` in values/agents-orchestrator/common.yaml) and agents-web to the merge commit `<WEB_SHA>` of its epic PR (chart `0.1.0-main.<WEB_SHA>`, `image.tag` `<WEB_SHA>` in values/agents-web/common.yaml). Wait until each main CI run for those shas is green including chart and image publish. Keep every other pin and value unchanged (no ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS value: the default applies). Update tests/test_orchestrator_release.py and tests/test_web_release.py to the new pins. `mise run check-pins` must pass. Never run an apply. `<ORCH_SHA>` and `<WEB_SHA>` are placeholders: the orchestrator replaces them with the real merge shas through `ticket.py amend` before this task starts.

#### Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the orchestrator merge sha `<ORCH_SHA>` [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the agents-web chart version and image tag agree on the agents-web merge sha `<WEB_SHA>` [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC3: the pins name the merge shas [evidence: command:grep -q "0.1.0-main.<ORCH_SHA>" helmfile.yaml.gotmpl && grep -q "0.1.0-main.<WEB_SHA>" helmfile.yaml.gotmpl]
- AC4: every pin's main CI is green [evidence: command:mise run check-pins]
- AC5: the release test files and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_orchestrator_release.py`
- `tests/test_web_release.py`

#### Interfaces

- `helmfile.yaml.gotmpl`: agents-orchestrator chart `0.1.0-main.<ORCH_SHA>`, agents-web chart `0.1.0-main.<WEB_SHA>`.
- `values/agents-orchestrator/common.yaml`: `image.tag` `<ORCH_SHA>`; `values/agents-web/common.yaml`: `image.tag` `<WEB_SHA>`. No other value changes.

#### Expected outcome

agents-helmfile main pins the orchestrator and web releases of this epic (which also carry decouple-s3-session-cache-fr, open question Q7), ready for the apply in helmfile-backup-live-check.

#### Steps

- Read helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, values/agents-web/common.yaml, tests/test_orchestrator_release.py and tests/test_web_release.py in one pass.
- Red: change the pin assertions in the two test files to `<ORCH_SHA>` and `<WEB_SHA>`; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py`; expect the pin tests to fail.
- Green: change the pins; rerun the verify; expect passed and lint exit 0; `mise run check-pins`; expect every pin green.

#### Notes

- (my call, builder Q4) `<ORCH_SHA>` and `<WEB_SHA>` mean the 7-character short merge sha (the pin tests require `[0-9a-f]{7}`), never the full 40.
- (my call, builder Q5) the orchestrator session amends the placeholders with `ticket.py amend` after both epic PRs (agents-orchestrator, agents-web) have merged and their main CI runs are green; the Red step then edits the test literals first.
- `<ORCH_SHA>` and `<WEB_SHA>` are placeholders; the orchestrator replaces them with `ticket.py amend` once both epic PRs merged and their main CI runs (images and chart publish) are green. Never pin an epic-branch commit.
- Chart-pull tests blocked by a container network policy may be deselected locally (precedent); they run unblocked before the apply.
- Never run an apply in this task.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes.

### S7: helmfile backup live check

- Status: todo
- Files: `MEMORY.md`
- Verify: `mise run lint && grep -q 'live transcript backup live check' MEMORY.md`
- Verified head: none

#### Requirement

User request (mx-34 #234, 2026-10-28, relaying the user's priorities), verbatim: "The live-session backup trigger: yes, take it after the paste-.env bug, as a small start-development epic. The user lost sessions in the incident, so a live backup is worth having." Origin (mx-34 #232), verbatim: "there's no backup trigger for a live session (last_transcripts_backup=null)".

README Goal G5, verbatim: "released and deployed (orchestrator image, web image, helmfile pins), and proven live: a running session's transcripts object appears in S3 with a recent `last_transcripts_backup`."

Design D8 (the live check), verbatim: "Live check: after the apply, a running session gets a `sessions_backup` record `saved` and the object's LastModified in S3 is recent (HEAD with the reconciler's credentials is not available to agents; the check reads `status.cache` and the API field) (my call)."

Design D8 planner detail (2026-10-29, open question Q7 planned on its recommended answer), verbatim: "this epic's orchestrator and web pins are the first to deploy its changes too, including its copy migration of every pre-epic session at the first converge [...] The live check therefore also reads each live session's `status.cache.migration`. Apply order: orchestrator first, then web (the web reads the new required `BackupRun.kind`). The apply runs under the deploy Lease `agents/agents-helmfile-apply` (user decision)."

User decision, verbatim: "agents-helmfile (pins plus a live check after the apply under the deploy lease: Lease agents/agents-helmfile-apply created with kubectl create -f, holderIdentity, acquireTime, leaseDurationSeconds 3600; stale after 60 min, message the holder via the superleader before deleting; delete only your own; kubeconfig from the pod SA, context in-cluster-sa)".

Live applies are run by the orchestrator session only, never by a subagent. Steps, after the agents-helmfile PR merged, in `code/agents-helmfile` on `main`, least destructive first:
1. Claim the deploy Lease: `kubectl --context in-cluster-sa -n agents create -f <lease.yaml>` for Lease `agents-helmfile-apply` with `holderIdentity` (the session's own ccw address), `acquireTime` (now) and `leaseDurationSeconds: 3600`. If it already exists: an `acquireTime` under 60 minutes old means wait; a stale one (60 minutes or more) means message its holder via the superleader first and delete it only after that; never delete a Lease that is not your own otherwise.
2. Check that the pinned orchestrator and web image tags and chart versions exist in Harbor.
3. `mise run diff` read in full: only the agents-orchestrator and agents-web chart versions and image tags change; anything else stops the task (Lease released).
4. Write a handoff checkpoint naming the remaining steps before the apply (the apply may roll agent pods, the deployer's included).
5. `mise run apply -- --selector name=agents-orchestrator`, then `mise run apply -- --selector name=agents-web` (orchestrator first).
6. `mise run diff` shows no pending change; `mise run smoke` green.
7. Live check, read-only: each live session's `status.cache.migration` (decouple copy migration: `done`, or `failed` with its reason); a running session with a completed turn gets `status.cache.sessions_backup` `saved` with `last_saved`, and its API `backup.last_transcripts_backup` has `kind` `live` and a `finished_at` after the apply; that session's agent pods kept their uids through the backup (no pause, scale or restart); no `agent-<slug>-sessions-save` Job was created for a live session.
8. Delete your own Lease.
9. MEMORY.md entry containing the words `live transcript backup live check`, dated, with the applied orchestrator and web charts and images, the step 7 session slug, record and API values, and the migration outcomes.

#### Acceptance conditions

- AC1: (orchestrator session) the deploy Lease agents/agents-helmfile-apply was created with this session as holderIdentity before the apply and deleted by it after the live check, and no other holder's Lease was deleted without messaging the holder via the superleader [evidence: judgement:orchestrator quotes the Lease holderIdentity, acquireTime and the delete in the task Notes]
- AC2: (orchestrator session) the pinned orchestrator and web image tags and chart versions exist in Harbor before the apply, and the pre-apply diff showed only those pins [evidence: judgement:orchestrator records the registry check and the diff summary in the task Notes]
- AC3: after the applies helmfile reports no pending change [evidence: command:mise run diff]
- AC4: the smoke passes against the applied release [evidence: command:mise run smoke]
- AC5: (orchestrator session) a running session has status.cache.sessions_backup saved with last_saved, its API backup.last_transcripts_backup has kind live and a finished_at after the apply, and its agent pods kept their uids [evidence: judgement:orchestrator quotes the session slug, the status.cache.sessions_backup record, the API field and the pod uids before and after in the task Notes]
- AC6: (orchestrator session) each live session's status.cache.migration outcome is recorded [evidence: judgement:orchestrator quotes each live session's migration record in the task Notes]
- AC7: MEMORY.md records the live check and the applied versions [evidence: command:grep -q "live transcript backup live check" MEMORY.md]

#### Files

- `MEMORY.md`

#### Interfaces

- None new; uses `kubectl --context in-cluster-sa` (kubeconfig from the pod service account), `mise run diff`, `mise run apply`, `mise run smoke`, and the public orchestrator API (port-forward as the smoke does) for `status.cache` and `backup`.
- Lease manifest: `apiVersion: coordination.k8s.io/v1`, `kind: Lease`, `metadata: {name: agents-helmfile-apply, namespace: agents}`, `spec: {holderIdentity: <own ccw address>, acquireTime: <now, RFC 3339 micro>, leaseDurationSeconds: 3600}`, written under the workbench `.scratchpad`.

#### Expected outcome

The orchestrator and web releases of this epic run live; a running session's Claude transcripts have a fresh live backup in S3, visible as `kind: live` in the API; the decouple migration outcome of each live session is on record; the deploy Lease is released.

#### Steps

- Orchestrator session only: steps 1-9 of the Requirement, in order; stop at step 3 if the diff shows more than the pins (release the Lease first).
- Write the handoff checkpoint (step 4) before the apply; after a roll, resume from it.
- Record each result in the task Notes as it happens (Lease holder and times, Harbor check, diff summary, smoke tail, the step 7 records and pod uids), then the MEMORY.md entry; commit it through the agents-helmfile PR flow; `mise run lint`; expect exit 0.

#### Notes

- Never put `mise run apply` in AC evidence (agents-helmfile MEMORY 2026-10-25). Subagent `kubectl exec` is denied by the permission classifier; the whole task is orchestrator-run.
- (my call, builder Q8) the whole task is orchestrator-session work (live apply, Lease, kubectl); a builder subagent stops after helmfile-backup-pins.
- The first live backup runs within a reconcile tick for a session with an agent busy or gone idle (`agent_status.free_since` set, a completed turn implies it) and no backup record, so step 7 needs no 30-minute wait; if no running session has a completed turn, send one short read-only message to a session first and record it.
- Q7 is open; the plan follows its recommended answer (the decouple changes deploy here). A "no" adds a decouple-only deploy before this one.
- Recurring retro: live apply and proof tasks run several times their seed; budget for more than one attempt. A defect found live becomes a new task, never a hand fix.
- `gh` must be authenticated in the deploying pod for check-pins.

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
