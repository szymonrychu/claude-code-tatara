---
title: wrapper client and sse
status: todo
repo: agent-orchestrator
value: "One typed, tested way to talk to every wrapper endpoint the orchestrator needs, including a resumable SSE reader."
files: [src/agent_orchestrator/wrapper/__init__.py, src/agent_orchestrator/wrapper/client.py, src/agent_orchestrator/wrapper/sse.py, src/agent_orchestrator/wrapper/models.py, tests/test_wrapper_client.py]
verify: "uv run pytest tests/test_wrapper_client.py -q && mise run lint"
depends_on: [scaffold-repo-and-cli]
owns: [wrapper-client]
uses: [wrapper-idle-since, wrapper-context-surface, wrapper-user-message-event, wrapper-peers-view]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# wrapper client and sse

## Requirement

An async httpx client for claude-code-wrapper's `/v1` API (D5). It depends on epic claude-code-wrapper-orchestr for the `idle_since`, `context`, `user_message` and `/v1/peers` surface.

- `WrapperClient(base_url, token, http=None)` sends `Authorization: Bearer <token>`.
- Session methods: `list_sessions()`, `create_session(name, workdir, model=None, effort=None)`, `get_session(id) -> Snapshot`.
- `submit_turn(id, text) -> TurnAccepted | Busy | Unavailable`: 202 maps to TurnAccepted(turn_id), 409 to Busy, 503 and network errors to Unavailable(reason).
- Control methods: `interrupt(id)`, `command(id, name)`, `get_turn(id, turn_id)`.
- `peers() -> PeersView`: `{enabled: false}`, or self plus members.
- `events(id, last_event_id=None) -> AsyncIterator[Envelope]`: streams `GET /v1/sessions/{id}/events` with `Last-Event-ID`.
- `Snapshot` carries state, current_turn_id, `idle_since`, `context {used_tokens, window_tokens, used_percentage, model, source, updated_at} | None`, model and workdir. Unknown fields are ignored.
- `sse.SSEParser`: an incremental parser. It handles `id:`, `event:`, multi-line `data:`, `retry:` and comment lines (`: ping`), LF and CRLF line ends, and chunks split anywhere. It dispatches on a blank line.
- A wrapper error body `{"error": {code, message}}` raises `WrapperError(status, code, message)`.

## Acceptance conditions

- AC1: the SSE parser yields identical events however the byte stream is chunked [evidence: test:tests/test_wrapper_client.py::test_sse_parser_chunk_boundaries]
- AC2: comments are ignored and multi-line data is joined [evidence: test:tests/test_wrapper_client.py::test_sse_comments_and_multiline]
- AC3: submit_turn maps 202, 409, 503 and a network error [evidence: test:tests/test_wrapper_client.py::test_submit_turn_maps_202_409_503]
- AC4: the snapshot parses idle_since and context, and a null context [evidence: test:tests/test_wrapper_client.py::test_snapshot_parses_idle_since_and_context]
- AC5: peers() parses the disabled and enabled shapes [evidence: test:tests/test_wrapper_client.py::test_peers_view_disabled_and_enabled]
- AC6: events() sends Last-Event-ID and the bearer token [evidence: test:tests/test_wrapper_client.py::test_events_sends_last_event_id_and_bearer]
- AC7: an error envelope raises WrapperError with its code [evidence: test:tests/test_wrapper_client.py::test_error_envelope_raises]

## Files

- `src/agent_orchestrator/wrapper/__init__.py`
- `src/agent_orchestrator/wrapper/client.py`
- `src/agent_orchestrator/wrapper/sse.py`
- `src/agent_orchestrator/wrapper/models.py`
- `tests/test_wrapper_client.py`

## Interfaces

- `agent_orchestrator.wrapper.client:WrapperClient` (contract `wrapper-client`)
- `agent_orchestrator.wrapper.models`: `Snapshot`, `Context`, `Envelope`, `PeersView`, `TurnAccepted`, `Busy`, `Unavailable`, `WrapperError`
- `agent_orchestrator.wrapper.sse:SSEParser`

## Expected outcome

Every later process talks to wrappers through one client whose behaviour is pinned by unit tests.

## Steps

- Write tests/test_wrapper_client.py with the seven named tests using `httpx.MockTransport`; run it; expect failures.
- Implement models.py, sse.py and client.py.
- Rerun `uv run pytest tests/test_wrapper_client.py -q`; expect `7 passed`; run `mise run lint`.

## Notes

Field names follow the wrapper README as changed by epic claude-code-wrapper-orchestr (contracts wrapper-idle-since, wrapper-context-surface, wrapper-user-message-event, wrapper-peers-view); read that README section before coding the models. Envelope is `{seq, ts, session_id, type, data}` with SSE `id` = seq (brief-wrapper section 1).
