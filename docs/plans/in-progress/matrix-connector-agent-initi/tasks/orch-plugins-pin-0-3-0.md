---
title: orch plugins pin 0.3.0
status: in-progress
repo: agents-orchestrator
value: agent pods install the plugins release that offers the chat tools
files: [src/agents_orchestrator/settings.py, pyproject.toml, uv.lock, README.md, tests/test_settings.py]
verify: "uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint"
depends_on: [plugins-release-0-3-0, orch-chat-relay]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch plugins pin 0.3.0

## Requirement

README Goal, verbatim: "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."

Design D13, verbatim: "The orchestrator then pins v0.2.0 and adds `CHAT_TOOLS` to every session's allow list (`k8s/on_start.py:orchestrator_allow`); the routes decide." (This task: the pin; orch-chat-tools-allow: the allow list.)

Needs a merged upstream: any-mcp-tatara-plugins tag `v0.2.0` on origin (task plugins-release-0-3-0).

Scope (agents-orchestrator):
- `src/agents_orchestrator/settings.py`: `any_mcp_plugins_ref` default `v0.2.0`.
- `pyproject.toml`: dev dependency `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.2.0#subdirectory=orchestration/orchestrator`; `uv lock` updates `uv.lock`.
- `README.md`: the `ORCH_ANY_MCP_PLUGINS_REF` row default `v0.2.0` and the `## Images` plugins release tag.
- `tests/test_settings.py::test_defaults` is no longer accurate (named): on main it pins `any_mcp_plugins_ref == "v0.1.0"`; it asserts `v0.2.0`.
- No agents-helmfile change (helmfile-chat-values).

## Acceptance conditions

- ac1: the settings default is v0.2.0 (updated) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the README documents the v0.2.0 default and no longer names v0.1.0 for the plugins [evidence: command:grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.2.0` |' README.md && ! grep -qF 'plugins release tag (`v0.1.0`)' README.md]
- ac4: the pinned orchestrator plugin carries the chat tools [evidence: command:grep -rq "chat_send" "$(uv run --frozen python -c 'import os, any_mcp_tatara_orchestrator as m; print(os.path.dirname(m.__file__))')"]
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

Agent pods rendered by this orchestrator install the plugins release that offers the chat tools.

## Steps

- Confirm tag `v0.3.0` on any-mcp-tatara-plugins origin (`git ls-remote --tags https://github.com/szymonrychu/any-mcp-tatara-plugins v0.3.0`); stop and report if absent.
- Red: change `test_defaults` to v0.3.0; run `uv run --frozen pytest tests/test_settings.py tests/test_images.py`: fails.
- Green: settings default, pyproject pin, `uv lock`, README; run the task's verify: passes. Quote the summary line.

## Notes

- Dependency-bump TDD exception for the version values; `test_plugins_dev_pin_matches_settings_ref` ties dev dependency, uv.lock and the default to one tag.
- Builds on slash-commands' orch-plugins-pin-0-2-0 (same files); this epic is blocked until it merged.
- The README check of ac3 assumes slash-commands wrote "plugins release tag (`v0.2.0`)"; read the README first and adapt the grep only in wording if the sentence differs, keeping the intent (no v0.2.0 plugins pin left).
- Changing the default changes the rendered config hash and rolls agent pods on deploy (README `## Images`); the deploy is chat-live-smoke.

- 2026-10-28 amended: plugins release number swap (design B2): this epic releases v0.2.0 on top of v0.1.0; slash-commands releases v0.3.0
