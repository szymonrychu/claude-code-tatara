# file download in file browser implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: wrapper client download

- Status: done
- Files: `src/agents_orchestrator/wrapper/client.py`, `tests/test_wrapper_client.py`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_wrapper_client.py && mise run lint`
- Verified head: e6aaf416717ce80333604f89da894e501740a7e4

#### Requirement

Design D4, verbatim (client part): "A new `WrapperClient.open_download` (`wrapper/client.py`, modelled on `events`) sends the streamed GET with the bearer only in `Authorization` and inspects the status before any byte reaches the browser: wrapper 4xx is re-raised with the wrapper's status and code (token scrubbed), 5xx is 502 `wrapper_error`, transport failure is 502 `wrapper_unreachable`, the same map as `forward` (share one mapping helper rather than copying it). ... No total timeout (any size); connect and each read keep the client's `DEFAULT_TIMEOUT`."

This task builds the client method only; the mapping to ApiError lives in the route task (orch-file-download-route).

Scope (agents-orchestrator):
- `src/agents_orchestrator/wrapper/client.py`: `async def open_download(self, session_id: str, path: str) -> httpx.Response`: sends `GET /v1/sessions/{session_id}/files/download` with query `path`, the bearer only in the `Authorization` header, streamed (`self._http.send(request, stream=True)`), timeout `httpx.Timeout(DEFAULT_TIMEOUT)` (connect and per read, no total). For status >= 300 it reads the body, closes the response and raises `WrapperError(status, code, message)` through `_raise_for_error`; a transport failure raises `WrapperUnreachable`. For a 2xx it returns the open response; the caller relays `aiter_raw()` and must `aclose()` it.
- `tests/test_wrapper_client.py`: the new tests below, with `httpx.MockTransport` as the file already does.

#### Acceptance conditions

- ac1: `open_download` requests `GET /v1/sessions/<sid>/files/download?path=<rel>` with the bearer only in `Authorization` (not in the URL), returns the open 2xx response whose `aiter_raw()` yields the exact bytes (including NUL and non-UTF-8 bytes) and whose headers are the wrapper's (new) [evidence: test:tests/test_wrapper_client.py::test_open_download_streams_raw_bytes]
- ac2: a wrapper 4xx JSON error raises `WrapperError` with the wrapper's status, code and message, a 5xx raises `WrapperError` with its status, a transport failure raises `WrapperUnreachable`, and the response is closed in each case (new) [evidence: test:tests/test_wrapper_client.py::test_open_download_errors]
- ac3: the wrapper client suite and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_wrapper_client.py && mise run lint]

#### Files

- `src/agents_orchestrator/wrapper/client.py`
- `tests/test_wrapper_client.py`

#### Interfaces

- `wrapper/client.py:WrapperClient.open_download(self, session_id: str, path: str) -> httpx.Response`: the open, streamed 2xx response (caller relays `aiter_raw()` and calls `aclose()`); raises `WrapperError(status, code, message)` for status >= 300 (response read and closed first) and `WrapperUnreachable` for a transport failure.
- Kept: `request_json`, `events` and every other client method unchanged.
- Consumed by orch-file-download-route.

#### Expected outcome

The orchestrator can open a wrapper download, see its status and headers before any byte is relayed, and stream the raw bytes.

#### Steps

- Red: add `test_open_download_streams_raw_bytes` and `test_open_download_errors` to `tests/test_wrapper_client.py` (`httpx.MockTransport`); run `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_wrapper_client.py`: fails (no method).
- Green: `open_download`; run the task's verify: passes, quote the pytest summary line.

#### Notes

- Rulings and their pin tests: raw bytes (no content decoding) pinned by `test_open_download_streams_raw_bytes`; the response is closed before an error is raised, pinned by `test_open_download_errors`.
- Model it on `events` (wrapper/client.py:234): `self._http.build_request(...)` then `self._http.send(request, stream=True)`; `httpx.Timeout(DEFAULT_TIMEOUT)` bounds connect and each read, never the total.

- 2026-10-27 done

### S2: wrapper file download route

- Status: done
- Files: `src/claude_code_wrapper/files.py`, `src/claude_code_wrapper/api/files.py`, `README.md`, `tests/test_api_files.py`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_files.py tests/test_readme_api.py && mise run lint`
- Verified head: 7f7cd159d95e3445299b72c653eb703ef917142a

#### Requirement

Epic README goals, verbatim: "A small download (arrow down) icon on every file row of the Files tree, aligned to the right edge of the file browser." "Clicking it downloads that file from the agent's workspace to the user's computer, byte-exact, for text and binary files of any size (no 1 MiB preview cap)." "New raw-bytes download route in claude-code-wrapper and an orchestrator route forwarding it, with the existing workspace path guards."

User decision U1, verbatim: "Download every file type (text and binary) of any size through a new raw-bytes streaming route in the wrapper (Content-Type application/octet-stream or sniffed mime, Content-Disposition attachment with an RFC 6266 filename*), forwarded by a streaming orchestrator route under the existing sessions/{id}/files namespace, reusing the existing path traversal and workspace-root guards and auth; no size cap beyond what the guards impose."

User decision U2, verbatim: "Directories, symlinks to directories and type 'other' show no download icon; symlinks to files download the target bytes only if the existing guard allows it."

This task is the claude-code-wrapper part: design D1 (raw-bytes route `GET /v1/sessions/{id}/files/download?path=`), D2 (response headers) and D3 (listing field `target_type`), as written in design.md.

Scope (claude-code-wrapper):
- `src/claude_code_wrapper/files.py`: a helper that resolves with `_resolve`, opens with `_open_nofollow`, checks `S_ISREG` on `fstat` of that descriptor and returns what the route needs to stream (descriptor, size, resolved name, mime) before any byte is sent; `list_directory` adds `target_type` to every entry (D3).
- `src/claude_code_wrapper/api/files.py`: `GET /sessions/{session_id}/files/download` streaming the bytes (D1) with the D2 headers; errors raised before the response starts, through the existing `_raise`.
- `README.md`: a `### GET /v1/sessions/{id}/files/download` section in the API reference (query, headers, no size cap, not redacted, errors), the Trust model file-API sentence naming the download route, and `target_type` in the `GET /v1/sessions/{id}/files` section.
- `tests/test_api_files.py`: the new tests below.

#### Acceptance conditions

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

#### Files

- `src/claude_code_wrapper/files.py`
- `src/claude_code_wrapper/api/files.py`
- `README.md`
- `tests/test_api_files.py`

#### Interfaces

- New wrapper route `GET /v1/sessions/{id}/files/download?path=<rel>` (`api/files.py`): 200 with the raw bytes; headers `Content-Type` (guessed mime or `application/octet-stream`), `Content-Length` (fstat size), `Content-Disposition: attachment; filename="<fallback>"; filename*=UTF-8''<encoded>`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store`; errors 400 `invalid_path`, 400 `not_a_file`, 401 `unauthorized`, 404 `not_found` as JSON envelopes.
- Listing entry (`files.py:list_directory`): `{name, type, size, mtime, target_type}`, `target_type` one of `"dir"`, `"file"`, `"other"`, `null`.
- Kept: `files.py:resolve_in_workdir`, `_resolve`, `_open_nofollow`, `read_preview` and the `files/content` contract unchanged.
- Consumed by fake-wrapper-download (the fake mirrors both) and orch-file-download-route.

#### Expected outcome

`curl -H "$H" -OJ "localhost:8080/v1/sessions/$SID/files/download?path=<rel>"` saves the file byte-exact under its name, for any size and type; every path `files/content` refuses is refused the same way; the listing tells a symlink to a file from a symlink to a directory.

#### Steps

- Red: add the nine tests of the acceptance conditions to `tests/test_api_files.py`; run `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_files.py`: the download tests fail with 404 (no route) and `test_list_symlink_target_type` fails on the missing key.
- Green: the `files.py` helper and `target_type`, the route in `api/files.py`; rerun: the file tests pass.
- Docs: README route section, Trust model sentence, listing `target_type`; run the task's verify: passes, quote the pytest summary line.

#### Notes

- Rulings and their pin tests: download name = last segment of the normalised requested path (the link name for a symlink), pinned by `test_download_content_disposition`; fallback character set (printable ASCII 0x20-0x7E minus `"` and `\`, each other character `_`), pinned by `test_download_content_disposition`; `target_type` null for dangling, looping and escaping links whatever the outside target is, pinned by `test_list_symlink_target_type`; bytes read stop at the `fstat` size, pinned by `test_download_bytes_exact`.
- Mimic `test_content_open_nofollow_and_fstat` and `test_escapes_refused` for the guard tests; `make_client(work, tmp_path, file_preview_max_bytes=4)` sets limits. Count descriptors with `os.listdir("/proc/self/fd")`.
- Compute `target_type` with `resolve_in_workdir` then `os.stat` of the resolved path; `ValueError` or `OSError` gives null.
- Never block the event loop on a read (worker thread); close the descriptor on every exit, including a client that disconnects mid-stream.
- The component has no MEMORY.md; record the non-obvious calls in the README section.
- Known environment failures outside this task's verify: `tests/test_container.py` (no docker) and the 3 process-group tests (container PID 1).

- 2026-10-27 done

### S3: fake wrapper download

- Status: done
- Files: `tests/fakes/fake_wrapper.py`, `tests/test_fake_wrapper_contract.py`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_fake_wrapper_contract.py && mise run lint`
- Verified head: bd809e04997d2b08d5af63df3527aabaf5bed737

#### Requirement

Design D6, verbatim: "`tests/fakes/fake_wrapper.py` gets the download route and `target_type`, and `tests/test_fake_wrapper_contract.py` gets cases that run on both legs (fake locally, real image in CI), plus fake-only cases for what the real image cannot set up (symlinks, a file over the preview cap). Why: orchestrator route tests run against the fake, so the fake must be held to the real wrapper's contract (retro of generic-any-mcp-with-git-and: fakes encoded a wrong assumption)."

The contract the fake mirrors is the claude-code-wrapper one built by task wrapper-file-download-route (design D1, D2, D3): `GET /v1/sessions/{id}/files/download?path=` streams the raw bytes with `Content-Type` (guessed mime, else `application/octet-stream`), `Content-Length`, `Content-Disposition: attachment; filename="<fallback>"; filename*=UTF-8''<encoded>` (name = last segment of the normalised requested path), `X-Content-Type-Options: nosniff`, `Cache-Control: no-store`; it refuses with the same codes as `files/content`; every listing entry carries `target_type` (`dir`, `file`, `other` for a symlink resolving inside the workdir, else null; null for non-symlinks). Read the wrapper's README section and `src/claude_code_wrapper/api/files.py` on its epic branch before writing the fake, and copy the header construction semantics exactly.

Scope (agents-orchestrator):
- `tests/fakes/fake_wrapper.py`: the download route (streamed, honours `_auth`, `_get`, `_locate`, no `file_preview_max_bytes` cap) and `target_type` in `list_files`.
- `tests/test_fake_wrapper_contract.py`: new both-leg cases `test_files_download` and `test_files_download_errors`; new fake-only cases `test_fake_files_download_ignores_preview_cap` and `test_fake_files_symlink_target_type`. `test_files_list` asserts the entry key set `{"name", "type", "size", "mtime"}`, which is no longer accurate because the listing contract gains `target_type` (D3): it asserts the five keys and `target_type` null for the file and directory entries.

#### Acceptance conditions

- ac1: on both legs, `files/download` returns the exact bytes of a text file and of the `blob.bin` file of `_tree`, with Content-Length, Content-Type (`text/x-python` for `src/main.py`), Content-Disposition `attachment; filename="main.py"; filename*=UTF-8''main.py`, nosniff and no-store (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_files_download]
- ac2: on both legs, the download refuses `../outside`, `/etc/passwd`, a NUL path and `src/../../x` with 400 invalid_path, `src` and the empty path with 400 not_a_file, `missing` and an unknown session with 404 not_found, and no bearer with 401 (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_files_download_errors]
- ac3: on the fake, a file larger than `file_preview_max_bytes` downloads fully and byte-exact (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_files_download_ignores_preview_cap]
- ac4: on the fake, listing `target_type` is `file`, `dir`, `other` for links to a file, a directory, a FIFO inside the workdir, null for a dangling link and a link escaping the workdir, null for non-symlinks (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_files_symlink_target_type]
- ac5: the listing contract case asserts the five entry keys including `target_type` [evidence: test:tests/test_fake_wrapper_contract.py::test_files_list]
- ac6: the contract suite (fake leg) and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_fake_wrapper_contract.py && mise run lint]

#### Files

- `tests/fakes/fake_wrapper.py`
- `tests/test_fake_wrapper_contract.py`

#### Interfaces

- Fake route `GET /v1/sessions/{session_id}/files/download` in `tests/fakes/fake_wrapper.py:FakeWrapper` with the wrapper contract of wrapper-file-download-route (bytes, headers, error codes); `list_files` entries gain `target_type`.
- Kept: every existing fake control (`files_max_entries`, `file_preview_max_bytes`, `set_unreachable`, `workdir(sid)`).
- Consumed by orch-file-download-route (`tests/test_api_file_download.py`, `tests/test_api_files.py`).

#### Expected outcome

The fake answers the download and the listing exactly as the real wrapper does, and one contract suite proves it on both legs (fake here, real image in CI after orch-wrapper-pin-download).

#### Steps

- Red: add `test_files_download`, `test_files_download_errors`, `test_fake_files_download_ignores_preview_cap`, `test_fake_files_symlink_target_type` and the five-key assertion in `test_files_list`; run `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_fake_wrapper_contract.py`: the new cases fail (404, missing key).
- Green: the fake route and `target_type`; run the task's verify: passes, quote the pytest summary line.

#### Notes

- The real leg (`-m integration`, real wrapper image) runs only in CI and passes only once orch-wrapper-pin-download pins the wrapper commit carrying the route; locally the verify runs the fake leg.
- `_tree` writes files through the turn `files` field (text only) on both legs; symlinks, the FIFO and the over-cap file are written straight into `fake.workdir(sid)` in the fake-only cases.
- Build the fake's headers with the same rules as the wrapper (copy the semantics from the wrapper's `api/files.py` on its epic branch, do not import the wrapper package).

- 2026-10-27 done

### S4: orch file download route

- Status: done
- Files: `src/agents_orchestrator/api/workspace.py`, `src/agents_orchestrator/api/schemas.py`, `README.md`, `openapi.json`, `MEMORY.md`, `tests/test_api_file_download.py`, `tests/test_api_files.py`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_file_download.py tests/test_readme_api.py tests/test_fake_wrapper_contract.py tests/test_wrapper_client.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint`
- Verified head: 33d1c8fafb09af72ec2dbb3d1683547e438f36d6

#### Requirement

Epic README goal, verbatim: "New raw-bytes download route in claude-code-wrapper and an orchestrator route forwarding it, with the existing workspace path guards." and "Clicking it downloads that file from the agent's workspace to the user's computer, byte-exact, for text and binary files of any size (no 1 MiB preview cap)."

User decision U1, verbatim: "Download every file type (text and binary) of any size through a new raw-bytes streaming route in the wrapper (Content-Type application/octet-stream or sniffed mime, Content-Disposition attachment with an RFC 6266 filename*), forwarded by a streaming orchestrator route under the existing sessions/{id}/files namespace, reusing the existing path traversal and workspace-root guards and auth; no size cap beyond what the guards impose."

Design D4, verbatim: "in `api/workspace.py` (the layering pin), query `path` and optional `agent_id`, agent choice by the existing `resolve_agent` (404 `not_found`, 409 `agent_not_ready`, 503 `unavailable`). A new `WrapperClient.open_download` (`wrapper/client.py`, modelled on `events`) sends the streamed GET with the bearer only in `Authorization` and inspects the status before any byte reaches the browser: wrapper 4xx is re-raised with the wrapper's status and code (token scrubbed), 5xx is 502 `wrapper_error`, transport failure is 502 `wrapper_unreachable`, the same map as `forward` (share one mapping helper rather than copying it). A 2xx becomes a `StreamingResponse` relaying the raw upstream chunks (`aiter_raw`, so bytes and `Content-Length` stay exact) with the wrapper's `Content-Type`, `Content-Length` and `Content-Disposition`, plus `X-Content-Type-Options: nosniff` and `Cache-Control: no-store` set by the orchestrator. The upstream response is closed when the relay ends, fails or the browser goes away. No total timeout (any size); connect and each read keep the client's `DEFAULT_TIMEOUT`. A failure after the first byte aborts the connection, so the browser marks the download failed instead of saving a short file. OpenAPI: a `200` with `application/octet-stream`, schema `string`/`binary`. README `## API` gets the route section. Not on the service-port allowlist (my call: no service needs it, as for the other file routes); no Origin guard (top-level GET, like the other file GETs)."

Design D3 (orchestrator part): "The orchestrator `FileEntry` schema and the fake wrapper carry it" - `target_type: Literal["dir", "file", "other"] | None` on `schemas.FileEntry`, passed through by the listing.

Design D7, verbatim: "the orchestrator route's behaviour tests live in a new `tests/test_api_file_download.py` that needs no database: a real `FakeWrapper`, `workspace.resolve_agent` monkeypatched to return a `WrapperTarget` for it (or to raise `ApiError`), and a stub pool whose `connection()` is an async context manager. The DB-backed `tests/test_api_files.py` is extended for agent choice and scoping on the new route and the listing key set; it runs in CI only."

Scope (agents-orchestrator):
- `src/agents_orchestrator/api/workspace.py`: route `GET /api/v1/sessions/{session_id}/files/download`; the shared error-mapping helper used by `forward` and the download.
- `src/agents_orchestrator/api/schemas.py`: `FileEntry.target_type`.
- `README.md`: `### GET /api/v1/sessions/{session_id}/files/download` in `## API` (query, headers, no cap, not redacted, errors 400 invalid_path, 400 not_a_file, 404 not_found, 409 agent_not_ready, 502 wrapper_unreachable, 502 wrapper_error, 503 unavailable, and how a mid-stream failure ends the response); `target_type` in the listing section.
- `openapi.json`: regenerated with `uv run python -m agents_orchestrator.api.openapi > openapi.json`.
- `MEMORY.md`: a dated entry (2026-10-27, file-download-in-file-browse D4) for the first byte-streaming proxy route: why status is mapped before headers, why raw chunks, why no total timeout, why not on the service port.
- `tests/test_api_file_download.py` (new, Docker-free): the tests below.
- `tests/test_api_files.py` (CI only): `test_no_ready_agent` and `test_agent_id_selects_and_scopes` loop over `files/download` too (new route, same agent rules); `test_list_proxied_from_first_ready_agent` asserts the entry key set `{"name", "type", "size", "mtime"}`, which is no longer accurate because `target_type` joins the listing (D3): it asserts the five keys.

#### Acceptance conditions

- ac1: through the route, a text file, a binary file and a 3 MiB + 1 byte file download byte-exact from the fake wrapper, with the wrapper's Content-Type, Content-Length and Content-Disposition and the orchestrator's `X-Content-Type-Options: nosniff` and `Cache-Control: no-store` (new) [evidence: test:tests/test_api_file_download.py::test_download_streams_bytes_exact]
- ac2: wrapper refusals pass through with their status and code in the error envelope (400 invalid_path, 400 not_a_file, 404 not_found), a wrapper 401 is relayed without the derived token in the body, an unreachable wrapper is 502 wrapper_unreachable and a wrapper 5xx is 502 wrapper_error (new) [evidence: test:tests/test_api_file_download.py::test_download_errors_pass_through]
- ac3: `resolve_agent` refusals (404 not_found, 409 agent_not_ready, 503 unavailable) answer as JSON error envelopes before any wrapper call (new) [evidence: test:tests/test_api_file_download.py::test_download_resolve_errors]
- ac4: the upstream response is closed after a complete download and after a refused one (new) [evidence: test:tests/test_api_file_download.py::test_download_closes_upstream]
- ac5: listing entries carry the wrapper's `target_type` through the orchestrator (new) [evidence: test:tests/test_api_file_download.py::test_listing_target_type_passes_through]
- ac6: README documents the route and openapi.json matches the app (the 200 is `application/octet-stream`) [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_readme_api.py && python3 -c "import json,sys; d=json.load(open('openapi.json')); r=d['paths']['/api/v1/sessions/{session_id}/files/download']['get']['responses']['200']['content']; sys.exit(0 if 'application/octet-stream' in r else 1)"]
- ac7: only `api/workspace.py` imports the wrapper package (layering pin unchanged) [evidence: test:tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper]
- ac8: (CI only, needs Docker) the DB-backed file route tests cover agent choice and scoping on `files/download` and the five listing keys [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_files.py]
- ac9: targeted Docker-free suites and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_file_download.py tests/test_readme_api.py tests/test_fake_wrapper_contract.py tests/test_wrapper_client.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint]
- ac10: a wrapper stream that fails after the first byte aborts the client response (it errors, never ends as a clean short body) and the upstream is closed (new) [evidence: test:tests/test_api_file_download.py::test_download_midstream_failure_aborts]

#### Files

- `src/agents_orchestrator/api/workspace.py`
- `src/agents_orchestrator/api/schemas.py`
- `README.md`
- `openapi.json`
- `MEMORY.md`
- `tests/test_api_file_download.py`
- `tests/test_api_files.py`

#### Interfaces

- New route `GET /api/v1/sessions/{session_id}/files/download?path=<rel>&agent_id=<uuid?>` in `api/workspace.py`: 200 `application/octet-stream` (OpenAPI schema `string`/`binary`) relaying the wrapper's `Content-Type`, `Content-Length`, `Content-Disposition`, plus `X-Content-Type-Options: nosniff`, `Cache-Control: no-store`; errors as JSON envelopes: wrapper 4xx passed through, 409 `agent_not_ready`, 404 `not_found`, 502 `wrapper_unreachable`, 502 `wrapper_error`, 503 `unavailable`.
- `api/schemas.py:FileEntry.target_type: Literal["dir", "file", "other"] | None`.
- One error-mapping helper in `api/workspace.py` used by `forward` and the download (no copied map).
- Uses `wrapper/client.py:WrapperClient.open_download` (wrapper-client-download) and the fake of fake-wrapper-download.
- Consumed by web-sync-orchestrator-api (openapi.json) and web-download-icon (URL, `target_type`).

#### Expected outcome

`GET /api/v1/sessions/<id>/files/download?path=<rel>` streams the file byte-exact from the first usable agent, with download headers; refusals answer as JSON before any byte; the listing carries `target_type`; openapi.json and README document both.

#### Steps

- Red: write `tests/test_api_file_download.py` (five tests of the acceptance conditions) and the CI-only extensions in `tests/test_api_files.py`; run `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_file_download.py`: fails (404 route, missing key).
- Green: the route, the shared error map, `FileEntry.target_type`; rerun: passes.
- Docs: README `## API` section and listing `target_type`; `uv run python -m agents_orchestrator.api.openapi > openapi.json`; MEMORY.md entry; run the task's verify: passes, quote the pytest summary line. `tests/test_api_files.py` needs Docker and is left to CI.

#### Notes

- Docker-free rig (D7): `create_app(make_settings(master_key=KEY), pool=<stub>)` with a stub whose `connection()` is an async context manager; monkeypatch `workspace.resolve_agent` to return `WrapperTarget(agent_id, session_id, pod_name, url=fake.base_url, wrapper_session_id=sid, token=fake.token)` or raise `ApiError`; drive it with `client_for(app)` from `tests/test_api_sessions.py` (importing it does not start Postgres; only its fixtures do).
- `get_client(app)` is the shared httpx client (`trust_env=False`); tests may preset `app.state.wrapper_http`.
- Close the upstream response on every exit path (complete, refused, browser disconnect); pin with a spy on `httpx.Response.aclose`.
- The fake wrapper 5xx can be produced with an `httpx.MockTransport` preset on `app.state.wrapper_http` if the fake has no control for it.
- `tests/test_api_files.py` and the contract real leg run only in CI (Docker); say so in the hand-back rather than claiming them.

- 2026-10-27 amended: builder check: design's abort-after-first-byte behaviour had no acceptance condition (my call)

- 2026-10-27 done

### S5: orch wrapper pin download

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `e2e/agent-test.Dockerfile`, `README.md`, `tests/e2e/test_e2e_kind.py`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_images.py tests/test_render.py && mise run lint`
- Verified head: 34194f4416736c64635cde6cd6ddba7f6f99928b

#### Requirement

Design D9, verbatim: "once the wrapper change is merged on claude-code-wrapper `main`, the orchestrator pins that merge commit in the dev dependency (`pyproject.toml`, `uv.lock`), README `## Images` and `e2e/agent-test.Dockerfile` (`BASE_IMAGE`, `WRAPPER_SHA`), and the kind e2e gets a download case, so CI's integration leg and e2e run the real route. Precedent: done epic web-ui-cluster-tabs-with-fil task `wrapper-sha-pin`."

Needs a merged upstream: the claude-code-wrapper PR carrying task wrapper-file-download-route merged on `main`. Do not start before `git -C <wrapper checkout> fetch origin main` shows a `main` commit whose `src/claude_code_wrapper/api/files.py` has the `files/download` route; the pin is that merge commit (40-character sha, image tag its first 7 characters). Merged (2026-10-27): claude-code-wrapper PR #5, merge commit `4581f3bff79741d934272653c1a93d0ccfc95ba8`; `<sha>` is that value and `<sha7>` is `4581f3b`.

Scope (agents-orchestrator):
- `pyproject.toml`: dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<sha>`; `uv.lock` refreshed with `uv lock`.
- `e2e/agent-test.Dockerfile`: `ARG BASE_IMAGE=harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`, `ARG WRAPPER_SHA=<sha>`.
- `README.md` `## Images`: the recommended agent image `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`.
- `tests/e2e/test_e2e_kind.py`: new `test_files_download_through_api`, modelled on `test_files_list_and_read_through_api`: the agent writes a text file and a binary file (bytes 0-255) through its shell; the API download returns them byte-exact with `Content-Disposition` attachment; `..`, `../etc/passwd` and `/etc/passwd` are 400 invalid_path; the listing entry of the file has `target_type` null.

#### Acceptance conditions

- ac1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit, the merge commit carrying the download route [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- ac2: the dev dependency and README image pin agree [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- ac3: the pinned wrapper package has the download route [evidence: command:unset VIRTUAL_ENV && uv run --frozen python -c "import claude_code_wrapper.api.files as f, sys; sys.exit(0 if any(getattr(r, 'path', '').endswith('/files/download') for r in f.router.routes) else 1)"]
- ac4: (CI only, kind) the e2e download case passes against the real agent image (new) [evidence: command:mise run test:e2e]
- ac5: images and render suites and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_images.py tests/test_render.py && mise run lint]

#### Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`
- `tests/e2e/test_e2e_kind.py`

#### Interfaces

- The wrapper pin (pyproject dev dependency, `uv.lock`, `e2e/agent-test.Dockerfile` `BASE_IMAGE` and `WRAPPER_SHA`, README `## Images`), all one sha, the claude-code-wrapper `main` merge commit carrying wrapper-file-download-route.
- New kind e2e case `tests/e2e/test_e2e_kind.py::test_files_download_through_api`.

#### Expected outcome

CI's integration contract leg and kind e2e build the agent image from the wrapper commit that has the download route, and the e2e proves a byte-exact download through the API.

#### Steps

- Confirm the merged upstream (the requirement's precondition) and read the merge sha.
- Change the pyproject pin, run `uv lock`; run `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_images.py`: the Dockerfile and README checks fail on the old sha.
- Update the Dockerfile args and README `## Images`, add the e2e case; run the task's verify: passes, quote the pytest summary line. The e2e runs in CI only.

#### Notes

- `tests/test_images.py` ties pyproject, uv.lock, README Images and the Dockerfile to one sha (`test_ccw_dev_dependency_matches_agent_image_sha`, `test_agent_test_dockerfile_matches_dev_dependency`); `tests/test_render.py` validates rendered configs against the pinned wrapper's config schema.
- The Harbor image exists only for wrapper `main` builds; check with `regctl image digest` when credentials allow, else `scripts/e2e.sh` builds from source.
- Precedent: done epic web-ui-cluster-tabs-with-fil task `wrapper-sha-pin` (amended with the merge sha when the wrapper PR merged).

- 2026-10-27 amended: wrapper PR #5 merged at 4581f3b

- 2026-10-27 done

### S6: web sync orchestrator api

- Status: done
- Files: `openapi/orchestrator.json`, `openapi/orchestrator.source`, `src/api/schema.d.ts`
- Verify: `mise exec -- npm run check:api && mise exec -- npx tsc -b && mise run lint`
- Verified head: 47a13832e81939c5500e81a061d4b92ca953e01c

#### Requirement

User decision U4, verbatim: "After the orchestrator route lands, regenerate the web client schema with `npm run sync:api -- orchestrator` and keep `npm run check:api` green."

Design D8, verbatim: "after the orchestrator route lands, `npm run sync:api -- orchestrator` (vendors `openapi/orchestrator.json`, `openapi/orchestrator.source`, regenerates `src/api/schema.d.ts`) and `npm run check:api` stays green. The sync takes everything between the current pin (ff54218) and the orchestrator head."

Scope (agents-web): run `mise exec -- npm run sync:api -- orchestrator --from <agents-orchestrator tree at the commit of orch-file-download-route>` (the default `../agents-orchestrator` is the sibling integration tree; the script refuses an uncommitted `openapi.json`). Commit exactly the three generated files. No hand edits.

#### Acceptance conditions

- ac1: `openapi/orchestrator.source` names the agents-orchestrator commit that carries the download route, and the vendored document has it [evidence: command:grep -q '/api/v1/sessions/{session_id}/files/download' openapi/orchestrator.json && grep -q 'target_type' openapi/orchestrator.json]
- ac2: the generated types carry the route and `FileEntry.target_type` [evidence: command:grep -q 'files/download' src/api/schema.d.ts && grep -q 'target_type' src/api/schema.d.ts]
- ac3: the generated schemas match the vendored documents [evidence: command:mise exec -- npm run check:api]
- ac4: the type check and lint pass [evidence: command:mise exec -- npx tsc -b && mise run lint]

#### Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`

#### Interfaces

- Generated: `openapi/orchestrator.json`, `openapi/orchestrator.source` (`agents-orchestrator <sha>`), `src/api/schema.d.ts` (`paths['/api/v1/sessions/{session_id}/files/download']`, `components['schemas']['FileEntry']['target_type']`).
- Consumed by web-download-icon.

#### Expected outcome

The web client's generated types match the orchestrator commit carrying the download route, and `npm run check:api` is green.

#### Steps

- Run `mise exec -- npm run sync:api -- orchestrator --from <agents-orchestrator tree at orch-file-download-route's commit>`: it prints the gen:api output and exits 0.
- Run the task's verify: passes. Commit exactly the three generated files.

#### Notes

- The default `../agents-orchestrator` is the sibling integration tree; the script refuses an `openapi.json` with uncommitted changes.
- If the regenerated types break compilation elsewhere (drift since ff54218), report it as a `discovered` entry; do not patch it here.
- No hand edits to generated files.

- 2026-10-27 done

### S7: web download icon

- Status: done
- Files: `src/api/files.ts`, `src/api/files.test.ts`, `src/files/FilesPanel.tsx`, `src/files/FilesPanel.test.tsx`, `MEMORY.md`
- Verify: `mise exec -- npx vitest run src/files/FilesPanel.test.tsx src/api/files.test.ts src/layout/designRules.test.ts src/nomenclature.test.ts && mise exec -- npx tsc -b && mise run lint`
- Verified head: e7a2499db68fcf04a25f324fed88875c3faea644

#### Requirement

User request (2026-10-27), verbatim: "In file browser, I need to be able to download a file. I expect small "arrow down" icon aligned with right side of the file browser, that's going to download a file to my computer from agent's workspace."

Epic README goals, verbatim: "A small download (arrow down) icon on every file row of the Files tree, aligned to the right edge of the file browser." and "Clicking it downloads that file from the agent's workspace to the user's computer, byte-exact, for text and binary files of any size (no 1 MiB preview cap)."

User decision U2, verbatim: "Directories, symlinks to directories and type 'other' show no download icon; symlinks to files download the target bytes only if the existing guard allows it."

User decision U3, verbatim: "The UI triggers the download with a plain anchor to the relative basePath URL (download attribute), no blob buffering; icon FileDownloadOutlined, small IconButton with aria-label 'Download <name>', right-aligned in the tree row, click does not open the preview (stopPropagation); errors (e.g. 404, 403) cannot be read from a plain anchor, so state in design.md how errors surface (my call: plain anchor, browser shows the error page) or choose a fetch+blob path if you judge it necessary and say why."

Design D5, verbatim: "the icon is `IconButton component="a"` with `href` = the relative URL `${base()}/sessions/<id>/files/download?path=<rel>` (new `fileDownloadUrl` in `src/api/files.ts`), the `download` attribute set to the entry name, `size="small"`, `aria-label="Download <name>"`, icon `FileDownloadOutlined` (`fontSize="small"`). It is the last element of the tree row and the name grows, so the icon sits on the right edge. Its click handler calls `stopPropagation`, so the click neither opens the preview nor selects the row. Shown per D3; no icon on `dir`, `other`, or `symlink` rows whose `target_type` is not `file`. No `agent_id`: the same first usable agent the listing uses."

Design D3 (UI part): "agents-web shows the download icon for `type == "file"` and for `type == "symlink"` with `target_type == "file"`."

Scope (agents-web):
- `src/api/files.ts`: `fileDownloadUrl(sessionId: string, path: string): string` built with `base()` and `query({ path })`; the file header comment stays accurate ("read-only" still holds).
- `src/api/files.test.ts` (new): pins the URL.
- `src/files/FilesPanel.tsx`: `Row` gains an optional trailing action; file rows and symlink-to-file rows render the download anchor; the name element grows so the icon sits on the right edge.
- `src/files/FilesPanel.test.tsx`: the new tests below; the hoisted `api` mock of `../api/files` gains `fileDownloadUrl` (the panel now imports it; this extends the mock for the new export, it does not change any existing assertion).
- `MEMORY.md`: a dated entry (2026-10-27, file-download-in-file-browse D5): plain anchor, why not fetch plus blob, how errors surface.

#### Acceptance conditions

- ac1: `fileDownloadUrl('c1', 'src/a b.txt')` is the relative `${base()}/sessions/c1/files/download?path=src%2Fa+b.txt` under the runtime config's basePath (new) [evidence: command:mise exec -- npx vitest run src/api/files.test.ts -t 'fileDownloadUrl']
- ac2: every `file` row and every `symlink` row with `target_type` `file` has a link named `Download <name>` whose `href` is `fileDownloadUrl(sessionId, path)` and whose `download` attribute is the name, with the FileDownloadOutlined icon; `dir`, `other` and `symlink` rows with `target_type` `dir`, `other` or null have none (new) [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx -t 'download_icon_only_on_file_rows']
- ac3: clicking the download link neither calls `readFile`, opens a preview nor selects the row (new) [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx -t 'download_click_does_not_open_preview']
- ac4: the download link is the last element of its row and the row's name element grows (`flex-grow: 1`), so the icon sits at the right edge (new) [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx -t 'download_icon_right_aligned']
- ac5: the design rules and nomenclature guards hold for the changed files [evidence: command:mise exec -- npx vitest run src/layout/designRules.test.ts src/nomenclature.test.ts]
- ac6: the Files panel and files API suites, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/files/FilesPanel.test.tsx src/api/files.test.ts && mise exec -- npx tsc -b && mise run lint]

#### Files

- `src/api/files.ts`
- `src/api/files.test.ts`
- `src/files/FilesPanel.tsx`
- `src/files/FilesPanel.test.tsx`
- `MEMORY.md`

#### Interfaces

- `src/api/files.ts:fileDownloadUrl(sessionId: string, path: string): string`, built with `base()` and `query({ path })`.
- `src/files/FilesPanel.tsx:Row` gains an optional trailing action; the download anchor is `IconButton component="a" href download size="small" aria-label="Download <name>"` with `FileDownloadOutlined fontSize="small"`.
- Kept: `listFiles`, `readFile`, preview behaviour, polling and event refresh unchanged.

#### Expected outcome

Each file row (and each symlink-to-file row) of the Files tree shows a small arrow-down icon at its right edge; clicking it saves the file through the browser's download, without opening the preview.

#### Steps

- Red: write `src/api/files.test.ts` and the three FilesPanel tests (`download_icon_only_on_file_rows`, `download_click_does_not_open_preview`, `download_icon_right_aligned`), add `fileDownloadUrl` to the hoisted `api` mock; run `mise exec -- npx vitest run src/files/FilesPanel.test.tsx src/api/files.test.ts`: the new tests fail.
- Green: `fileDownloadUrl`, the `Row` action and the anchor; rerun: passes.
- MEMORY.md entry; run the task's verify: passes, quote the vitest summary line.

#### Notes

- Rulings and their pin tests: icon rows (file, symlink with `target_type` file) versus no-icon rows (dir, other, symlink with `target_type` dir, other or null), pinned by `download_icon_only_on_file_rows`; click isolation, pinned by `download_click_does_not_open_preview`; right alignment, pinned by `download_icon_right_aligned`.
- Extending the hoisted `api` mock with `fileDownloadUrl` is required because the panel imports it; no existing assertion changes.
- designRules forbid `title=` on IconButton (use aria-label) and off-grid spacing; `getComputedStyle` works with emotion in jsdom (precedent `src/layout/TopBar.test.tsx:120`). The stopPropagation precedent is `src/terminal/TerminalPanel.tsx:146-149`.
- MEMORY.md entry (2026-10-27, file-download-in-file-browse D5): plain anchor, why not fetch plus blob (buffers the whole file), errors surface in the browser, not the panel.
- The full suite has 10 load-dependent timeouts in unrelated files (PresetForm, ScheduleForm, Endpoints, FiltersEditor); run only the files in `verify`.

- 2026-10-27 done

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
