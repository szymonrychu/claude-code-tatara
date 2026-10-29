---
title: orch plugins pin 0.5.1
status: todo
repo: agents-orchestrator
value: "the slash deploy carries the latest stable orchestrator plugin, including tatara's handover advice floor"
files: [src/agents_orchestrator/settings.py, pyproject.toml, uv.lock, README.md, tests/test_settings.py]
verify: "uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint"
depends_on: [orch-wrapper-pin-0-4-1]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 625210
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch plugins pin 0.5.1

## Requirement

Leader decision (2026-10-29, mx-34 #462, relaying tatara #460): tatara tagged any-mcp-tatara-plugins `v0.5.1` (76d7fb3, merge ef17204: the orchestrator plugin floors the handover advice threshold at 1%), on top of this epic's `v0.5.0` (dfa0355; `git merge-base --is-ancestor dfa0355 v0.5.1` verified). The slash deploy pins `v0.5.1` instead of `v0.5.0` (deployed pins are always the latest stable, standing rule mx-34 #396).

Scope (agents-orchestrator), on the epic branch rebased onto orchestrator `main`, same files as orch-plugins-pin-0-2-0:
- `src/agents_orchestrator/settings.py`: `any_mcp_plugins_ref` default `v0.5.0` -> `v0.5.1`.
- `pyproject.toml`: dev dependency `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.5.1#subdirectory=orchestration/orchestrator`; `uv lock` updates `uv.lock`.
- `README.md`: the `ORCH_ANY_MCP_PLUGINS_REF` row default `v0.5.1` and the `## Images` plugins release tag (`v0.5.0` -> `v0.5.1`; the any-mcp `v0.5.0` pin is a different repo and stays).
- `tests/test_settings.py::test_defaults` is no longer accurate (named): it pins `v0.5.0`; it asserts `v0.5.1`.

## Acceptance conditions

- ac1: the settings default is v0.5.1 (updated) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the README documents the v0.5.1 default and no longer names v0.5.0 for the plugins [evidence: command:grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.5.1` |' README.md && ! grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.5.0` |' README.md]
- ac4: the pinned orchestrator plugin carries the slash session_send description and the advice floor [evidence: command:d="$(uv run --frozen python -c 'import os, any_mcp_tatara_orchestrator as m; print(os.path.dirname(m.__file__))')" && grep -rq "Claude Code slash command" "$d"]
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
