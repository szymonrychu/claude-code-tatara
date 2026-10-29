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

Scope (any-mcp-tatara-plugins): `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py` (sixteen `ToolSpec`s bound to `/agent/v1/orchestration/*`, their descriptions), `orchestration/orchestrator/tests/test_orchestrator_plugin.py`, `orchestration/orchestrator/README.md`. No new file: `tests/test_nomenclature.py` pins the plugin to these three files and bans the words matching `cluster|agent[-_]orchestrator` in them, so names, descriptions and README text avoid both. `orchestrator_activity` (the hive digest) and the new `orchestrator_orchestration_actions` (the caller's audit rows) are different tools; their descriptions say which is which.

Test no longer accurate (named): `orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_lists_all_tools` asserts the listed tools equal the `ALL_TOOLS` set, sixteen tools on main at v0.5.1 (`orchestrator_activity` included); `ALL_TOOLS` gains the sixteen orchestration tools, thirty-two in all, and the test is otherwise unchanged. The plugin README line "The plugin always lists all sixteen tools" and its tool table become no longer accurate the same way: thirty-two tools.

User settlement B6 (2026-10-27), verbatim: "the build starts only after all three blockers have merged. The first task reads the real migration number, plugins version and tool counts from main and amends the dependent tasks. No assumed numbers in ACs." The count in this task is the baseline-facts count (16) plus sixteen: 32.

Open question Q9 (pending; the plan follows the recommended answer), verbatim: "A flagged session may create sessions or schedules only from presets it created itself (or from an explicit spec); presets made in the UI, which may hold secrets in env, are refused not_owner, so their secrets never reach a pod the agent controls?" recommended "yes". The descriptions of session_create, schedule_create and schedule_update say so.

## Acceptance conditions

- ac1: ALL_TOOLS holds the sixteen tools main holds plus the sixteen orchestration tools, 32 in all, and the plugin lists exactly that set with hive true and false (updated) [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_lists_all_tools]
- ac2: each orchestration tool calls its /agent/v1/orchestration route with the D11 method, path and body and the session credentials [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_orchestration_tools_call_agent_routes]
- ac3: the refusals not_orchestrator, not_leader, not_user_turn, not_owner, not_found, privilege_escalation, self_delete, protected_target, session_deleting, owned_limit, rate_limited, too_frequent, payload_too_large, schedules_unconfigured and schedules_unavailable surface their code and status with the token redacted [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_orchestration_errors_surface_code]
- ac4: the descriptions say writes are only for the user's own request in a turn the user started, changes are limited to objects this session created, the delete tools require naming the target to the user before deleting, and preset reads mask other presets' secrets, and session_create, schedule_create and schedule_update say a session or schedule may be created only from a preset this session created or from an explicit spec, and the descriptions of orchestrator_activity and orchestrator_orchestration_actions tell the hive digest from the caller's audit rows [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_orchestration_descriptions]
- ac5: the plugin README lists the sixteen orchestration tools, says the plugin lists thirty-two tools, and says the orchestration tools render only for sessions flagged session_orchestration [evidence: command:grep -q orchestrator_session_delete orchestration/orchestrator/README.md && grep -q session_orchestration orchestration/orchestrator/README.md]
- ac6: the three plugin files carry none of the banned words and stay the only tracked plugin files [evidence: test:tests/test_nomenclature.py::test_no_old_nomenclature]
- ac7: the targeted tests and lint pass [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py tests/test_nomenclature.py && mise run lint]

## Files

- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`
- `orchestration/orchestrator/README.md`

## Interfaces

- Tool to route map (prefix `/agent/v1/orchestration`): `presets_list` GET `/presets`; `preset_get` GET `/presets/{id}`; `preset_create` POST `/presets` `{name, spec}`; `preset_update` PUT `/presets/{id}` `{name, spec}`; `preset_delete` DELETE `/presets/{id}`; `sessions_overview` GET `/sessions`; `session_create` POST `/sessions` `{preset_id?, spec?, slug?, prompt?}`; `session_scale` POST `/sessions/{slug}/scale` `{replicas}`; `session_delete` DELETE `/sessions/{slug}`; `schedules_list` GET `/schedules`; `schedule_create` POST `/schedules`; `schedule_update` PUT `/schedules/{id}`; `schedule_delete` DELETE `/schedules/{id}`; `schedule_run` POST `/schedules/{id}/run`; `schedule_runs` GET `/schedules/{id}/runs`; `orchestration_actions` GET `/actions`.
- Read the final paths and bodies from the orchestrator README `### Orchestration` on agents-orchestrator main; the map above is the design's.

## Expected outcome

Agents of flagged sessions get sixteen tools that drive the orchestration routes, with descriptions that keep them on the user's request.

## Steps

- Red: rename and extend the count test, add the three new tests; run `uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py`: fails.
- Green: tool specs, descriptions, README; run the task's verify. Quote the summary line.

## Notes

- Builds on hive-decoupling's and Matrix's `__init__.py` (shared file); read it first.
- The plugin does no I/O at load (`test_no_io_at_load` stays green).

- 2026-10-27 amended: builder check B6 and Q9: counts from baseline-facts, own-preset rule in descriptions

- 2026-10-29 amended: staleness refresh: test_lists_all_tools over ALL_TOOLS (16 to 32), nomenclature test, activity vs actions descriptions
