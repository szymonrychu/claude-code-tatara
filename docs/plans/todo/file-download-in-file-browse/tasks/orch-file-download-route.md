---
title: orch file download route
status: todo
repo: agents-orchestrator
value: "the browser can download any workspace file through the orchestrator, streamed and byte-exact"
files: [src/agents_orchestrator/api/workspace.py, src/agents_orchestrator/api/schemas.py, README.md, openapi.json, MEMORY.md, tests/test_api_file_download.py, tests/test_api_files.py]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_file_download.py tests/test_readme_api.py tests/test_fake_wrapper_contract.py tests/test_wrapper_client.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint"
depends_on: [fake-wrapper-download, wrapper-client-download]
model: opus
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

# orch file download route

## Requirement

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

Notes: `get_client(app)` is the shared httpx client (`trust_env=False`); tests may preset `app.state.wrapper_http`. `make_settings` and `client_for` come from `tests/test_api_sessions.py` (importing it does not start Postgres; only its fixtures do). Pass `master_key` so token derivation works. The upstream response must be closed in every exit path; pin it with a spy on `aclose`.

## Acceptance conditions

- ac1: through the route, a text file, a binary file and a 3 MiB + 1 byte file download byte-exact from the fake wrapper, with the wrapper's Content-Type, Content-Length and Content-Disposition and the orchestrator's `X-Content-Type-Options: nosniff` and `Cache-Control: no-store` (new) [evidence: test:tests/test_api_file_download.py::test_download_streams_bytes_exact]
- ac2: wrapper refusals pass through with their status and code in the error envelope (400 invalid_path, 400 not_a_file, 404 not_found), a wrapper 401 is relayed without the derived token in the body, an unreachable wrapper is 502 wrapper_unreachable and a wrapper 5xx is 502 wrapper_error (new) [evidence: test:tests/test_api_file_download.py::test_download_errors_pass_through]
- ac3: `resolve_agent` refusals (404 not_found, 409 agent_not_ready, 503 unavailable) answer as JSON error envelopes before any wrapper call (new) [evidence: test:tests/test_api_file_download.py::test_download_resolve_errors]
- ac4: the upstream response is closed after a complete download and after a refused one (new) [evidence: test:tests/test_api_file_download.py::test_download_closes_upstream]
- ac5: listing entries carry the wrapper's `target_type` through the orchestrator (new) [evidence: test:tests/test_api_file_download.py::test_listing_target_type_passes_through]
- ac6: README documents the route and openapi.json matches the app (the 200 is `application/octet-stream`) [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_readme_api.py && python3 -c "import json,sys; d=json.load(open('openapi.json')); r=d['paths']['/api/v1/sessions/{session_id}/files/download']['get']['responses']['200']['content']; sys.exit(0 if 'application/octet-stream' in r else 1)"]
- ac7: only `api/workspace.py` imports the wrapper package (layering pin unchanged) [evidence: test:tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper]
- ac8: (CI only, needs Docker) the DB-backed file route tests cover agent choice and scoping on `files/download` and the five listing keys [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_files.py]
- ac9: targeted Docker-free suites and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_file_download.py tests/test_readme_api.py tests/test_fake_wrapper_contract.py tests/test_wrapper_client.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint]

## Files

- `src/agents_orchestrator/api/workspace.py`
- `src/agents_orchestrator/api/schemas.py`
- `README.md`
- `openapi.json`
- `MEMORY.md`
- `tests/test_api_file_download.py`
- `tests/test_api_files.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
