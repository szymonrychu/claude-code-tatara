---
title: plugin session send priority
status: todo
repo: any-mcp-tatara-plugins
value: a superleader can ask for immediate or wait-until-idle delivery and knows what each does
files: [orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py, orchestration/orchestrator/tests/test_orchestrator_plugin.py, orchestration/orchestrator/README.md]
verify: "uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py && mise run lint"
depends_on: [wrapper-midturn-probe]
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

- `spec("session_send", "POST", "/sessions/{slug}/messages", _schema({"slug": ..., "text": ..., "priority": {"type": "string", "enum": ["immediate", "idle"], "description": ...}}, ["slug", "text"]), "*")`.
- `_descriptions()["session_send"]` and `["chat_send"]`: wording within D15; the existing slash-command sentence of the slash epic stays.

## Expected outcome

A superleader sees that its messages reach a busy leader at once by default, can ask for idle delivery, and knows a chat message that joined a turn makes that turn's answer reach the chat.

## Steps

- Read the plugin `__init__.py` (`_descriptions`, the tool specs), `tests/test_orchestrator_plugin.py` and the plugin README in one pass.
- Red: add `test_session_send_priority` and extend the two description tests; run `uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py`; expect them to fail.
- Green: change the schema and descriptions, README; run the task's verify; expect all passed. Quote the summary line.

## Notes

- `test_lists_fifteen_tools` (or the count the hive-decoupling epic left) must stay accurate: no new tool here.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: depends_on wrapper-midturn-probe so the probe gates every root task (interrogate 6; frontmatter edited directly, amend cannot change it)
