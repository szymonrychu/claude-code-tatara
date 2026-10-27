---
title: wrapper file write route
status: in-progress
repo: claude-code-wrapper
value: "the editor can save a workspace file back, guarded by the workdir confinement and a stale-write check"
files: [src/claude_code_wrapper/files.py, src/claude_code_wrapper/api/files.py, README.md, tests/test_api_files.py]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_files.py tests/test_readme_api.py && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1858483
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper file write route

## Requirement

Epic README goal, verbatim: "RO/RW editor mode: read-only by default, RW lets the user edit and save the file back to the agent's workspace (new write route in claude-code-wrapper and orchestrator)."

User decision U3, verbatim: "(my call) 'RW editor mode': read-only by default with an RO/RW toggle per tab; RW enables editing and Save (button and Ctrl/Cmd+S); new write route in the wrapper (PUT file content, UTF-8 text only, size cap = the existing file_preview_max_bytes, existing workspace path guards, optimistic concurrency via the mtime/size the editor loaded: a changed file answers 409 and the UI offers reload or overwrite) and an orchestrator forwarding route, then `npm run sync:api -- orchestrator`. Binary and too_large files open read-only with the current note, no editor."

Epic README non-goal, verbatim: "No file create, rename or delete."

This task is the claude-code-wrapper part: design D3 (write route `PUT /v1/sessions/{id}/files/content`) and D4 (optimistic concurrency on mtime and size), as written in design.md.

Scope (claude-code-wrapper):
- `src/claude_code_wrapper/files.py`: a blocking write helper following D3 steps 1 to 6 (resolve with `_resolve`; UTF-8 encode and cap at `limits.file_preview_max_bytes` as `too_large`; parent opened `O_RDONLY | O_DIRECTORY | O_NOFOLLOW`, target opened `O_RDONLY | O_NOFOLLOW | O_NONBLOCK` with `dir_fd` and `S_ISREG` checked on its `fstat`; `expected` compared with `_iso(st_mtime)` and `st_size` of that descriptor as `file_changed`; atomic replace through a temporary file in the same directory with the original permission bits, `fsync`, `os.replace` with dir fds; temp removed and every descriptor closed on every exit); the module docstring stops saying read-only.
- `src/claude_code_wrapper/api/files.py`: `PUT /sessions/{session_id}/files/content` with a pydantic body `{content: str, expected: {mtime: str, size: int >= 0} | null}` (both required, `extra="forbid"`), run in a worker thread, answering `{session_id, path, size, mtime}`; `_raise` maps `not_found` 404, `file_changed` 409, `too_large` 413, else 400; the module docstring names the write route.
- `README.md`: a `### \`PUT /v1/sessions/{id}/files/content\`` section in the API reference (body, response, the D4 limits: check and replace are not one atomic step, millisecond mtime; no create; symlink writes its target; content not redacted; errors 400 invalid_path, 400 not_a_file, 401 unauthorized, 404 not_found, 409 file_changed, 413 too_large, 422 invalid_request); the Errors table gains `file_changed` and the `too_large` and `not_a_file` rows name the write route; the Trust model sentence that says the file API is read-only is rewritten to name the write route and its guards.
- `tests/test_api_files.py`: the new tests below.

## Acceptance conditions

- ac1: a PUT replaces the file content byte-exact for UTF-8 text with non-ASCII letters, CRLF line endings, no trailing newline and the empty string, and the answer `{session_id, path, size, mtime}` equals the `size` and `mtime` a following `GET .../files/content` reports (new) [evidence: test:tests/test_api_files.py::test_write_replaces_content]
- ac2: with `expected` equal to the loaded `mtime` and `size` the write succeeds; with a different `mtime` or a different `size` it answers 409 `file_changed` and the file is unchanged; with `expected: null` it overwrites unconditionally (new) [evidence: test:tests/test_api_files.py::test_write_optimistic_concurrency]
- ac3: content whose UTF-8 encoding is longer than `limits.file_preview_max_bytes` answers 413 `too_large` and leaves the file unchanged; content exactly at the cap is written (with `make_client(..., file_preview_max_bytes=8)`) (new) [evidence: test:tests/test_api_files.py::test_write_size_cap]
- ac4: `..`, an absolute path, a NUL byte and a symlink escaping the workdir answer 400 `invalid_path` and leave the outside file unchanged; a directory, the workdir itself (empty path) and a FIFO answer 400 `not_a_file`; a missing path answers 404 `not_found` and creates nothing; an unknown session and a vanished workdir answer 404 `not_found`; no bearer answers 401; a body without `content`, without `expected`, with an extra key or with a non-string `content` answers 422 `invalid_request` (new) [evidence: test:tests/test_api_files.py::test_write_guards]
- ac5: a path swapped after the confinement check (to a FIFO, a symlink to an outside file, a symlink to a device) is refused with 400 and the outside file is unchanged; every open of the target uses `O_NOFOLLOW`; a symlink inside the workdir to a regular file writes the target and the link stays a symlink (new) [evidence: test:tests/test_api_files.py::test_write_open_nofollow_and_fstat]
- ac6: the write keeps the file's permission bits, leaves no temporary file in the directory after a success and after a write failure (an `os.write` monkeypatched to raise `OSError`), and after the failure the original content is intact (new) [evidence: test:tests/test_api_files.py::test_write_atomic_replace]
- ac7: the process holds no more open descriptors after a successful write and after each refused one than before (new) [evidence: test:tests/test_api_files.py::test_write_closes_descriptors]
- ac8: the new route is documented in the README API reference [evidence: test:tests/test_readme_api.py::test_every_public_route_documented]
- ac9: `file_changed` and every other code the API answers are in the README Errors table [evidence: test:tests/test_readme_api.py::test_error_codes_documented]
- ac10: README carries the route heading, the `file_changed` code and no longer calls the file API read-only [evidence: command:grep -qF '### `PUT /v1/sessions/{id}/files/content`' README.md && grep -q 'file_changed' README.md && ! grep -q 'is read-only and reads only' README.md]
- ac11: the file and README suites and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_files.py tests/test_readme_api.py && mise run lint]

## Files

- `src/claude_code_wrapper/files.py`
- `src/claude_code_wrapper/api/files.py`
- `README.md`
- `tests/test_api_files.py`

## Interfaces

- New wrapper route `PUT /v1/sessions/{id}/files/content?path=<rel>` (`api/files.py`): body `{"content": str, "expected": {"mtime": str, "size": int >= 0} | null}` (both keys required, `extra="forbid"`); 200 `{"session_id", "path", "size", "mtime"}`; errors 400 `invalid_path`, 400 `not_a_file`, 401 `unauthorized`, 404 `not_found`, 409 `file_changed` (new code), 413 `too_large`, 422 `invalid_request`, as JSON envelopes.
- New helper in `files.py` (name the builder's, for example `write_file(workdir, rel, content, expected, max_bytes) -> dict`), blocking, raising `FileError` with the codes above.
- `api/files.py:_raise`: status by code (`not_found` 404, `file_changed` 409, `too_large` 413, else 400).
- Kept unchanged: `resolve_in_workdir`, `_resolve`, `_open_nofollow`, `list_directory`, `read_preview`, the `GET` listing, content and download contracts.
- Consumed by fake-wrapper-file-write (the fake mirrors it) and orch-file-write-route.

## Expected outcome

`curl -X PUT -H "$H" -H 'Content-Type: application/json' -d '{"content":"x\n","expected":null}' "localhost:8080/v1/sessions/$SID/files/content?path=<rel>"` replaces an existing workspace file atomically and answers its new size and mtime; a stale `expected` answers 409 `file_changed`; nothing outside the workdir, no non-regular file and no missing path can be written.

## Steps

- Red: add the seven write tests of the acceptance conditions to `tests/test_api_files.py`; run `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_files.py`: the write tests fail with 405 `method_not_allowed` (no PUT route).
- Green: the `files.py` helper, the route and `_raise` in `api/files.py`; rerun: the file tests pass.
- Docs: README route section, Errors table, Trust model sentence, module docstrings; run the task's verify: passes, quote the pytest summary line.

## Notes

- Rulings and their pin tests: a symlink inside the workdir writes its target and stays a link, pinned by `test_write_open_nofollow_and_fstat`; atomic replace keeps permission bits and leaves no temp file, pinned by `test_write_atomic_replace`; a missing path is 404 and never created, pinned by `test_write_guards`; the stamp compare uses `_iso(st_mtime)` (milliseconds) and `st_size` of the opened descriptor, pinned by `test_write_optimistic_concurrency`; the cap counts UTF-8 bytes, not characters, pinned by `test_write_size_cap`.
- Order of checks (design D3): resolve, encode and cap, open parent and target and `fstat`, compare `expected`, replace. The cap is checked before the file is opened, so an over-cap body never touches the disk.
- Mimic `test_content_open_nofollow_and_fstat` (swap the path after `resolve_in_workdir`) and `test_escapes_refused`; `make_client(work, tmp_path, file_preview_max_bytes=8)` sets the cap; count descriptors with `os.listdir("/proc/self/fd")`.
- The download epic changed this file and `tests/test_api_files.py`; build on its state, do not undo its download route or `target_type`.
- Never log the content. Never block the event loop (`asyncio.to_thread`, like the other file routes).
- The component has no MEMORY.md; record the non-obvious calls (atomic replace, D4 limits) in the README section.
- Known environment failures outside this task's verify: `tests/test_container.py` (no docker) and the 3 process-group tests (container PID 1).
