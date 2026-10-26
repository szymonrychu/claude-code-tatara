---
title: Allow the init-scripts tools agents are told to use
status: todo
repo: agents-orchestrator
value: "Agents can actually call orchestrator_init_scripts_get/edit, which the init Job tells them to use"
files: [src/agents_orchestrator/k8s/on_start.py, tests/test_on_start.py, README.md]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q -o addopts=\"\" tests/test_on_start.py tests/test_render.py && mise run lint"
depends_on: [orch-render-session-tools]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 553016
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Allow the init-scripts tools agents are told to use

## Requirement

Discovered during orch-render-session-tools (2026-10-27): the init Job's README text in src/agents_orchestrator/reconciler/init.py:97 tells agents that "the orchestrator_init_scripts_edit tool" applies edits to the next session, and any-mcp v0.4.0's orchestrator plugin defines init_scripts_get and init_scripts_edit (GET/PUT /init-scripts on the agent API), but orchestrator_allow in src/agents_orchestrator/k8s/on_start.py never allows them, so no agent can call them. Add init_scripts_get and init_scripts_edit to the allow list of every session that gets the orchestrator any-mcp entry (alone and hive), in a fixed position after the session tools, keeping each list's existing order. If the agent API's /init-scripts routes are restricted (for example to the leader), the tools are still listed and the server's refusal stands; do not change the routes. Update the README section that lists the rendered orchestrator tools.

## Acceptance conditions

- ac1: an alone session's orchestrator entry allows exactly sessions_list, session_send, init_scripts_get, init_scripts_edit in that order [evidence: test:tests/test_on_start.py::test_alone_session_tools_entry]
- ac2: a hive session's allow list ends with sessions_list, session_send, init_scripts_get, init_scripts_edit after the hive (and scale, when scalable) tools [evidence: test:tests/test_on_start.py::test_hive_session_tools]
- ac3: every tool name the orchestrator renders or names to agents (including the init Job text) is offered by the pinned any-mcp orchestrator plugin [evidence: test:tests/test_on_start.py::test_allowed_tools_exist_in_plugin]
- ac4: on_start, render, init and nomenclature tests and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q -o addopts="" tests/test_on_start.py tests/test_render.py tests/test_agent_init_scripts.py tests/test_nomenclature.py && mise run lint]

## Files

- `src/agents_orchestrator/k8s/on_start.py`
- `tests/test_on_start.py`
- `README.md`

## Interfaces

- `src/agents_orchestrator/k8s/on_start.py:orchestrator_allow(spec) -> list[str]` gains the two init-scripts tools (a module constant next to SESSION_TOOLS).
- any-mcp v0.4.0 plugin tool names: init_scripts_get, init_scripts_edit (code/any-mcp/src/any_mcp/orchestrator.py).

## Expected outcome

Every session's orchestrator entry allows the init-scripts tools, and a test ties every allowed or advertised tool name to the pinned plugin, so the init Job's advice works.

## Steps

- Red: extend test_alone_session_tools_entry and test_hive_session_tools and add test_allowed_tools_exist_in_plugin; run the task's verify; expect failures on the missing names.
- Green: add the constant and append it in orchestrator_allow; update README; run the task's verify and the ac4 command on the committed HEAD.

## Notes

- Discovered by the orch-render-session-tools implementer; verified by the orchestrator: reconciler/init.py:97 names orchestrator_init_scripts_edit, on_start.py HIVE_TOOLS/SESSION_TOOLS omit it.
- test_allowed_tools_exist_in_plugin can load the plugin from the installed any-mcp (dev dependency) as test_plugin_parity does.
- tests/test_nomenclature.py checks tracked files: run it after committing; avoid the word cluster.

- 2026-10-26 amended: ac4 named a nonexistent test file; the init-scripts tests are tests/test_agent_init_scripts.py
