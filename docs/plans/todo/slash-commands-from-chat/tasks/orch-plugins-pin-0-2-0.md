---
title: orch plugins pin 0.2.0
status: todo
repo: agents-orchestrator
value: agent pods install the orchestrator plugin release that tells superleaders slash text runs as a command
files: [src/agents_orchestrator/settings.py, pyproject.toml, uv.lock, README.md, tests/test_settings.py]
verify: "uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint"
depends_on: [plugins-release-0-2-0, orch-wrapper-pin-0-4-0]
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

# orch plugins pin 0.2.0

## Requirement

Goal G2 (README), verbatim: "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text."

Builder check settlement (user decision), verbatim: "add two tasks, any-mcp-tatara-plugins release v0.2.0 after plugin-session-send-slash, and an orchestrator plugins pin bump (ORCH_ANY_MCP_PLUGINS_REF, dev dependency, README, tests)".

Design D13, verbatim (the pin part): "then the orchestrator pins it (task orch-plugins-pin-0-2-0: the `ORCH_ANY_MCP_PLUGINS_REF` default, the `any-mcp-tatara-orchestrator` dev dependency, README, tests), so superleaders actually see the description. The helmfile value of `ORCH_ANY_MCP_PLUGINS_REF` stays with the gate's deploy decision."

Needs a merged upstream: any-mcp-tatara-plugins tag `v0.2.0` on origin (task plugins-release-0-2-0).

Scope (agents-orchestrator):
- `src/agents_orchestrator/settings.py`: `any_mcp_plugins_ref` default `v0.2.0`.
- `pyproject.toml`: dev dependency `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.2.0#subdirectory=orchestration/orchestrator`; `uv lock` updates `uv.lock`.
- `README.md`: the `ORCH_ANY_MCP_PLUGINS_REF` row default `v0.2.0` and the `## Images` any-mcp paragraph (`v0.1.0` -> `v0.2.0` for the plugins release tag only; the any-mcp `v0.5.0` pin is unchanged).
- `tests/test_settings.py::test_defaults` is no longer accurate (named): it pins `any_mcp_plugins_ref == "v0.1.0"`; it asserts `v0.2.0`.
- No agents-helmfile change (the gate's deploy decision).

## Acceptance conditions

- ac1: the settings default is v0.2.0 (updated) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the README documents the v0.2.0 default and no longer names v0.1.0 for the plugins [evidence: command:grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.2.0` |' README.md && ! grep -q "plugins release tag (\`v0.1.0\`)" README.md]
- ac4: the pinned orchestrator plugin carries the new session_send description [evidence: command:grep -rq "Claude Code slash command" "$(uv run --frozen python -c 'import os, any_mcp_tatara_orchestrator as m; print(os.path.dirname(m.__file__))')"]
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
