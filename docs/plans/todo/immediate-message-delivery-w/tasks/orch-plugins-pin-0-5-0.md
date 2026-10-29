---
title: orch plugins pin 0.5.0
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

# orch plugins pin 0.5.0

## Requirement

Design D15, verbatim: "Released as plugins 0.5.0 on top of hive-decoupling's 0.4.0; the orchestrator pins it."

Design D19, verbatim: "The orchestrator pins the wrapper merge commit of v0.5.0 [...] then the plugins ref v0.5.0".

Scope (agents-orchestrator): `src/agents_orchestrator/settings.py` (`ORCH_ANY_MCP_PLUGINS_REF` default v0.4.0 from hive-decoupling to v0.5.0), `pyproject.toml` and `uv.lock` (the `any-mcp-tatara-orchestrator` dev dependency), `README.md` (settings table), `tests/test_settings.py` (the default pin, no longer accurate after the bump).

## Acceptance conditions

- ac1: the settings default is v0.5.0 (updated, named) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the README documents the v0.5.0 default and names no older plugins tag [evidence: command:grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.5.0` |' README.md && test "$(grep -oE 'plugins release tag \(`v[0-9.]+`\)' README.md | grep -vc 'v0.5.0')" = 0]
- ac4: the pinned orchestrator plugin's session_send schema carries priority [evidence: command:grep -rq '"priority"' "$(uv run --frozen python -c 'import os, any_mcp_tatara_orchestrator as m; print(os.path.dirname(m.__file__))')"]
- ac5: settings, images and on-start suites and lint pass [evidence: command:uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint]

## Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `tests/test_settings.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
