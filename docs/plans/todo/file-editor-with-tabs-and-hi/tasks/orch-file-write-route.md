---
title: orch file write route
status: todo
repo: agents-orchestrator
value: "the browser can save a workspace file through the orchestrator, origin-guarded, with conflicts reported"
files: [src/agents_orchestrator/api/workspace.py, src/agents_orchestrator/api/schemas.py, README.md, openapi.json, MEMORY.md, tests/test_api_file_write.py, tests/test_api_files.py]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_file_write.py tests/test_readme_api.py tests/test_fake_wrapper_contract.py tests/test_origin.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint"
depends_on: [fake-wrapper-file-write]
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

# orch file write route

## Requirement

Epic README goal, verbatim: "RO/RW editor mode: read-only by default, RW lets the user edit and save the file back to the agent's workspace (new write route in claude-code-wrapper and orchestrator)."

User decision U3, verbatim: "(my call) 'RW editor mode': read-only by default with an RO/RW toggle per tab; RW enables editing and Save (button and Ctrl/Cmd+S); new write route in the wrapper (PUT file content, UTF-8 text only, size cap = the existing file_preview_max_bytes, existing workspace path guards, optimistic concurrency via the mtime/size the editor loaded: a changed file answers 409 and the UI offers reload or overwrite) and an orchestrator forwarding route, then `npm run sync:api -- orchestrator`. Binary and too_large files open read-only with the current note, no editor."

Design D5, verbatim: "in `api/workspace.py` (the layering pin), query `path` and optional `agent_id`, agent choice by the existing `resolve_agent` (404 `not_found`, 409 `agent_not_ready`, 503 `unavailable`), the existing `forward` error map (wrapper 4xx passed through with status and code, token scrubbed: 400 `invalid_path`, 400 `not_a_file`, 404 `not_found`, 409 `file_changed`, 413 `too_large`; 5xx 502 `wrapper_error`; transport 502 `wrapper_unreachable`). The route carries the existing Origin guard (`dependencies=guarded`, 403 `forbidden_origin`) because it mutates, like the terminal POST and DELETE. Request model `schemas.WriteFile {content: str, expected: FileStamp | None}` and `schemas.FileStamp {mtime: str, size: int >= 0}`, both `extra="forbid"` (422 `invalid_request` before any wrapper call); response `schemas.FileWritten {session_id, agent_id, path, size, mtime}`. `_file_call` takes the method and an optional JSON body instead of a hard-coded GET, so the three file routes share it. Content is never logged (the `forward` debug lines carry method and path only). Not on the service-port allowlist (no service needs it) and not on the agent port. README `## API` gets the route section; `openapi.json` regenerated; MEMORY.md records the write route and the Origin guard choice. Behaviour tests run without a database (as the download epic's D7): a new `tests/test_api_file_write.py` with a real `FakeWrapper`, `workspace.resolve_agent` monkeypatched and a stub pool; the DB-backed `tests/test_api_files.py` is extended for agent choice on PUT and runs in CI only."

Scope (agents-orchestrator):
- `src/agents_orchestrator/api/workspace.py`: route `PUT /api/v1/sessions/{session_id}/files/content` with `dependencies=guarded`; `_file_call` generalised to a method and an optional JSON body.
- `src/agents_orchestrator/api/schemas.py`: `FileStamp`, `WriteFile`, `FileWritten`.
- `README.md`: `### \`PUT /api/v1/sessions/{session_id}/files/content\`` in `## API` (body, response, the 409 `file_changed` semantics and `expected: null`, the Origin guard, errors 400 invalid_path, 400 not_a_file, 403 forbidden_origin, 404 not_found, 409 agent_not_ready, 409 file_changed, 413 too_large, 422 invalid_request, 502 wrapper_unreachable, 502 wrapper_error, 503 unavailable); the listing and content sections stop calling the workdir read-only where they describe the API as a whole.
- `openapi.json`: regenerated with `uv run python -m agents_orchestrator.api.openapi > openapi.json`.
- `MEMORY.md`: a dated entry (2026-10-27, file-editor-with-tabs-and-hi D5): the write route, why the Origin guard, why not on the service port, content never logged.
- `tests/test_api_file_write.py` (new, Docker-free): the tests below.
- `tests/test_api_files.py` (CI only): `test_no_ready_agent` and the agent choice cases loop over the PUT route too (new route, same agent rules).

## Acceptance conditions

- ac1: a PUT through the route with the loaded stamp writes the file in the fake wrapper's workdir byte-exact and answers `{session_id, agent_id, path, size, mtime}` with the orchestrator session and agent ids (new) [evidence: test:tests/test_api_file_write.py::test_write_proxied]
- ac2: wrapper refusals pass through with their status and code in the error envelope (409 `file_changed` for a stale stamp, 413 `too_large`, 400 `invalid_path`, 400 `not_a_file`, 404 `not_found`); `expected: null` overwrites; a wrapper 401 is relayed without the derived token in the body; an unreachable wrapper is 502 `wrapper_unreachable` and a wrapper 5xx is 502 `wrapper_error` (new) [evidence: test:tests/test_api_file_write.py::test_write_errors_pass_through]
- ac3: a body with an unknown key, without `content`, without `expected` or with a negative `size` answers 422 `invalid_request` and the wrapper receives no request (new) [evidence: test:tests/test_api_file_write.py::test_write_body_validated]
- ac4: a request with an Origin outside `allowed_origins` answers 403 `forbidden_origin` and the wrapper receives no request; an allowed Origin and no Origin pass (new) [evidence: test:tests/test_api_file_write.py::test_write_origin_guarded]
- ac5: `resolve_agent` refusals (404 `not_found`, 409 `agent_not_ready`, 503 `unavailable`) answer as JSON error envelopes before any wrapper call (new) [evidence: test:tests/test_api_file_write.py::test_write_resolve_errors]
- ac6: with logging at DEBUG, no log record of a write carries the file content or the derived token (new) [evidence: test:tests/test_api_file_write.py::test_write_never_logs_content_or_token]
- ac7: the existing GET listing and content routes still answer through the generalised `_file_call` (new) [evidence: test:tests/test_api_file_write.py::test_reads_still_proxied]
- ac8: README documents the route and openapi.json matches the app (the PUT has a `WriteFile` request body and a `FileWritten` 200) [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_readme_api.py && python3 -c "import json,sys; d=json.load(open('openapi.json')); op=d['paths']['/api/v1/sessions/{session_id}/files/content']['put']; ok='WriteFile' in json.dumps(op['requestBody']) and 'FileWritten' in json.dumps(op['responses']['200']); sys.exit(0 if ok else 1)"]
- ac9: only `api/workspace.py` imports the wrapper package (layering pin unchanged) [evidence: test:tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper]
- ac10: (CI only, needs Docker) the DB-backed file route tests cover agent choice and no ready agent on the PUT route [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_files.py]
- ac11: targeted Docker-free suites and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_api_file_write.py tests/test_readme_api.py tests/test_fake_wrapper_contract.py tests/test_origin.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint]

## Files

- `src/agents_orchestrator/api/workspace.py`
- `src/agents_orchestrator/api/schemas.py`
- `README.md`
- `openapi.json`
- `MEMORY.md`
- `tests/test_api_file_write.py`
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
