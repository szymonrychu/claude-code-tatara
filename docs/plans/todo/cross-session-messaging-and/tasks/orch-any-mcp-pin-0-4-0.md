---
title: orch any-mcp pin 0.4.0
status: todo
repo: agents-orchestrator
value: new sessions install the any-mcp release that has the session tools
files: [src/agents_orchestrator/settings.py, pyproject.toml, uv.lock, README.md, tests/test_settings.py, tests/golden/session_single.yaml, tests/golden/session_two_peers.yaml, tests/test_agent_session_messaging.py]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_settings.py tests/test_images.py tests/test_render.py tests/test_agent_init_scripts.py tests/test_agent_session_messaging.py && mise run lint"
depends_on: [anymcp-session-tools, orch-agent-service-accounts, orch-agent-session-messaging]
model: opus
review: ""
verified_head: ""
points: 2
expected_minutes: 6
expected_tokens: 553016
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch any-mcp pin 0.4.0

## Requirement

Goal G5 (epic README), verbatim: "Deployed: new orchestrator, any-mcp and agents-web versions applied through agents-helmfile ...". Design D12: agents-orchestrator pins any-mcp `v0.4.0` in `settings.any_mcp_ref`, `pyproject.toml` and `uv.lock` (README and goldens follow).

Needs a merged upstream: any-mcp task anymcp-session-tools merged to any-mcp main and tag `v0.4.0` pushed with a green release workflow (design Rollout R1). Do not start before `git ls-remote https://github.com/szymonrychu/any-mcp refs/tags/v0.4.0` prints a sha.

Scope (agents-orchestrator):
- `src/agents_orchestrator/settings.py`: `any_mcp_ref: str = "v0.4.0"`.
- `pyproject.toml`: `any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.4.0`; `uv.lock` refreshed (`uv lock`).
- `README.md`: the `ORCH_ANY_MCP_REF` row default and the `## Images` any-mcp sentence name `v0.4.0`; the dated breaking-change note ("Agents need any-mcp `v0.3.0` or later") stays as history.
- `tests/test_settings.py::test_defaults` asserts `any_mcp_ref == "v0.3.0"`: no longer accurate because the pinned release moves to v0.4.0 by design D12; it asserts `"v0.4.0"`.
- `tests/golden/session_single.yaml`, `tests/golden/session_two_peers.yaml`: regenerated with the golden helper of `tests/test_render.py` (the onStart script names the ref).
- `tests/test_agent_session_messaging.py` (from task orch-agent-session-messaging): add `test_session_tools_parity`, driving the installed any-mcp v0.4.0 `OrchestratorPlugin` through `any_mcp.testing.PluginHarness` against the app on the agent port, like `tests/test_agent_init_scripts.py::test_plugin_parity`: the first test of the new tools against the real routes.

## Acceptance conditions

- ac1: the pyproject any-mcp pin, uv.lock and the settings default agree on v0.4.0 [evidence: test:tests/test_images.py::test_pyproject_any_mcp_pin_matches_settings_ref]
- ac2: the default settings pin v0.4.0 [evidence: test:tests/test_settings.py::test_defaults]
- ac3: the two-replica golden renders the v0.4.0 install [evidence: test:tests/test_render.py::test_golden_two_replicas_with_peers]
- ac4: the single golden renders the v0.4.0 install [evidence: test:tests/test_render.py::test_golden_single_without_peers]
- ac5: the plugin parity test passes against any-mcp v0.4.0 [evidence: test:tests/test_agent_init_scripts.py::test_plugin_parity]
- ac5b: through the real any-mcp v0.4.0 plugin, orchestrator sessions_list returns the server's session list and session_send from a plain session's leader to a superleader session queues a message and returns its message_id [evidence: test:tests/test_agent_session_messaging.py::test_session_tools_parity]
- ac6: README names v0.4.0 as the ORCH_ANY_MCP_REF default [evidence: command:grep -q '`ORCH_ANY_MCP_REF` | `v0.4.0`' README.md]
- ac7: the settings, images, render, onStart and README tests pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_settings.py tests/test_images.py tests/test_render.py tests/test_on_start.py tests/test_readme_api.py]
- ac8: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `tests/test_settings.py`
- `tests/golden/session_single.yaml`
- `tests/golden/session_two_peers.yaml`
- `tests/test_agent_session_messaging.py`

## Interfaces

- `settings.py:Settings.any_mcp_ref` default `v0.4.0`; `pyproject.toml` dependency `any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.4.0`.
- After this task `any_mcp.orchestrator.OrchestratorPlugin` in the dev environment has the `sessions_list` and `session_send` tools (used by task orch-render-session-tools's parity test).

## Expected outcome

New sessions install any-mcp v0.4.0, and the orchestrator's dev environment tests against it.

## Steps

- Red: change `tests/test_settings.py::test_defaults` to `v0.4.0`; run `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_settings.py tests/test_images.py`: fails.
- Green: bump settings, pyproject, `uv lock`, regenerate the goldens, README; run the task's verify: passes.
- Run ac5, ac6, ac7 and ac8 commands: pass.

## Notes

- This task is a dependency bump; the only behaviour is the pinned ref, pinned by ac1 to ac4.
- `uv lock` needs network to GitHub; the lock must record `any-mcp?rev=v0.4.0#` (ac1).
- `tests/test_on_start.py::test_plugin_entry_session_key`'s docstring mentions v0.3.0; it validates against whatever any-mcp is installed and stays accurate; do not edit it.
- Orchestrator tests need Docker; run with `VIRTUAL_ENV` unset; `uv sync` after `uv lock`.

- 2026-10-26 amended: gate 2026-10-26: one-sided superleader messaging (tools for every session, target_not_superleader), Q1 no orchestrator kubectl install, Q2 yes
