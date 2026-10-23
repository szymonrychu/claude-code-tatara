---
title: wrapper file api
status: todo
repo: claude-code-wrapper
value: any client can browse and read a session workdir safely over the wrapper API
files: [src/claude_code_wrapper/files.py, src/claude_code_wrapper/api/files.py, src/claude_code_wrapper/api/app.py, src/claude_code_wrapper/config.py, README.md, tests/test_api_files.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_api_files.py tests/test_readme_api.py tests/test_readme_config.py tests/test_config.py && mise run lint"
depends_on: []
owns: [wrapper-path-confinement, wrapper-files-api]
uses: []
model: ""
estimate: 42
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

Errors (the existing `ApiError` envelope): `invalid_path` 400 (escape, absolute, NUL), `not_found` 404 for an unknown session (existing `SessionNotFound` path) and for a missing path, `not_a_directory` 400 when listing a file, `not_a_file` 400 when reading a directory, FIFO, socket or device (never opened, checked with `stat` first). The session workdir comes from `manager.get(id)["workdir"]`, so live and persisted sessions both work; a session whose workdir no longer exists answers `not_found`.

Config: `LimitsConfig.files_max_entries` (default 2000, ge=1) and `LimitsConfig.file_preview_max_bytes` (default 1048576, ge=1); the existing `max_file_bytes` keeps its meaning (turn files).

README (`code/claude-code-wrapper/README.md`): one `### \`GET /v1/sessions/{id}/files\`` and one `### \`GET /v1/sessions/{id}/files/content\`` section under `## API reference` (parameters, response fields, errors), rows for the new error codes in `## Errors`, rows for the two config keys with their defaults in `## Configuration reference`, and a `## Trust model` sentence that the file API reads only inside the session workdir after symlink resolution.

## Acceptance conditions

- AC1: listing the root returns dirs first, dotfiles and .git included, with root, types, sizes and mtimes [evidence: test:tests/test_api_files.py::test_list_root_dirs_first_includes_dotfiles]
- AC2: listing pages at files_max_entries with next_offset [evidence: test:tests/test_api_files.py::test_list_pages_with_next_offset]
- AC3: `..`, absolute paths, NUL bytes and a symlink pointing outside the workdir are refused with invalid_path and nothing outside is read [evidence: test:tests/test_api_files.py::test_escapes_refused]
- AC4: content returns text, binary (NUL or invalid UTF-8) and too_large kinds per the 1 MiB cap [evidence: test:tests/test_api_files.py::test_content_kinds]
- AC5: a FIFO is refused with not_a_file without being opened, and directory vs file mismatches answer not_a_directory and not_a_file [evidence: test:tests/test_api_files.py::test_fifo_and_type_mismatch_refused]
- AC6: a request without the bearer token is 401, an unknown session or path is 404 [evidence: test:tests/test_api_files.py::test_auth_and_not_found]
- AC7: README documents both routes, the error codes and the config keys, enforced by the README tests [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_readme_api.py tests/test_readme_config.py tests/test_config.py]
- AC8: the confinement helper exists and is the only path resolver of the file routes [evidence: symbol:src/claude_code_wrapper/files.py::resolve_in_workdir]
- AC9: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_api_files.py tests/test_readme_api.py tests/test_readme_config.py tests/test_config.py && mise run lint]

## Files

- `src/claude_code_wrapper/files.py`
- `src/claude_code_wrapper/api/files.py`
- `src/claude_code_wrapper/api/app.py`
- `src/claude_code_wrapper/config.py`
- `README.md`
- `tests/test_api_files.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
