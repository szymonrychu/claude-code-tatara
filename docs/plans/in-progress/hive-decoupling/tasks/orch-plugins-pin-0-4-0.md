---
title: orch plugins pin 0.4.0
status: in-progress
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

Needs a merged upstream: any-mcp-tatara-plugins tag `v0.3.0` on origin (task plugins-release-0-4-0).

Scope (agents-orchestrator):
- `src/agents_orchestrator/settings.py`: `any_mcp_plugins_ref` default `v0.3.0`.
- `pyproject.toml`: dev dependency `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.3.0#subdirectory=orchestration/orchestrator`; `uv lock` updates `uv.lock`.
- `README.md`: the `ORCH_ANY_MCP_PLUGINS_REF` row default `v0.3.0` and the `## Images` plugins release tag.
- `tests/test_settings.py::test_defaults` is no longer accurate (named): it pins the previous plugins tag; it asserts `v0.3.0`.
- No agents-helmfile change here (helmfile-deploy-pin).

Builder check settlement 1 (2026-10-27, my call): the build starts only after slash-commands-from-chat and matrix-connector-agent-initi have merged. `v0.3.0` (the plugins release tag, `vX.Y.Z`), `0.3.0` (the same without the `v`) and `0010` (the orchestrator migration number, four digits) in this task are placeholders: orch-activity-route reads the real values from main and replaces them here with `ticket.py amend` before this task starts. No number in this task is assumed; `0.4.0` and `0009` in design.md are only the expectation.

## Acceptance conditions

- ac1: the settings default is v0.3.0 (updated, named) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the README documents the v0.3.0 default and names no older plugins tag [evidence: command:grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.3.0` |' README.md && test "$(grep -oE 'plugins release tag \(`v[0-9.]+`\)' README.md | grep -vc 'v0.3.0')" = 0]
- ac4: the pinned orchestrator plugin carries the activity tool [evidence: command:grep -rq "/activity" "$(uv run --frozen python -c 'import os, any_mcp_tatara_orchestrator as m; print(os.path.dirname(m.__file__))')"]
- ac5: settings, images and on-start suites and lint pass [evidence: command:uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint]

## Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `tests/test_settings.py`

## Interfaces

- `Settings.any_mcp_plugins_ref` default `v0.3.0` (`ORCH_ANY_MCP_PLUGINS_REF`); dev dependency `any-mcp-tatara-orchestrator` at `v0.3.0`.

## Expected outcome

Agent pods rendered by this orchestrator install the plugins release that offers the activity tool.

## Steps

- Confirm tag `v0.3.0` on any-mcp-tatara-plugins origin (`git ls-remote --tags https://github.com/szymonrychu/any-mcp-tatara-plugins v0.3.0`); stop and report if absent.
- Red: change `test_defaults` to v0.3.0; run `uv run --frozen pytest tests/test_settings.py tests/test_images.py`: fails.
- Green: settings default, pyproject pin, `uv lock`, README; run the task's verify: passes. Quote the summary line.

## Notes

- Dependency-bump TDD exception for the version values; `test_plugins_dev_pin_matches_settings_ref` ties dev dependency, uv.lock and the default to one tag.
- Shared file `settings.py` with the epics before; build on their pins.
- Changing the default changes the rendered config hash and rolls agent pods on deploy (README `## Images`); the deploy is helmfile-apply-live-proof.

- 2026-10-27 amended: builder check settlement 1: migration number and plugins tag are placeholders until orch-activity-route amends them from main
