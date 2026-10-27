---
title: plugin chat tools
status: todo
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

Design D13, verbatim: "The orchestrator plugin gains `chat_rooms`, `chat_send`, `chat_react`, `chat_status` (HttpBinding tools, existing `on_error` mapping); descriptions say the final answer reaches the chat only for chat-started turns, sends are asynchronous and return `s<n>`, `reply_to`/`to` take `m<n>`/`s<n>`, leader only, and status via `orchestrator_chat_status`."

Design D2, verbatim (the routes the tools call): "`GET /agent/v1/chat/rooms` [...] `POST /agent/v1/chat/messages` body `{text, room?, reply_to?}` [...] `POST /agent/v1/chat/reactions` body `{to, key}` [...] `GET /agent/v1/chat/messages/{id}`".

Architecture risk, verbatim: "Double output: the agent calls send during a chat-started turn and its final answer is posted too. Mitigation: PREAMBLE and tool description".

Scope (any-mcp-tatara-plugins, `orchestration/orchestrator`): four `spec(...)` entries and descriptions in `any_mcp_tatara_orchestrator/__init__.py`, the plugin docstring, the plugin README's tool list. `tests/test_orchestrator_plugin.py::test_lists_eleven_tools` is no longer accurate (named): it pins eleven tools; it becomes `test_lists_fifteen_tools` pinning the fifteen names. No version bump here (plugins-release-0-3-0).

## Acceptance conditions

- ac1: the plugin lists fifteen tools, the eleven existing ones plus chat_rooms, chat_send, chat_react and chat_status (updated) [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_lists_fifteen_tools]
- ac2: chat_rooms calls GET /agent/v1/chat/rooms, chat_send POST /agent/v1/chat/messages with {text, room?, reply_to?}, chat_react POST /agent/v1/chat/reactions with {to, key}, chat_status GET /agent/v1/chat/messages/{id}, each with the session credentials [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_tools_call_agent_routes]
- ac3: upstream refusals (room_not_allowed, room_not_authorised, bad_reference, rate_limited, not_leader, chat_unavailable) surface their code and status, the token redacted [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_errors_surface_code]
- ac4: the chat_send description says the final answer reaches the chat only for chat-started turns, that sends are asynchronous and return s<n>, that reply_to takes m<n> or s<n>, and that only the leader may send; chat_react and chat_status descriptions name their references [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_descriptions]
- ac5: the plugin README lists the four chat tools [evidence: command:grep -q orchestrator_chat_send orchestration/orchestrator/README.md && grep -q orchestrator_chat_status orchestration/orchestrator/README.md]
- ac6: the targeted tests and lint pass [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py && mise run lint]

## Files

- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`
- `orchestration/orchestrator/README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
