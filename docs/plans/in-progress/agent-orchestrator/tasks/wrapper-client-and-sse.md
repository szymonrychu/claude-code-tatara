---
title: wrapper client and sse
status: in-progress
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

- `WrapperClient(base_url, token, http=None, send_timeout=15.0)` sends `Authorization: Bearer <token>`; `send_timeout` bounds `submit_turn` only (D24).
- Session methods: `list_sessions()` (each entry carries state and whether a transcript exists; read manager.py:1020-1034 and the README for the field names), `create_session(name, workdir, model=None, effort=None)`, `get_session(id) -> Snapshot`, `resume_session(id)` (`POST /v1/sessions/{id}/resume`, D27).
- `submit_turn(id, text, metadata=None) -> TurnAccepted | Busy | Gone | ConfigError | Rejected | Unavailable | Ambiguous` maps every outcome (D23, D24): 202 TurnAccepted(turn_id), 409 Busy, 404 or 410 Gone, 401 or 403 ConfigError, 413 or 422 Rejected, 5xx and connect errors (connection refused, connect timeout, DNS failure: nothing was delivered) Unavailable(reason), a read timeout or a connection reset after the request was written Ambiguous(reason). No status is left unmapped; any other 4xx is Rejected. `metadata` is sent as the wrapper's turn `metadata` object (README.md:329, kept on the turn record at turns.py:105).
- Control methods: `interrupt(id)`, `command(id, name)`.
- Turn records (D24): `list_turns(id) -> list[TurnSummary]` (`GET /v1/sessions/{id}/turns`, start order) and `get_turn(id, turn_id) -> TurnRecord` (the full record, including `metadata`). Both raise `WrapperError` on 404 and `WrapperUnreachable` on connect errors and timeouts, so the verifier can tell a missing session from an unreachable wrapper.
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
- AC8: submit_turn maps every status: 404 and 410 to Gone, 401 and 403 to ConfigError, 413 and 422 to Rejected, any 5xx to Unavailable [evidence: test:tests/test_wrapper_client.py::test_submit_turn_maps_every_status]
- AC9: a connect error maps to Unavailable and a read timeout or reset after send maps to Ambiguous [evidence: test:tests/test_wrapper_client.py::test_connect_error_unavailable_read_timeout_ambiguous]
- AC10: submit_turn honours send_timeout and other calls do not [evidence: test:tests/test_wrapper_client.py::test_send_timeout_applies_to_submit_only]
- AC11: resume_session posts to the resume endpoint with the bearer token [evidence: test:tests/test_wrapper_client.py::test_resume_session_posts_resume]
- AC12: submit_turn sends metadata, and get_turn and list_turns parse the turn record with its metadata, a 404 raises WrapperError and a connect error raises WrapperUnreachable [evidence: test:tests/test_wrapper_client.py::test_turn_metadata_and_turn_records]

## Files

- `src/agent_orchestrator/wrapper/__init__.py`
- `src/agent_orchestrator/wrapper/client.py`
- `src/agent_orchestrator/wrapper/sse.py`
- `src/agent_orchestrator/wrapper/models.py`
- `tests/test_wrapper_client.py`

## Interfaces

- `agent_orchestrator.wrapper.client:WrapperClient` (contract `wrapper-client`)
- `agent_orchestrator.wrapper.models`: `Snapshot`, `Context`, `Envelope`, `PeersView`, `TurnAccepted`, `Busy`, `Gone`, `ConfigError`, `Rejected`, `Unavailable`, `Ambiguous`, `TurnSummary`, `TurnRecord`, `WrapperError`, `WrapperUnreachable`
- `agent_orchestrator.wrapper.sse:SSEParser`

## Expected outcome

Every later process talks to wrappers through one client whose behaviour is pinned by unit tests.

## Steps

- Write tests/test_wrapper_client.py with the twelve named tests using `httpx.MockTransport`; run it; expect failures.
- Implement models.py, sse.py and client.py.
- Rerun `uv run pytest tests/test_wrapper_client.py -q`; expect `12 passed`; run `mise run lint`.

## Notes

Field names follow the wrapper README as changed by epic claude-code-wrapper-orchestr (contracts wrapper-idle-since, wrapper-context-surface, wrapper-user-message-event, wrapper-peers-view); read that README section before coding the models. Envelope is `{seq, ts, session_id, type, data}` with SSE `id` = seq (brief-wrapper section 1).
