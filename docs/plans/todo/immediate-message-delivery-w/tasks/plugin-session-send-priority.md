---
title: plugin session send priority
status: todo
repo: any-mcp-tatara-plugins
value: a superleader can ask for immediate or wait-until-idle delivery and knows what each does
files: [orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py, orchestration/orchestrator/tests/test_orchestrator_plugin.py, orchestration/orchestrator/README.md]
verify: "uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py && mise run lint"
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

# plugin session send priority

## Requirement

Goal G2 (README), verbatim: "each message carries a priority, immediate (the default) or idle (wait until the leader is idle, today's behaviour), settable from the web composer, the orchestrator messages API, the superleader's session_send tool and the ccw peer send_message tool."

Design D15, verbatim: "any-mcp-tatara-plugins `session_send` gains `priority` (enum `immediate`, `idle`, default `immediate`) and its description says: a message to a busy leader joins its running turn at once and shares that turn's answer; `idle` waits until the leader is idle. The `chat_send` description's "chat-started turn" rule extends to a turn a chat message joined. Released as plugins 0.5.0 on top of hive-decoupling's 0.4.0; the orchestrator pins it."

Scope (any-mcp-tatara-plugins): `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py` (`session_send` schema and description, `chat_send` description), `orchestration/orchestrator/tests/test_orchestrator_plugin.py`, `orchestration/orchestrator/README.md` (tool table).

## Acceptance conditions

- ac1: the session_send input schema has priority, a string enum of immediate and idle, not required, and a call with priority idle posts it in the body to /sessions/{slug}/messages (new) [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_session_send_priority]
- ac2: the session_send description says a message to a busy leader joins its running turn at once and shares its answer, and that idle waits until the leader is idle; the slash command sentence stays (updated) [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_descriptions_from_config]
- ac3: the chat_send description counts a turn a chat message joined as chat-started (updated) [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_descriptions]
- ac4: the plugin README's tool table names the priority parameter [evidence: command:grep -q 'priority' orchestration/orchestrator/README.md]
- ac5: the plugin tests and lint pass [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py && mise run lint]

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
