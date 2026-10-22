# claude-code-wrapper orchestrator support design

## Summary

claude-code-wrapper gets six additive changes so agent-orchestrator can drive it headlessly: `idle_since`, a `user_message` event, backward history paging with a type filter, `GET /v1/peers`, a statusline relay and a `context` snapshot field plus SSE event. They land in the wrapper itself (user decision), each with README.md updates enforced by test_readme_api. Source design: section 4 of the orchestrator design (scratchpad orch/design-orchestrator.md).

## Intent and why

The orchestrator routes to the agent idle the longest, draws a 0-100 context gauge, scrolls chat history backwards and shows the peer mesh. The wrapper exposes none of these (brief-wrapper.md section 6). Fixing them in the wrapper avoids a second, drifting copy of model-window tables in the orchestrator.

## Goals

- Snapshot has `idle_since`; `session_state.data` has `since`.
- `user_message {turn_id, origin, text, files}` is emitted when a prompt is pasted, for every origin.
- `GET .../history?before_seq=&limit=&types=` pages backwards with `prev_seq` and `has_more_before`.
- `GET /v1/peers` returns the mesh view or `{enabled: false}`.
- `ccw statusline` relays Claude Code statusline JSON to `POST /internal/statusline` and chains the user's statusLine.
- Snapshot `context` and SSE `context` event carry used_tokens, window_tokens, used_percentage, model, source, updated_at.

## Non-goals

- No orchestrator logic in the wrapper; no breaking change to routes or events; no model-window table in the wrapper.
- No subagent transcript endpoint, no per-session mcp_servers (other gaps in the brief).

## Anti-goals

- Running the full 11-minute suite per task.
- Undocumented routes, events or keys (the README tests fail).
- Diverging from the concurrently developed origin/main (session claude-code-wrapper-58).

## Constraints

- Python 3.12, FastAPI, uv; lint is `uv run ruff check . && uv run ruff format --check .`, which is exactly `mise run lint` (mise.toml: ruff check + ruff format --check only, not the full suite; `mise run test` is the 11-minute suite).
- README.md is the spec and is test-enforced (tests/test_readme_api.py).
- Task verify is targeted: the task's test file plus tests/test_readme_api.py plus lint.
- Branch must be rebased on origin/main before the PR.

## Decisions

### D1: idle_since in the snapshot (approval A1)
Snapshot `idle_since` (ISO, null unless idle) and `session_state.data.since`. Alternative: orchestrator tracks turn_completed itself; rejected, it loses state across reconnects.

### D2: user_message event (approval A2)
New event emitted at paste time with origin client|initial|agent|peer (turns.py:27) plus restart|command, command with turn_id null. `turn_started.text` kept. Alternative: derive from transcript; rejected, not available per brief.

### D3: backward history (approval A3)
`before_seq`, `types` (validated against EVENT_TYPES), `prev_seq` (null when no more), `has_more_before`; 400 combined with after_seq. The orchestrator stores events itself but the user decided it ships for other headless clients.

### D4: GET /v1/peers (approval A4)
Bearer-authenticated mesh view, never exposes peers.token; `{enabled:false}` when peers are off.

### D5: statusline relay (approval A5)
`ccw statusline` posts stdin to `/internal/statusline` and runs the chained user statusLine. Alternative: `/context` command (makes the session busy, screen text); rejected.

### D6: context surface (approval A6)
used_tokens = input + cache_creation + cache_read of statusline current_usage, model = statusline model.id, used_percentage computed when null but inputs known. `context` and `user_message` ride the normal ring and rotation (my call); restart-continue emits user_message origin restart (my call).
Snapshot `context` and a deduped `context` event; null until the first assistant message and reset on compact. No model-window table in the wrapper (the statusline provides the denominator).

### D7: delivery conventions (approval A7)
Fixed in the wrapper itself; targeted verify per task; README note to rebase onto origin/main before the PR. Chain order W1 -> W2 -> W3 -> W5 -> W6 because tasks share events.py and router.py; W4 is independent. (my call: the chain order)

### D8: onStart instance hook
An onStart instance hook fires once per ccw process start, after the global mise install and before peer join, resume_on_start or any session create, so agent-orchestrator can install any-mcp per pod before claude spawns MCP servers; a blocking deny or an on_error deny failure exits non-zero (gap found at the agent-orchestrator gate: onCreate runs after claude starts, setup_commands run per created session only) (user decision)

## Research

| Lens | Status | Adopted | Rejected |
|---|---|---|---|
| wrapper code | ran (brief-wrapper.md) | snapshot at manager.py:1429, events.py page(), router _last_context | /context command for gauge |
| docs | ran (brief-docs.md section 5) | statusline context_window.* fields (code.claude.com/docs/en/statusline) | model-window table |
| ui, infra, anymcp | skipped, other epics | | |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| brief-wrapper.md section 6 | no idle-since field | idle-since-in-snapshot |
| brief-wrapper.md section 6 | no user-message event | user-message-event |
| brief-wrapper.md section 2 | forward-only history | history-before-seq-and-types |
| brief-wrapper.md section 6 | no GET for peer membership | peer-mesh-view-route |
| brief-docs.md section 5 | statusline context_window JSON | statusline-relay, context-in-snapshot-and-sse |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 idle_since | idle-since-in-snapshot |
| D2 user_message | user-message-event |
| D3 backward history | history-before-seq-and-types |
| D4 peers view | peer-mesh-view-route |
| D5 statusline relay | statusline-relay |
| D6 context surface | context-in-snapshot-and-sse |
| D7 delivery conventions | idle-since-in-snapshot, user-message-event, history-before-seq-and-types, peer-mesh-view-route, statusline-relay, context-in-snapshot-and-sse |
| D8 onStart instance hook | on-start-instance-hook |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `wrapper-idle-since` | idle-since-in-snapshot | none | `code/claude-code-wrapper/README.md` (consumed by the agent-orchestrator epic) |
| `wrapper-user-message-event` | user-message-event | none | `code/claude-code-wrapper/README.md` (consumed by the agent-orchestrator epic) |
| `wrapper-history-backward` | history-before-seq-and-types | none | `code/claude-code-wrapper/README.md` (consumed by the agent-orchestrator epic) |
| `wrapper-peers-view` | peer-mesh-view-route | none | `code/claude-code-wrapper/README.md` (consumed by the agent-orchestrator epic) |
| `wrapper-statusline-callback` | statusline-relay | context-in-snapshot-and-sse | `code/claude-code-wrapper/src/claude_code_wrapper/router.py` |
| `wrapper-context-surface` | context-in-snapshot-and-sse | none | `code/claude-code-wrapper/README.md` (consumed by the agent-orchestrator epic) |
| `wrapper-on-start-hook` | on-start-instance-hook | none | `code/claude-code-wrapper/README.md` (consumed by the agent-orchestrator epic) |

## Review focus

- Event dedupe and reset on compact (context-in-snapshot-and-sse).
- The statusline chain never failing the user's statusline (statusline-relay).
- events.py shared by three tasks: EVENT_TYPES additions must keep tests/test_readme_api.py green.

## Left to the builder

Exact internal payload validation for `/internal/statusline`, and the chain-config file location, within the existing hook relay conventions.

## Assumptions and unknowns

- The Claude Code statusLine stdin JSON has `context_window.{used_percentage,context_window_size,current_usage}` (code.claude.com/docs/en/statusline); confirm with a fake-claude fixture in tests.
- Pod-shared sessions_root listing other pods' sessions is an orchestrator/deploy concern, not handled here.

## Open questions

none

## Irreversible operations in scope

none
