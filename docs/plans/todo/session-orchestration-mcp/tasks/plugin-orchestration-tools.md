---
title: plugin orchestration tools
status: todo
repo: any-mcp-tatara-plugins
value: "flagged sessions get sixteen tools for presets, sessions, schedules and the audit"
files: [orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py, orchestration/orchestrator/tests/test_orchestrator_plugin.py, orchestration/orchestrator/README.md]
verify: "uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py && mise run lint"
depends_on: [orch-schedule-relay]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# plugin orchestration tools

## Requirement

README Goal G1, verbatim: "A session the user flagged `session_orchestration` (a per-preset or per-spec switch, off by default, set only by the user through agents-web or the public API) has orchestrator MCP tools to list, create, edit and delete presets, list, create, scale and delete sessions, and list, create, edit, delete and run cron schedules, on the user's request; only its leader may call them, and no unflagged session gets the tools."

Design D11, verbatim: "Plugin tools (prefix `orchestrator_`, leader-only, rendered only when flagged): presets `presets_list`, `preset_get`, `preset_create`, `preset_update`, `preset_delete`; sessions `sessions_overview`, `session_create`, `session_scale`, `session_delete`; schedules `schedules_list`, `schedule_create`, `schedule_update`, `schedule_delete`, `schedule_run`, `schedule_runs`; audit `orchestration_actions`."

Design D3, verbatim: "Tool descriptions require the agent to name the target to the user before deleting."

Architect reuse, verbatim: "`OrchestratorPlugin.on_error`."

Scope (any-mcp-tatara-plugins): `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py` (sixteen `ToolSpec`s bound to `/agent/v1/orchestration/*`, their descriptions), `orchestration/orchestrator/tests/test_orchestrator_plugin.py`, `orchestration/orchestrator/README.md`.

Test no longer accurate (named): the plugin's tool-count test (`test_lists_<n>_tools` as hive-decoupling leaves it; `test_lists_eleven_tools` today, fifteen after Matrix) counts the tools without the new sixteen; it is renamed to the new count and asserts the full list.

## Acceptance conditions

- ac1: the plugin lists the tools hive-decoupling left plus the sixteen orchestration tools, the count test renamed to the new total (updated) [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_lists_orchestration_tools]
- ac2: each orchestration tool calls its /agent/v1/orchestration route with the D11 method, path and body and the session credentials [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_orchestration_tools_call_agent_routes]
- ac3: the refusals not_orchestrator, not_leader, not_user_turn, not_owner, not_found, privilege_escalation, self_delete, protected_target, session_deleting, owned_limit, rate_limited, too_frequent, payload_too_large, schedules_unconfigured and schedules_unavailable surface their code and status with the token redacted [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_orchestration_errors_surface_code]
- ac4: the descriptions say writes are only for the user's own request in a turn the user started, changes are limited to objects this session created, the delete tools require naming the target to the user before deleting, and preset reads mask other presets' secrets [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_orchestration_descriptions]
- ac5: the plugin README lists the sixteen tools and says they render only for sessions flagged session_orchestration [evidence: command:grep -q orchestrator_session_delete orchestration/orchestrator/README.md && grep -q session_orchestration orchestration/orchestrator/README.md]
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
