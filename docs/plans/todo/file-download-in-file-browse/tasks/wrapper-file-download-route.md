---
title: wrapper file download route
status: todo
repo: claude-code-wrapper
value: "any workspace file, text or binary of any size, can be fetched as raw bytes behind the existing path guards"
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

# wrapper file download route

## Requirement

Epic README goals, verbatim: "A small download (arrow down) icon on every file row of the Files tree, aligned to the right edge of the file browser." "Clicking it downloads that file from the agent's workspace to the user's computer, byte-exact, for text and binary files of any size (no 1 MiB preview cap)." "New raw-bytes download route in claude-code-wrapper and an orchestrator route forwarding it, with the existing workspace path guards."

User decision U1, verbatim: "Download every file type (text and binary) of any size through a new raw-bytes streaming route in the wrapper (Content-Type application/octet-stream or sniffed mime, Content-Disposition attachment with an RFC 6266 filename*), forwarded by a streaming orchestrator route under the existing sessions/{id}/files namespace, reusing the existing path traversal and workspace-root guards and auth; no size cap beyond what the guards impose."

User decision U2, verbatim: "Directories, symlinks to directories and type 'other' show no download icon; symlinks to files download the target bytes only if the existing guard allows it."

This task is the claude-code-wrapper part: design D1 (raw-bytes route `GET /v1/sessions/{id}/files/download?path=`), D2 (response headers) and D3 (listing field `target_type`), as written in design.md.

Scope (claude-code-wrapper):
- `src/claude_code_wrapper/files.py`: a helper that resolves with `_resolve`, opens with `_open_nofollow`, checks `S_ISREG` on `fstat` of that descriptor and returns what the route needs to stream (descriptor, size, resolved name, mime) before any byte is sent; `list_directory` adds `target_type` to every entry (D3).
- `src/claude_code_wrapper/api/files.py`: `GET /sessions/{session_id}/files/download` streaming the bytes (D1) with the D2 headers; errors raised before the response starts, through the existing `_raise`.
- `README.md`: a `### GET /v1/sessions/{id}/files/download` section in the API reference (query, headers, no size cap, not redacted, errors), the Trust model file-API sentence naming the download route, and `target_type` in the `GET /v1/sessions/{id}/files` section.
- `tests/test_api_files.py`: the new tests below.

## Acceptance conditions

- ac1: text, binary (NUL bytes, invalid UTF-8) and a file over 1 MiB (3 MiB + 1 byte) download byte-exact with Content-Length equal to the file size; an empty file answers 200 with no body [evidence: test:tests/test_api_files.py::test_download_bytes_exact]
- ac2: a 10-byte file downloads fully with `limits.file_preview_max_bytes` set to 4 (no preview cap) [evidence: test:tests/test_api_files.py::test_download_ignores_preview_cap]
- ac3: Content-Type is the guessed mime (`text/x-python` for `.py`) or `application/octet-stream` when unknown; `X-Content-Type-Options: nosniff` and `Cache-Control: no-store` are set [evidence: test:tests/test_api_files.py::test_download_content_type_and_safety_headers]
- ac4: Content-Disposition is `attachment; filename="<fallback>"; filename*=UTF-8''<encoded>` per D2: for a name holding a non-ASCII letter (e-acute), a space, a double quote and a backslash the fallback replaces the non-ASCII letter, the quote and the backslash with `_` (the space stays) and `filename*` percent-encodes the UTF-8 bytes; a symlink downloads under the link name, not the target name; a nested path uses its last segment [evidence: test:tests/test_api_files.py::test_download_content_disposition]
- ac5: every path `files/content` refuses is refused by the download with the same status and code (`..`, absolute, NUL, escaping symlink, unfollowable final symlink: 400 invalid_path; directory, FIFO, the workdir root: 400 not_a_file; missing, unknown session, vanished workdir: 404 not_found; no bearer: 401), and no refused answer carries the outside file's bytes [evidence: test:tests/test_api_files.py::test_download_guards]
- ac6: a path swapped after the confinement check (to a FIFO, an escaping symlink, a device) is refused, every open uses `O_RDONLY | O_NOFOLLOW | O_NONBLOCK`, and a symlink inside the workdir to a regular file downloads the target bytes [evidence: test:tests/test_api_files.py::test_download_open_nofollow_and_fstat]
- ac7: the process holds no more open descriptors after a complete download and after a refused one than before [evidence: test:tests/test_api_files.py::test_download_closes_descriptor]
- ac8: listing entries carry `target_type`: `file`, `dir`, `other` for symlinks resolving inside the workdir to a file, a directory, a FIFO; `null` for a dangling link, a link loop, a link escaping the workdir to a file and one escaping to a directory; `null` for every non-symlink entry [evidence: test:tests/test_api_files.py::test_list_symlink_target_type]
- ac9: the new route is documented in the README API reference and no new error code is undocumented [evidence: test:tests/test_readme_api.py::test_every_public_route_documented]
- ac10: README documents `target_type` and the download route's headers [evidence: command:grep -q 'target_type' README.md && grep -qF '### `GET /v1/sessions/{id}/files/download`' README.md && grep -q "filename\*=UTF-8''" README.md]
- ac11: the file and README suites and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_files.py tests/test_readme_api.py && mise run lint]

## Files

- `src/claude_code_wrapper/files.py`
- `src/claude_code_wrapper/api/files.py`
- `README.md`
- `tests/test_api_files.py`

## Interfaces

- New wrapper route `GET /v1/sessions/{id}/files/download?path=<rel>` (`api/files.py`): 200 with the raw bytes; headers `Content-Type` (guessed mime or `application/octet-stream`), `Content-Length` (fstat size), `Content-Disposition: attachment; filename="<fallback>"; filename*=UTF-8''<encoded>`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store`; errors 400 `invalid_path`, 400 `not_a_file`, 401 `unauthorized`, 404 `not_found` as JSON envelopes.
- Listing entry (`files.py:list_directory`): `{name, type, size, mtime, target_type}`, `target_type` one of `"dir"`, `"file"`, `"other"`, `null`.
- Kept: `files.py:resolve_in_workdir`, `_resolve`, `_open_nofollow`, `read_preview` and the `files/content` contract unchanged.
- Consumed by fake-wrapper-download (the fake mirrors both) and orch-file-download-route.

## Expected outcome

`curl -H "$H" -OJ "localhost:8080/v1/sessions/$SID/files/download?path=<rel>"` saves the file byte-exact under its name, for any size and type; every path `files/content` refuses is refused the same way; the listing tells a symlink to a file from a symlink to a directory.

## Steps

- Red: add the nine tests of the acceptance conditions to `tests/test_api_files.py`; run `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_files.py`: the download tests fail with 404 (no route) and `test_list_symlink_target_type` fails on the missing key.
- Green: the `files.py` helper and `target_type`, the route in `api/files.py`; rerun: the file tests pass.
- Docs: README route section, Trust model sentence, listing `target_type`; run the task's verify: passes, quote the pytest summary line.

## Notes

- Rulings and their pin tests: download name = last segment of the normalised requested path (the link name for a symlink), pinned by `test_download_content_disposition`; fallback character set (printable ASCII 0x20-0x7E minus `"` and `\`, each other character `_`), pinned by `test_download_content_disposition`; `target_type` null for dangling, looping and escaping links whatever the outside target is, pinned by `test_list_symlink_target_type`; bytes read stop at the `fstat` size, pinned by `test_download_bytes_exact`.
- Mimic `test_content_open_nofollow_and_fstat` and `test_escapes_refused` for the guard tests; `make_client(work, tmp_path, file_preview_max_bytes=4)` sets limits. Count descriptors with `os.listdir("/proc/self/fd")`.
- Compute `target_type` with `resolve_in_workdir` then `os.stat` of the resolved path; `ValueError` or `OSError` gives null.
- Never block the event loop on a read (worker thread); close the descriptor on every exit, including a client that disconnects mid-stream.
- The component has no MEMORY.md; record the non-obvious calls in the README section.
- Known environment failures outside this task's verify: `tests/test_container.py` (no docker) and the 3 process-group tests (container PID 1).
