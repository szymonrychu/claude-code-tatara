---
title: orch plugins pin 0.4.0
status: todo
repo: agents-orchestrator
value: agent pods install the plugins release that offers the activity tool
files: [src/agents_orchestrator/settings.py, pyproject.toml, uv.lock, README.md, tests/test_settings.py]
verify: "uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint"
depends_on: [plugins-release-0-4-0, orch-handover-outcome-note, orch-drop-feed-cursor]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch plugins pin 0.4.0

## Requirement

README Goal G5, verbatim: "Released and deployed: any-mcp-tatara-plugins next minor tag, orchestrator pins, agents-helmfile bump, apply, a smoke covering the activity route and tool, and a live handoff proof."

Design D9, verbatim: "`any_mcp_plugins_ref` default, dev dependency and README Images move to the new plugins tag."

Needs a merged upstream: any-mcp-tatara-plugins tag `v0.4.0` on origin (task plugins-release-0-4-0).

Scope (agents-orchestrator):
- `src/agents_orchestrator/settings.py`: `any_mcp_plugins_ref` default `v0.4.0`.
- `pyproject.toml`: dev dependency `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.4.0#subdirectory=orchestration/orchestrator`; `uv lock` updates `uv.lock`.
- `README.md`: the `ORCH_ANY_MCP_PLUGINS_REF` row default `v0.4.0` and the `## Images` plugins release tag.
- `tests/test_settings.py::test_defaults` is no longer accurate (named): after the Matrix epic it pins `any_mcp_plugins_ref == "v0.3.0"`; it asserts `v0.4.0`.
- No agents-helmfile change here (helmfile-deploy-pin).

## Acceptance conditions

- ac1: the settings default is v0.4.0 (updated, named) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the README documents the v0.4.0 default and names no older plugins tag [evidence: command:grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.4.0` |' README.md && ! grep -qE 'plugins release tag \(`v0\.[123]\.0`\)' README.md]
- ac4: the pinned orchestrator plugin carries the activity tool [evidence: command:grep -rq "/activity" "$(uv run --frozen python -c 'import os, any_mcp_tatara_orchestrator as m; print(os.path.dirname(m.__file__))')"]
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
