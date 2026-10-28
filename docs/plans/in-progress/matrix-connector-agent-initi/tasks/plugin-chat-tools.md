---
title: plugin chat tools
status: in-progress
repo: any-mcp-tatara-plugins
value: "agents get the four chat tools: rooms, send, react and status"
files: [orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py, orchestration/orchestrator/tests/test_orchestrator_plugin.py, orchestration/orchestrator/README.md]
verify: "uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py && mise run lint"
depends_on: [orch-chat-relay]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 941421
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# plugin chat tools

## Requirement

README Goals, verbatim:
- "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."
- "An agent can reply to a specific chat message (quoted reply) and react to a message with an emoji."
- "An agent can list the rooms it may post to and read the delivery status of what it sent."

Design D13, verbatim: "The orchestrator plugin gains `chat_rooms`, `chat_send`, `chat_react`, `chat_status` (HttpBinding tools, existing `on_error` mapping); descriptions say the final answer reaches the chat only for chat-started turns, sends are asynchronous and return `s<n>`, `reply_to`/`to` take `m<n>`/`s<n>`, leader only, status via `orchestrator_chat_status`, and the 1:1 binding (D9): a session talks in at most one chat room, its bound room, and starts a chat only in an unbound flagged room while it is bound to none (`room_bound`, `session_bound` otherwise)."

User decision (final gate, 2026-10-27), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go". Design D2, verbatim: "the binding refusals of D4 (b) are 409 `room_bound` and 409 `session_bound`."

Design D2, verbatim (the routes the tools call): "`GET /agent/v1/chat/rooms` [...] `POST /agent/v1/chat/messages` body `{text, room?, reply_to?}` [...] `POST /agent/v1/chat/reactions` body `{to, key}` [...] `GET /agent/v1/chat/messages/{id}`".

Architecture risk, verbatim: "Double output: the agent calls send during a chat-started turn and its final answer is posted too. Mitigation: PREAMBLE and tool description".

Scope (any-mcp-tatara-plugins, `orchestration/orchestrator`): four `spec(...)` entries and descriptions in `any_mcp_tatara_orchestrator/__init__.py`, the plugin docstring, the plugin README's tool list. `tests/test_orchestrator_plugin.py::test_lists_eleven_tools` is no longer accurate (named): it pins eleven tools; it becomes `test_lists_fifteen_tools` pinning the fifteen names. No version bump here (plugins-release-0-3-0).

## Acceptance conditions

- ac1: the plugin lists fifteen tools, the eleven existing ones plus chat_rooms, chat_send, chat_react and chat_status (updated) [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_lists_fifteen_tools]
- ac2: chat_rooms calls GET /agent/v1/chat/rooms, chat_send POST /agent/v1/chat/messages with {text, room?, reply_to?}, chat_react POST /agent/v1/chat/reactions with {to, key}, chat_status GET /agent/v1/chat/messages/{id}, each with the session credentials [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_tools_call_agent_routes]
- ac3: upstream refusals (room_not_allowed, room_not_authorised, room_bound, session_bound, bad_reference, rate_limited, not_leader, chat_unavailable) surface their code and status, the token redacted [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_errors_surface_code]
- ac4: the chat_send description says the final answer reaches the chat only for chat-started turns, that sends are asynchronous and return s<n>, that reply_to takes m<n> or s<n>, that only the leader may send, and that a session talks in at most one chat room (its bound room) and starts a chat only in an unbound flagged room while bound to none; chat_rooms, chat_react and chat_status descriptions name the binding rule or their references [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_descriptions]
- ac5: the plugin README lists the four chat tools and the one-room-per-session rule [evidence: command:grep -q orchestrator_chat_send orchestration/orchestrator/README.md && grep -q orchestrator_chat_status orchestration/orchestrator/README.md && grep -qi "one room" orchestration/orchestrator/README.md]
- ac6: the targeted tests and lint pass [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py && mise run lint]

## Files

- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`
- `orchestration/orchestrator/README.md`

## Interfaces

- Tools (namespace `orchestrator`, so agents see `orchestrator_chat_*`): `chat_rooms {}`; `chat_send {text: string, room?: string, reply_to?: string}`; `chat_react {to: string, key: string}`; `chat_status {id: string}`; all `additionalProperties: false`.

## Expected outcome

The orchestrator plugin offers the four chat tools against the orchestrator's chat routes, ready to release.

## Steps

- Red: rename and update `test_lists_eleven_tools`, add the three chat tests; run `uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py`: they fail.
- Green: the four specs and descriptions, README; run the task's verify: passes. Quote the summary line with counts.

## Notes

- Follow `test_session_tools_call_agent_routes` and `test_scale_and_init_tools_match_contracts` for the route assertions.
- Optional body fields that the agent omits must not be sent as null if the binding would send them; the connector rejects unknown fields, not nulls, so either is accepted, but keep it consistent with `session_send`.
- Depends on orch-chat-relay only for the agreed paths; nothing here imports the orchestrator.

- 2026-10-27 amended: final gate 2026-10-27: hard 1:1 room-session binding replaces last-speaker routing (D9): descriptions and binding refusal codes
