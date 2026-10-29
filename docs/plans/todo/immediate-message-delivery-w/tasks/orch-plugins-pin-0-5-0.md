---
title: orch plugins pin 0.7.0
status: todo
repo: agents-orchestrator
value: superleaders can choose immediate or idle delivery from their session_send tool
files: [src/agents_orchestrator/settings.py, pyproject.toml, uv.lock, README.md, tests/test_settings.py]
verify: "uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint"
depends_on: [plugins-release-0-5-0, orch-wrapper-pin-0-5-0]
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

# orch plugins pin 0.7.0

## Requirement

Design D15, verbatim: "Released as plugins 0.7.0 on top of session-orchestration-mcp's 0.7.0; the orchestrator pins it."

Design D19, verbatim: "The orchestrator pins the wrapper merge commit of v0.5.0 [...] then the plugins ref v0.7.0".

Scope (agents-orchestrator): `src/agents_orchestrator/settings.py` (`ORCH_ANY_MCP_PLUGINS_REF` default v0.7.0 from session-orchestration-mcp, the live baseline, to v0.7.0), `pyproject.toml` and `uv.lock` (the `any-mcp-tatara-orchestrator` dev dependency), `README.md` (settings table), `tests/test_settings.py` (the default pin, no longer accurate after the bump).

## Acceptance conditions

- ac1: the settings default is v0.7.0 (updated, named) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the README documents the v0.7.0 default and names no older plugins tag [evidence: command:grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.7.0` |' README.md && test "$(grep -oE 'plugins release tag \(`v[0-9.]+`\)' README.md | grep -vc 'v0.7.0')" = 0]
- ac4: the pinned orchestrator plugin's session_send schema carries priority [evidence: command:grep -rq '"priority"' "$(uv run --frozen python -c 'import os, any_mcp_tatara_orchestrator as m; print(os.path.dirname(m.__file__))')"]
- ac5: settings, images and on-start suites and lint pass [evidence: command:uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint]

## Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `tests/test_settings.py`

## Interfaces

- `settings.Settings.any_mcp_plugins_ref` default `"v0.7.0"`; dev dependency `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.7.0#subdirectory=orchestration/orchestrator` (the existing form).

## Expected outcome

Superleaders get the session_send tool that offers immediate or idle delivery.

## Steps

- Read `settings.py`, `pyproject.toml`, the README settings table, `tests/test_settings.py`, `tests/test_images.py` and hive-decoupling's orch-plugins-pin-0-4-0 task in one pass.
- Version pin bump with no behaviour change (TDD exception): update `tests/test_settings.py::test_defaults` (no longer accurate), the default, `uv lock`, README.
- Run the task's verify; expect all passed. Quote the summary line.

## Notes

- Id kept from an earlier numbering; it pins v0.7.0.
- Depends on the plugins v0.7.0 tag on origin (plugins-release-0-5-0 ac3, pushed by the orchestrator session).
- The helmfile value of `ORCH_ANY_MCP_PLUGINS_REF` stays with the gate's deploy decision (Q9).
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR; the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: plugins pin renumbered v0.6.0 -> v0.7.0 (mx-34 #469/#470): the baseline pin is session-orchestration-mcp's v0.6.0
