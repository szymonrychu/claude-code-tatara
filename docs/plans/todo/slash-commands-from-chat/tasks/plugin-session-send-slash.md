---
title: plugin session send slash
status: todo
repo: any-mcp-tatara-plugins
value: "a superleader agent's tool description says slash text runs as a command on the target session"
files: [orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py, orchestration/orchestrator/tests/test_orchestrator_plugin.py]
verify: "uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 656326
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# plugin session send slash

## Requirement

Goal G2 (README), verbatim: "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text."

Design D13, verbatim: "any-mcp-tatara-plugins `orchestration/orchestrator` `_descriptions()["session_send"]` adds: "Text that starts with / runs as a Claude Code slash command on the target session's leader (not framed); commands that end or replace a session, such as /exit or /clear, are refused." It names no full list (D5 keeps the list in one place)."

Scope (any-mcp-tatara-plugins): `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py` (`_descriptions` session_send text), `orchestration/orchestrator/tests/test_orchestrator_plugin.py` (`test_descriptions_from_config` asserts the new sentence).

## Acceptance conditions

- ac1: the session_send description says slash text runs as a command on the target's leader and that session-ending commands are refused, and names no full deny list (updated) [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_descriptions_from_config]
- ac2: the plugin tests and lint pass [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`

## Interfaces

- `orchestrator_session_send` tool description text (no schema change).

## Expected outcome

A superleader agent reading its tool list knows that "/x" sent to another session runs as a command there.

## Steps

- Red: add the assertions to `test_descriptions_from_config`; run it: fails.
- Green: change the description; run the task's verify: passes. Quote the summary line.

## Notes

- The description reaches agents only through a plugins release and the orchestrator's `ORCH_ANY_MCP_PLUGINS_REF` pin (`v0.1.0` today); that release and pin are an open question of design.md, not part of this task.
- No dependency inside the epic.
