---
title: orch plugins dev dependency
status: done
repo: agents-orchestrator
value: orchestrator tests exercise the released plugins-repo orchestrator plugin
files: [pyproject.toml, uv.lock, tests/test_on_start.py, tests/test_agent_scale.py, tests/test_agent_init_scripts.py, tests/test_agent_session_messaging.py]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_on_start.py tests/test_agent_scale.py tests/test_agent_init_scripts.py tests/test_agent_session_messaging.py tests/test_images.py && mise run lint"
depends_on: [plugins-orchestration-plugin]
model: opus
review: ""
verified_head: 77e270ecec6cedbc4e71fe0b44df0e3b7e1abd88
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: 2
actual_minutes: 3
actual_tokens: 569303
actual_roles: "impl 3, review 1"
actual_role_tokens: "impl 479430, review 89873"
---

# orch plugins dev dependency

## Requirement

Goal G4 (epic README), verbatim: "agents-orchestrator renders the orchestrator plugin from the plugins repo at a pinned ref and accepts a list of extra plugin sources per preset and session, installed in agent pods." Orchestrator design call, verbatim: "test imports of OrchestratorPlugin move to the plugins package (dev dependency)." Design D9, verbatim: "The dev group gains `any-mcp-tatara-orchestrator @ git+<plugins repo>@<plugins tag>#subdirectory=orchestration/orchestrator`; every test import of `any_mcp.orchestrator` moves to `any_mcp_tatara_orchestrator`."

Needs a merged upstream: any-mcp-tatara-plugins tag `v0.1.0` (design Rollout R2). Do not start before `git ls-remote https://github.com/szymonrychu/any-mcp-tatara-plugins refs/tags/v0.1.0` prints a sha.

Scope (agents-orchestrator, base: the merged state of epic cross-session-messaging-and, any-mcp still pinned at v0.4.0):
- `pyproject.toml` dev group: `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.1.0#subdirectory=orchestration/orchestrator`; `uv.lock` refreshed (`uv lock`).
- `tests/test_on_start.py`, `tests/test_agent_scale.py`, `tests/test_agent_init_scripts.py`, `tests/test_agent_session_messaging.py`: `from any_mcp.orchestrator import OrchestratorPlugin` becomes `from any_mcp_tatara_orchestrator import OrchestratorPlugin`; nothing else changes in them (the rendered `plugin` string in test_on_start.py stays until task orch-render-plugin-sources).

## Acceptance conditions

- ac1: no test imports any_mcp.orchestrator and the four modules import OrchestratorPlugin from any_mcp_tatara_orchestrator [evidence: command:! grep -rnE 'from any_mcp\.orchestrator|import any_mcp\.orchestrator' tests && test "$(grep -rl 'from any_mcp_tatara_orchestrator import OrchestratorPlugin' tests | wc -l | tr -d ' ')" -eq 4]
- ac2: the dev group pins the plugin package to the plugins repo tag v0.1.0 and uv.lock carries it [evidence: command:grep -qF 'any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.1.0#subdirectory=orchestration/orchestrator' pyproject.toml && grep -qF 'name = "any-mcp-tatara-orchestrator"' uv.lock]
- ac3: the init scripts plugin parity test passes through the plugins-repo package [evidence: test:tests/test_agent_init_scripts.py::test_plugin_parity]
- ac4: the session tools parity test passes through the plugins-repo package [evidence: test:tests/test_agent_session_messaging.py::test_session_tools_parity]
- ac5: the four moved modules and the images test pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_on_start.py tests/test_agent_scale.py tests/test_agent_init_scripts.py tests/test_agent_session_messaging.py tests/test_images.py]
- ac6: lint passes [evidence: command:mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `tests/test_on_start.py`
- `tests/test_agent_scale.py`
- `tests/test_agent_init_scripts.py`
- `tests/test_agent_session_messaging.py`

## Interfaces

- `pyproject.toml` `[dependency-groups].dev`: `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.1.0#subdirectory=orchestration/orchestrator`.
- Test import: `from any_mcp_tatara_orchestrator import OrchestratorPlugin`.

## Expected outcome

The orchestrator test suite drives the released plugins-repo plugin, so any-mcp can move to v0.5.0 (which has no `any_mcp.orchestrator`) without breaking a test.

## Steps

- Red: change the four imports; run the task's verify: fails with ModuleNotFoundError.
- Green: add the dev dependency, `uv lock`, `uv sync`; run the task's verify: passes.

## Notes

- any-mcp stays at v0.4.0 here; both modules coexist because the plugin package declares `any-mcp` unversioned.
- Leave the rendered `plugin: any_mcp.orchestrator:OrchestratorPlugin` strings in test_on_start.py alone; task orch-render-plugin-sources changes them with on_start.py.
- Orchestrator tests need Docker (testcontainers; check the Docker VM disk first) and run with `VIRTUAL_ENV` unset; if pytest fails with import errors from a stale `.venv` shebang, recreate it with `uv sync`.

- 2026-10-27 done
