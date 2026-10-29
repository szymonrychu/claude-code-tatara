---
title: orch archive live files
status: todo
repo: agents-orchestrator
value: A transcripts backup taken while Claude writes succeeds and never stores a torn JSONL line
files: [src/agents_orchestrator/cache/archive.py, src/agents_orchestrator/cache/transfer.py, src/agents_orchestrator/reconciler/cache.py, tests/test_cache_archive.py, tests/test_cache_cli.py, tests/test_sessions_backup.py, MEMORY.md]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_archive.py tests/test_cache_cli.py tests/test_cache_jobs_render.py tests/test_sessions_backup.py::test_sessions_save_job_render && mise run lint"
depends_on: []
model: opus
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

# orch archive live files

## Requirement

User request (mx-34 #234, 2026-10-28, relaying the user's priorities), verbatim: "The live-session backup trigger: yes, take it after the paste-.env bug, as a small start-development epic. The user lost sessions in the incident, so a live backup is worth having." Origin (mx-34 #232), verbatim: "there's no backup trigger for a live session (last_transcripts_backup=null)".

README Goal G3, verbatim: "a live backup taken while files are appended or atomically replaced succeeds and restores into a session that resumes (no torn final JSONL line, no failure on a replaced file)."

Design D6, verbatim: "`cache/archive.py:_add` opens a regular file first and builds its tar header from the open descriptor (`gettarinfo(fileobj=...)`, fstat), so an atomic replace (`os.replace`, the wrapper's events compaction, settings rewrites) archives the old inode instead of failing the whole save (today `OSError: unexpected end of data`, archive.py:116, `upload_failed: archive`). A `*.jsonl` member is cut at its last newline so an in-progress append never leaves a torn final line (Claude Code's tolerance on `--resume` is unknown). This applies to every save, discard included (my call: identical semantics for quiescent files)."

Design D6 amendment (planner, 2026-10-29, open question Q6, planned on its recommended answer), verbatim: "the descriptor-based header (fstat, opened with `O_NOFOLLOW`, regular files only) applies to every save, and the JSONL cut only to the transcripts archive: only the sessions Job carries `CACHE_TRIM_JSONL=true` (absent means no cut, so the workdir Job env stays as it is), and `transfer.save` passes it to `archive.pack(..., trim_jsonl=...)`. A "no" to Q6 drops the env variable and applies the cut to every save as first written."

Test no longer accurate and changed: tests/test_sessions_backup.py::test_sessions_save_job_render asserts that the sessions Job env equals the workdir Job env except `CACHE_DIR` and `CACHE_EXCLUDE`; `CACHE_TRIM_JSONL` now differs by target by design (D6 amendment), so it joins the compared-out keys and the test asserts `true` for the sessions Job and its absence from the workdir Job.

Review fix (interrogate 2026-10-29, Act on 6, FIFO swap hangs the pack): `os.open(..., O_RDONLY | O_NOFOLLOW)` blocks on a FIFO swapped in after the lstat, before the fstat type check. The open adds `O_NONBLOCK` (`os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK`), so a FIFO or other non-regular entry swapped in is opened without blocking, fails the fstat regular-file check and is skipped; the pack completes.

## Acceptance conditions

- AC1: a regular file atomically replaced (os.replace) after the walk listed it and before its content is read is archived with the content of the inode that was opened, and the pack succeeds [evidence: test:tests/test_cache_archive.py::test_replaced_file_archives_opened_inode]
- AC2: a file that grows while it is packed is archived with exactly the size its open descriptor reported at open, and the pack succeeds [evidence: test:tests/test_cache_archive.py::test_growing_file_archived_at_open_size]
- AC3: with trim_jsonl=True a member whose name ends in `.jsonl` and whose content does not end in a newline is cut after its last newline (a file with no newline gives an empty member), a `.jsonl` file ending in a newline and every other file are archived byte for byte [evidence: test:tests/test_cache_archive.py::test_trim_jsonl_cuts_torn_last_line]
- AC4: with trim_jsonl=False a `.jsonl` file without a trailing newline is archived byte for byte [evidence: test:tests/test_cache_archive.py::test_workspace_jsonl_never_trimmed]
- AC5: a path that is a symlink, a FIFO or otherwise not a regular file at open time (swapped in after the lstat) is never followed or read, the open of a FIFO swapped in never blocks (O_NONBLOCK) and the pack completes, and a file removed before its open is skipped as before (interrogate Act on 6) [evidence: test:tests/test_cache_archive.py::test_open_never_follows_or_blocks_on_swapped_in_entry]
- AC6: the sessions save Job carries CACHE_TRIM_JSONL `true`, the workdir save Job has no CACHE_TRIM_JSONL, every other env entry unchanged [evidence: test:tests/test_sessions_backup.py::test_sessions_save_job_render]
- AC7: `orch cache save` passes CACHE_TRIM_JSONL `true` to archive.pack as trim_jsonl=True, an absent CACHE_TRIM_JSONL as trim_jsonl=False, and any other value fails before any request [evidence: test:tests/test_cache_cli.py::test_save_trim_jsonl_env]
- AC8: every archive and CLI test passes, MEMORY.md records the descriptor-based pack and the transcripts-only cut, and lint passes [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_archive.py tests/test_cache_cli.py && grep -q "CACHE_TRIM_JSONL" MEMORY.md && mise run lint]

## Files

- `src/agents_orchestrator/cache/archive.py`
- `src/agents_orchestrator/cache/transfer.py`
- `src/agents_orchestrator/reconciler/cache.py`
- `tests/test_cache_archive.py`
- `tests/test_cache_cli.py`
- `tests/test_sessions_backup.py`
- `MEMORY.md`

## Interfaces

- `cache/archive.py:pack(workdir, out, *, exclude, max_bytes, trim_jsonl: bool) -> Packed`: `trim_jsonl` is keyword-only and required (no default: both callers pass it).
- `cache/archive.py:_add`: lstat classifies the entry as today (directory, regular file, symlink with the escape check, others skipped); a regular file is then opened with `os.open(path, os.O_RDONLY | os.O_NOFOLLOW)`, `os.fstat` must still say regular (else skipped), and the tar header comes from `tar.gettarinfo(arcname=rel, fileobj=<the open file>)`; `FileNotFoundError` (and `ELOOP` from a symlink swapped in) skip the entry as today.
- JSONL cut: with `trim_jsonl`, a member whose name ends in `.jsonl` gets `size` set to the offset just after the last `\n` within the fstat size (0 when there is none) and exactly those bytes are written.
- `cache/transfer.py:save`: reads `CACHE_TRIM_JSONL`: absent means false; present it parses like `CACHE_VERIFY_TLS` (`true` or `false`, case-insensitive, stripped; anything else is a bad env that fails before any request) and passes it to `archive.pack`.
- `reconciler/cache.py:render_cache_job`: env `CACHE_TRIM_JSONL` `"true"` is added to the sessions save Job only (a restore does not pack); every other Job env is unchanged, so `tests/test_cache_jobs_render.py::test_job_env_has_no_credentials` (the exact workdir env list) stays as it is.

## Expected outcome

A transcripts save that runs while the wrapper compacts `events.jsonl` with `os.replace` or rewrites its settings, or while Claude appends to a JSONL transcript, succeeds; every transcripts JSONL member ends at a newline. A workspace save archives every file byte for byte, as before. Symlinks are never followed.

## Steps

- Read `cache/archive.py`, `cache/transfer.py` (`save`, the `CACHE_VERIFY_TLS` parsing), `reconciler/cache.py:render_cache_job`, `tests/test_cache_archive.py`, `tests/test_cache_cli.py` (`test_save_saved`, `test_bad_verify_tls_fails_before_any_request`) and `tests/test_sessions_backup.py::test_sessions_save_job_render` in one pass.
- Red: add the tests named in AC1-AC5 to tests/test_cache_archive.py (simulate the replace and the growth deterministically, for example by monkeypatching `os.open` or `tarfile.TarFile.gettarinfo` to act between the lstat and the read, never with sleeps), AC7 to tests/test_cache_cli.py, and change `test_sessions_save_job_render` as the Requirement names (AC6); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_archive.py tests/test_cache_cli.py tests/test_sessions_backup.py::test_sessions_save_job_render`; expect the new tests to fail (AC1 with `OSError: unexpected end of data`, the others on the missing parameter or env).
- Green: change `_add`, `pack`, `transfer.save` and `render_cache_job`; rerun the verify; expect every test passed (all of these run locally, no Docker needed) and lint exit 0.
- Add the MEMORY.md entry (dated, with the why: an atomic replace failed the whole save; the cut is transcripts-only so a workspace file is never truncated, Q6); `mise run lint`; expect exit 0.

## Notes

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
