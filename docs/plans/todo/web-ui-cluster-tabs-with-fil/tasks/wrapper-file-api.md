---
title: wrapper file api
status: todo
repo: claude-code-wrapper
value: any client can browse and read a session workdir safely over the wrapper API
files: [src/claude_code_wrapper/files.py, src/claude_code_wrapper/api/files.py, src/claude_code_wrapper/api/app.py, src/claude_code_wrapper/config.py, README.md, tests/test_api_files.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_api_files.py tests/test_readme_api.py tests/test_readme_config.py tests/test_config.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [wrapper-path-confinement, wrapper-files-api]
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# wrapper file api

## Requirement

Add a session-scoped, read-only file API to the wrapper (design D1), test-first.

Routes (under the existing `/v1` router, bearer auth as every `/v1` route), in a new `src/claude_code_wrapper/api/files.py` registered in `api/app.py`:

- `GET /v1/sessions/{id}/files?path=<rel>&offset=<n>`: lists one directory of the session workdir. `path` is relative to the workdir, default empty (the workdir itself); `offset` default 0. Response 200 `{"session_id", "root": <absolute realpath of the workdir>, "path": <normalised relative path, "" for root>, "entries": [{"name", "type": "dir"|"file"|"symlink"|"other", "size": int|null, "mtime": ISO-8601 str}], "next_offset": int|null}`. Everything is listed, dotfiles and `.git` included. Order: directories first, then everything else, each by name (byte order). At most `limits.files_max_entries` entries per response; `next_offset` is the offset of the next page or null.
- `GET /v1/sessions/{id}/files/content?path=<rel>`: reads one file. Response 200 `{"session_id", "path", "size", "mtime", "mime": str|null (from `mimetypes.guess_type`), "kind": "text"|"binary"|"too_large", "content": str|null}`. `kind` is `too_large` when size exceeds `limits.file_preview_max_bytes` (content null, the file is not read past the check); `binary` when the first 8 KiB contain a NUL byte or the bytes are not valid UTF-8 (content null); else `text` with the decoded content.

Confinement, in a new `src/claude_code_wrapper/files.py` (one helper, owns part `wrapper-path-confinement`, reused by the terminal task for the shell cwd): `resolve_in_workdir(workdir: str, rel: str) -> Path` rejects absolute `rel`, NUL bytes, and any path whose `realpath` is not inside the `realpath` of the workdir (so `..` and escaping symlinks fail). A symlink entry is listed as `symlink` and is followed by the content route only when its resolved target stays inside the workdir.

Errors (the existing `ApiError` envelope): `invalid_path` 400 (escape, absolute, NUL), `not_found` 404 for an unknown session (existing `SessionNotFound` path) and for a missing path, `not_a_directory` 400 when listing a file, `not_a_file` 400 when reading a directory, FIFO, socket or device. The content route opens only after the realpath confinement check, with `os.open(path, O_RDONLY | O_NOFOLLOW | O_NONBLOCK)`, then `os.fstat` on the descriptor and refuses anything that is not a regular file (closing the descriptor unread); it never stats and then opens by path, so a path swapped to a FIFO, device or symlink between check and open cannot hang or leak, and size and the bounded read come from the same descriptor. The session workdir comes from `manager.get(id)["workdir"]`, so live and persisted sessions both work; a session whose workdir no longer exists answers `not_found`.

Config: `LimitsConfig.files_max_entries` (default 2000, ge=1) and `LimitsConfig.file_preview_max_bytes` (default 1048576, ge=1); the existing `max_file_bytes` keeps its meaning (turn files).

README (`code/claude-code-wrapper/README.md`): one `### \`GET /v1/sessions/{id}/files\`` and one `### \`GET /v1/sessions/{id}/files/content\`` section under `## API reference` (parameters, response fields, errors), rows for the new error codes in `## Errors`, rows for the two config keys with their defaults in `## Configuration reference`, and `## Trust model` sentences that the file API reads only inside the session workdir after symlink resolution, and that file content (and, in the terminal task, terminal frames) is not passed through the secret redactor: redaction would corrupt files and PTY streams, and the shell already runs as the agent uid, so anything the agent can read a client can read.

## Acceptance conditions

- AC1: listing the root returns dirs first, dotfiles and .git included, with root, types, sizes and mtimes [evidence: test:tests/test_api_files.py::test_list_root_dirs_first_includes_dotfiles]
- AC2: listing pages at files_max_entries with next_offset [evidence: test:tests/test_api_files.py::test_list_pages_with_next_offset]
- AC3: `..`, absolute paths, NUL bytes and a symlink pointing outside the workdir are refused with invalid_path and nothing outside is read [evidence: test:tests/test_api_files.py::test_escapes_refused]
- AC4: content returns text, binary (NUL or invalid UTF-8) and too_large kinds per the 1 MiB cap [evidence: test:tests/test_api_files.py::test_content_kinds]
- AC5: a FIFO is refused with not_a_file without blocking or reading (opened O_NONBLOCK, then refused by fstat), and directory vs file mismatches answer not_a_directory and not_a_file [evidence: test:tests/test_api_files.py::test_fifo_and_type_mismatch_refused]
- AC6: a request without the bearer token is 401, an unknown session or path is 404 [evidence: test:tests/test_api_files.py::test_auth_and_not_found]
- AC7: README documents both routes, the error codes and the config keys, enforced by the README tests [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_readme_api.py tests/test_readme_config.py tests/test_config.py]
- AC8: the confinement helper exists and is the only path resolver of the file routes [evidence: symbol:src/claude_code_wrapper/files.py::resolve_in_workdir]
- AC9: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_api_files.py tests/test_readme_api.py tests/test_readme_config.py tests/test_config.py && uv run ruff check . && uv run ruff format --check .]
- AC10: the content route opens with O_RDONLY|O_NOFOLLOW|O_NONBLOCK after confinement and checks fstat on the descriptor; a path swapped to a FIFO, symlink or device between the confinement check and the open is refused and nothing is read [evidence: test:tests/test_api_files.py::test_content_open_nofollow_and_fstat]
- AC11: README Trust model states that file content and terminal frames are not passed through the secret redactor and why [evidence: doc-section:README.md#Trust model]

## Files

- `src/claude_code_wrapper/files.py`
- `src/claude_code_wrapper/api/files.py`
- `src/claude_code_wrapper/api/app.py`
- `src/claude_code_wrapper/config.py`
- `README.md`
- `tests/test_api_files.py`

## Interfaces

- `claude_code_wrapper.files.resolve_in_workdir(workdir: str, rel: str) -> pathlib.Path` (owns part `wrapper-path-confinement`), plus listing and reading helpers in the same module.
- Routes `GET /v1/sessions/{id}/files` and `GET /v1/sessions/{id}/files/content` (owns part `wrapper-files-api`, cross-repo contract `wrapper-files-api`, consumed by agent-orchestrator task file-proxy-routes): field names above are the contract.
- `LimitsConfig.files_max_entries`, `LimitsConfig.file_preview_max_bytes`.

## Expected outcome

`curl -H 'Authorization: Bearer ...' http://pod:8080/v1/sessions/<id>/files` lists the workdir; `.../files/content?path=README.md` returns its text; nothing outside the workdir is ever readable.

## Steps

- Write `tests/test_api_files.py` with a stub manager (pattern of `tests/test_api_auth.py`: `TestClient` plus a stub whose `get(sid)` returns `{"workdir": str(tmp_path / "wd")}`), covering AC1-AC6; run `uv run pytest -q -p no:cacheprovider tests/test_api_files.py`: fails (404 routes).
- Implement `files.py`, `api/files.py`, register the router in `api/app.py`, add the config keys; rerun: passes.
- Update the README sections; run `uv run pytest -q -p no:cacheprovider tests/test_readme_api.py tests/test_readme_config.py tests/test_config.py`: passes.
- `uv run ruff check . && uv run ruff format --check .`: clean.

## Notes

- Confinement precedent: `workdir.py:safe_write_files` (realpath root, `is_relative_to`). Do not move or change it; the new helper is read-side.
- Read with a bounded read (`size` from `os.fstat` on the opened descriptor; never `read()` an unbounded file; never stat then open by path); do the blocking filesystem work in `asyncio.to_thread` so a slow CephFS stat does not stall the loop.
- `mtime` as UTC ISO-8601 with milliseconds, like other wrapper timestamps.
- Wrapper rules: plain ASCII, `uv run` always, never write service files into a session workdir (tests create their own fixture files in `tmp_path`).
- `tests/test_manager.py::test_shutdown_stops_all` fails only in this container (PID 1 does not reap zombies); not a verify target.

- 2026-10-23 amended: interrogate rulings 9 (open with O_NOFOLLOW|O_NONBLOCK and fstat, no stat-then-open) and 12 (README Trust model states no redaction of file content and terminal frames)
