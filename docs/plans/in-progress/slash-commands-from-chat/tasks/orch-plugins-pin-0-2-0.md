---
title: orch plugins pin 0.2.0
status: in-progress
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

Amendment (2026-10-29, user-approved release order agreed between hives 2026-10-28): the epic matrix-connector-agent-initi ran first, released any-mcp-tatara-plugins `v0.2.0` (commit 4506e70) and already pinned agents-orchestrator `main` to it (settings default, dev dependency, uv.lock, README, `tests/test_settings.py::test_defaults`, merge a9f936f). This epic releases `v0.3.0` (task plugins-release-0-2-0), so this pin moves `v0.2.0` -> `v0.3.0`: the release named `v0.2.0` in the quotes above now reads `v0.3.0` (design D13 amended the same way). The task slug stays orch-plugins-pin-0-2-0. Where the Interfaces, Steps and Notes sections below still name v0.2.0 (written before this amendment), they read v0.3.0.

Needs a merged upstream (see Amendment 2): any-mcp-tatara-plugins tag `v0.5.0` on origin (task plugins-release-0-2-0).


Amendment 2 (2026-10-29, user-approved, mx-34 #406): tatara's epic hive-decoupling released any-mcp-tatara-plugins `v0.4.0` (merge 6d5cc19, plugin version 0.4.0) and pinned agents-orchestrator `main` to it (df2b80e) before this epic's `v0.3.0` was tagged; `v0.3.0` stays unused. This epic ships as plugins `v0.5.0` on top of `v0.4.0`. Where Amendment 1 and the sections below read `v0.3.0`/`0.3.0` they now read `v0.5.0`/`0.5.0`, and where they read `v0.2.0`/`0.2.0` as the current release on `main` they now read `v0.4.0`/`0.4.0`. The Scope below is restated with these numbers. Tagging `v0.5.0` is approved (standing release-tag rule mx-34 #396 satisfied by #406).

Scope (agents-orchestrator), on the epic branch rebased onto orchestrator `main` (which carries the v0.4.0 pin):
- `src/agents_orchestrator/settings.py`: `any_mcp_plugins_ref` default `v0.4.0` -> `v0.5.0`.
- `pyproject.toml`: dev dependency `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.5.0#subdirectory=orchestration/orchestrator` (was `@v0.4.0`); `uv lock` updates `uv.lock`.
- `README.md`: the `ORCH_ANY_MCP_PLUGINS_REF` row default `v0.5.0` and the `## Images` any-mcp paragraph (`v0.4.0` -> `v0.5.0` for the plugins release tag only; the any-mcp `v0.5.0` pin is unchanged).
- `tests/test_settings.py::test_defaults` is no longer accurate (named): on `main` it pins `any_mcp_plugins_ref == "v0.4.0"`; it asserts `v0.5.0`.
- No agents-helmfile change (the gate's deploy decision).
- Needs any-mcp-tatara-plugins tag `v0.5.0` on origin (task plugins-release-0-2-0).

## Acceptance conditions

- ac1: the settings default is v0.5.0 (updated) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the README documents the v0.5.0 default and no longer names v0.4.0 or v0.1.0 for the plugins [evidence: command:grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.5.0` |' README.md && ! grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.4.0` |' README.md && ! grep -qF 'pin the same plugins release tag (`v0.4.0`)' README.md && ! grep -q "plugins release tag (\`v0.1.0\`)" README.md]
- ac4: the pinned orchestrator plugin carries the new session_send description [evidence: command:grep -rq "Claude Code slash command" "$(uv run --frozen python -c 'import os, any_mcp_tatara_orchestrator as m; print(os.path.dirname(m.__file__))')"]
- ac5: settings, images and on-start suites and lint pass [evidence: command:uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint]

## Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `tests/test_settings.py`

## Interfaces

- `Settings.any_mcp_plugins_ref` default `v0.2.0` (`ORCH_ANY_MCP_PLUGINS_REF`); dev dependency `any-mcp-tatara-orchestrator` at `v0.2.0`.

## Expected outcome

Agent pods rendered by this orchestrator install the plugins release whose session_send description says slash text from a superleader runs as a command.

## Steps

- Confirm tag `v0.2.0` on any-mcp-tatara-plugins origin (`git ls-remote --tags https://github.com/szymonrychu/any-mcp-tatara-plugins v0.2.0`).
- Red: change `test_defaults` to v0.2.0; run `uv run --frozen pytest tests/test_settings.py tests/test_images.py`: fails.
- Green: settings default, pyproject pin, `uv lock`, README; run the task's verify: passes. Quote the summary line.

## Notes

- `tests/test_images.py::test_plugins_dev_pin_matches_settings_ref` ties the dev dependency, uv.lock and the settings default to one tag.
- Changing the default changes the rendered config hash and rolls agent pods on deploy (README `## Images`); deploy is the gate's decision.
- Sequenced after orch-wrapper-pin-0-4-0 so one task at a time edits `pyproject.toml` and `uv.lock` (my call).
- Depends on plugins-release-0-2-0 and orch-wrapper-pin-0-4-0.

- 2026-10-29 amended: release order changed (user-approved, agreed between hives 2026-10-28): orchestrator main already pins plugins v0.2.0 (matrix-connector-agent-initi), so this pin moves v0.2.0 -> v0.3.0; slug stays orch-plugins-pin-0-2-0

- 2026-10-29 amended: plugins renumbered: hive-decoupling took v0.4.0 first; slash ships v0.5.0 (user-approved mx-34 #406)
