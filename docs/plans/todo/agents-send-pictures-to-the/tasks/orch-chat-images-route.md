---
title: orch chat images route
status: todo
repo: agents-orchestrator
value: "a leader's picture path becomes one connector call with the bytes, read only from its own workspace"
files: [src/agents_orchestrator/api/chat.py, src/agents_orchestrator/api/workspace.py, tests/test_agent_chat.py, tests/test_chat_contract.py, openapi.json, README.md, MEMORY.md]
verify: "uv run --frozen pytest tests/test_agent_chat.py tests/test_chat_contract.py tests/test_readme_api.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint"
depends_on: [orch-chat-contract-refresh]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1901552
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch chat images route

## Requirement

README Goal G1, verbatim: "an agent sends a picture (jpeg, png, gif or webp, judged by content, at most 8,000,000 bytes) from a file in its session workspace to its chat room through a new tool orchestrator_chat_send_image {path, caption?, room?, reply_to?}; the owner sees it in Messenger through the bridge."

README Goal G4, verbatim: "limits and failures are explicit: unsupported type, too large, missing file and rate (5 pictures a minute per session inside the 20 sends a minute) refuse synchronously with a named error; upload failures and bridge error notices mark the send failed, visible in orchestrator_chat_status."

Design D1, verbatim: "The tool takes `path`, absolute under the session workdir or relative, normalised by `api/agent.py:_normalise` (:261); invalid is 400 `invalid_path`. No URL argument."

Design D2, verbatim:
"- Route in api/chat.py runs exactly the checks of `_relay` (require_agent, 403 `trigger_session`, `_leads`, chat_available, `_capped_body`) by sharing them, not copying them; it parses only `path`.
- Seam `read_file_bytes(conn, settings, http, session_id, agent_id, path, max_bytes)` in api/workspace.py over `resolve_agent` and `WrapperClient.open_download`; reads at most max+1 bytes (413 `image_too_large`) inside `asyncio.timeout(10)`, maps errors with `_wrapper_errors` (404 `not_found` etc.). chat.py imports workspace, not wrapper, so the layering test stays unchanged.
- Then POST JSON `{data: base64, path, caption?, room?, reply_to?}` to `{ORCH_CHAT_URL}/chat/v1/images`; status and body pass through unchanged (D2 of the merged epic). Worst case 10 s + 10 s, under 30 s."

Design D7, verbatim: "Orchestrator read cap fixed 8,000,000."

Delta fix-as-ac, verbatim: "Image route runs the same checks as `_relay`, including 403 `trigger_session`."

Constraint, verbatim: "Orchestrator chat relay is JSON, 256 KiB body cap (`_capped_body`, api/chat.py:97), 10 s timeout, stores nothing. Only api/workspace.py may import wrapper (tests/test_api_sessions.py:237)."

Anti-goal, verbatim: "A tool reads an arbitrary file outside the session workdir, or bytes of a non-image (a credentials file) reach the chat."

Scope (agents-orchestrator):
- `api/chat.py`: the checks of `_relay` move into one helper that `_relay` and the new route share; `POST /agent/v1/chat/images` (202 pass-through, OpenAPI body `{path, caption?, room?, reply_to?}`): the capped body (256 KiB) must be a JSON object (else 422 `invalid_request`, my call: the api's existing code), `path` a string that `_normalise` accepts against the caller's session workdir (else 400 `invalid_path`); `read_file_bytes` for the caller's own agent; then the upstream body `{data: <base64>, path: <the normalised workdir-relative path>, ...}` with `caption`, `room` and `reply_to` passed through as the agent sent them (my call: the relative path is what the wrapper download route and the web renderer resolve); forwarded with the same `forward` (10 s, same headers, pass-through, 503 `chat_unavailable`).
- `api/workspace.py`: `read_file_bytes(conn, settings, http, session_id, agent_id, path, max_bytes) -> bytes`: `resolve_agent(session_id=..., agent_id=...)`, `WrapperClient.open_download`, reads raw chunks until more than `max_bytes` (413 `image_too_large`) inside `asyncio.timeout(10)`; wrapper errors through `_wrapper_errors`; the deadline is 502 `wrapper_unreachable` (my call: an existing code); the stream is always closed.
- Tests no longer accurate (named): `tests/test_agent_chat.py::test_readme_documents_chat_routes` (its served-route set gains `POST /agent/v1/chat/images`) and `tests/test_chat_contract.py::test_relay_routes_exist_upstream` (four relayed routes become five).
- `openapi.json` regenerated; README `### Chat` documents five routes and the image route's checks, read cap and codes; MEMORY.md: the image route parses `path` and is the only chat route that reads a body; it reads the caller's own pod.

## Acceptance conditions

- ac1: the leader of a user session gets the file read through its own agent's wrapper and forwarded to /chat/v1/images as {data: base64 of the exact bytes, path: normalised workdir-relative, caption, room, reply_to} with only the chat bearer, X-Orch-Session, X-Orch-Slug and Content-Type; the upstream 202 body comes back unchanged [evidence: test:tests/test_agent_chat.py::test_image_read_and_forwarded]
- ac2: an absolute path under the workdir is normalised; an empty, escaping, outside, NUL, missing or non-string path is 400 invalid_path and a body that is not a JSON object 422 invalid_request, with no wrapper or upstream call [evidence: test:tests/test_agent_chat.py::test_image_invalid_path]
- ac3: the route runs the relay's checks in the relay's order: 401 and 403 identity, 403 trigger_session, 403 not_leader, 503 chat_unconfigured, 413 payload_too_large over 256 KiB; a refusal calls neither the wrapper nor the upstream [evidence: test:tests/test_agent_chat.py::test_image_route_shares_relay_checks]
- ac4: a file of 8,000,000 bytes is forwarded whole; one of 8,000,001 bytes or more is 413 image_too_large after reading at most 8,000,001 bytes [evidence: test:tests/test_agent_chat.py::test_image_read_cap]
- ac5: a wrapper 404 is 404 not_found, a wrapper 5xx 502 wrapper_error, an unreachable wrapper or the 10 s read deadline 502 wrapper_unreachable, an upstream failure 503 chat_unavailable [evidence: test:tests/test_agent_chat.py::test_image_wrapper_and_upstream_errors]
- ac6: the file is read from the calling agent's own pod, never another agent's of the session [evidence: test:tests/test_agent_chat.py::test_image_read_from_caller_pod]
- ac7: only api/workspace.py imports the wrapper client (unchanged test) [evidence: test:tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper]
- ac8: the five relayed routes exist in the vendored upstream contract (updated, named) [evidence: test:tests/test_chat_contract.py::test_relay_routes_exist_upstream]
- ac9: the README documents the five chat routes and their codes (updated, named) [evidence: test:tests/test_agent_chat.py::test_readme_documents_chat_routes]
- ac10: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac11: MEMORY.md records the image route ruling [evidence: command:grep -q 'chat/images' MEMORY.md]
- ac12: the targeted tests and lint pass (no database) [evidence: command:uv run --frozen pytest tests/test_agent_chat.py tests/test_chat_contract.py tests/test_readme_api.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint]

## Files

- `src/agents_orchestrator/api/chat.py`
- `src/agents_orchestrator/api/workspace.py`
- `tests/test_agent_chat.py`
- `tests/test_chat_contract.py`
- `openapi.json`
- `README.md`
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
