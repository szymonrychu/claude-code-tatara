---
title: wrapper client download
status: todo
repo: agents-orchestrator
value: the orchestrator can open a streamed wrapper download and learn its errors before relaying a byte
files: [src/agents_orchestrator/wrapper/client.py, tests/test_wrapper_client.py]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest tests/test_wrapper_client.py && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper client download

## Requirement

Design D4, verbatim (client part): "A new `WrapperClient.open_download` (`wrapper/client.py`, modelled on `events`) sends the streamed GET with the bearer only in `Authorization` and inspects the status before any byte reaches the browser: wrapper 4xx is re-raised with the wrapper's status and code (token scrubbed), 5xx is 502 `wrapper_error`, transport failure is 502 `wrapper_unreachable`, the same map as `forward` (share one mapping helper rather than copying it). ... No total timeout (any size); connect and each read keep the client's `DEFAULT_TIMEOUT`."

This task builds the client method only; the mapping to ApiError lives in the route task (orch-file-download-route).

Scope (agents-orchestrator):
- `src/agents_orchestrator/wrapper/client.py`: `async def open_download(self, session_id: str, path: str) -> httpx.Response`: sends `GET /v1/sessions/{session_id}/files/download` with query `path`, the bearer only in the `Authorization` header, streamed (`self._http.send(request, stream=True)`), timeout `httpx.Timeout(DEFAULT_TIMEOUT)` (connect and per read, no total). For status >= 300 it reads the body, closes the response and raises `WrapperError(status, code, message)` through `_raise_for_error`; a transport failure raises `WrapperUnreachable`. For a 2xx it returns the open response; the caller relays `aiter_raw()` and must `aclose()` it.
- `tests/test_wrapper_client.py`: the new tests below, with `httpx.MockTransport` as the file already does.

Rulings and their pin tests: raw bytes (no content decoding) pinned by `test_open_download_streams_raw_bytes`; the response is closed before an error is raised, pinned by `test_open_download_errors`.

## Acceptance conditions

- ac1: `open_download` requests `GET /v1/sessions/<sid>/files/download?path=<rel>` with the bearer only in `Authorization` (not in the URL), returns the open 2xx response whose `aiter_raw()` yields the exact bytes (including NUL and non-UTF-8 bytes) and whose headers are the wrapper's (new) [evidence: test:tests/test_wrapper_client.py::test_open_download_streams_raw_bytes]
- ac2: a wrapper 4xx JSON error raises `WrapperError` with the wrapper's status, code and message, a 5xx raises `WrapperError` with its status, a transport failure raises `WrapperUnreachable`, and the response is closed in each case (new) [evidence: test:tests/test_wrapper_client.py::test_open_download_errors]
- ac3: the wrapper client suite and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_wrapper_client.py && mise run lint]

## Files

- `src/agents_orchestrator/wrapper/client.py`
- `tests/test_wrapper_client.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
