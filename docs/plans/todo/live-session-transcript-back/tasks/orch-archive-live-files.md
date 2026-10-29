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

Design D6 amendment (planner, 2026-10-29, open question Q6, planned on its recommended answer), verbatim: "the descriptor-based header (fstat, opened with `O_NOFOLLOW`, regular files only) applies to every save, and the JSONL cut only to the transcripts archive: the sessions Job carries `CACHE_TRIM_JSONL=true`, the workdir Job `CACHE_TRIM_JSONL=false`, and `transfer.save` passes it to `archive.pack(..., trim_jsonl=...)`. A "no" to Q6 drops the env variable and applies the cut to every save as first written."

Test no longer accurate and changed: tests/test_sessions_backup.py::test_sessions_save_job_render asserts that the sessions Job env equals the workdir Job env except `CACHE_DIR` and `CACHE_EXCLUDE`; `CACHE_TRIM_JSONL` now differs by target by design (D6 amendment), so it joins the compared-out keys and the test asserts `true` for the sessions Job and `false` for the workdir Job.

## Acceptance conditions

- AC1: a regular file atomically replaced (os.replace) after the walk listed it and before its content is read is archived with the content of the inode that was opened, and the pack succeeds [evidence: test:tests/test_cache_archive.py::test_replaced_file_archives_opened_inode]
- AC2: a file that grows while it is packed is archived with exactly the size its open descriptor reported at open, and the pack succeeds [evidence: test:tests/test_cache_archive.py::test_growing_file_archived_at_open_size]
- AC3: with trim_jsonl=True a member whose name ends in `.jsonl` and whose content does not end in a newline is cut after its last newline (a file with no newline gives an empty member), a `.jsonl` file ending in a newline and every other file are archived byte for byte [evidence: test:tests/test_cache_archive.py::test_trim_jsonl_cuts_torn_last_line]
- AC4: with trim_jsonl=False a `.jsonl` file without a trailing newline is archived byte for byte [evidence: test:tests/test_cache_archive.py::test_workspace_jsonl_never_trimmed]
- AC5: a path that is a symlink or not a regular file at open time (swapped in after the lstat) is never followed or read, and a file removed before its open is skipped as before [evidence: test:tests/test_cache_archive.py::test_open_never_follows_swapped_in_symlink]
- AC6: the sessions save Job carries CACHE_TRIM_JSONL `true` and the workdir save Job `false`, every other env entry unchanged [evidence: test:tests/test_sessions_backup.py::test_sessions_save_job_render]
- AC7: `orch cache save` passes CACHE_TRIM_JSONL to archive.pack as trim_jsonl, and a value other than true or false fails before any request [evidence: test:tests/test_cache_cli.py::test_save_trim_jsonl_env]
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
