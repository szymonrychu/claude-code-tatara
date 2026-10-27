---
title: plugin session send slash
status: in-progress
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

Design D13, verbatim: "any-mcp-tatara-plugins `orchestration/orchestrator` `_descriptions()["session_send"]` adds: "When your session is a superleader, text that starts with a slash command such as /compact runs as a Claude Code slash command on the target session's leader (not framed); commands that end or replace a session, such as /exit or /clear, are refused. From any other session it is delivered as a message." (my call, matching D1 after interrogate item 1). It names no full list (D5 keeps the list in one place)."

Interrogate item 1 (interrogate.md), verbatim (why the sentence names the superleader): "Store `kind='command'` only when the sender's session has `session_messaging`; otherwise the text stays a framed turn."

Scope (any-mcp-tatara-plugins): `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py` (`_descriptions` session_send text), `orchestration/orchestrator/tests/test_orchestrator_plugin.py` (`test_descriptions_from_config` asserts the new sentence). The release of this change is task plugins-release-0-2-0.

## Acceptance conditions

- ac1: the session_send description says a superleader's slash text runs as a Claude Code slash command on the target's leader, that session-ending commands are refused and that from other sessions it is a message, and names no full deny list (updated) [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_descriptions_from_config]
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

- The description reaches agents only through a plugins release and the orchestrator's `ORCH_ANY_MCP_PLUGINS_REF` pin (`v0.1.0` today): tasks plugins-release-0-2-0 and orch-plugins-pin-0-2-0 (builder check).
- No dependency inside the epic.

- 2026-10-27 amended: interrogate item 1 (the description says only a superleader's slash text runs as a command), design D13 revised
