---
title: orch orchestration tools pin
status: todo
repo: agents-orchestrator
value: "agent pods of flagged sessions install and may call the orchestration tools, no other session sees them"
files: [src/agents_orchestrator/settings.py, pyproject.toml, uv.lock, src/agents_orchestrator/k8s/on_start.py, README.md, tests/test_settings.py, tests/test_on_start.py, tests/test_orchestration_tools_parity.py]
verify: "uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py tests/test_orchestration_tools_parity.py && mise run lint"
depends_on: [plugins-release-orch-tools, orch-chart-schedule-relay]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch orchestration tools pin

## Requirement

README Goal G1, verbatim: "A session the user flagged `session_orchestration` (a per-preset or per-spec switch, off by default, set only by the user through agents-web or the public API) has orchestrator MCP tools to list, create, edit and delete presets, list, create, scale and delete sessions, and list, create, edit, delete and run cron schedules, on the user's request; only its leader may call them, and no unflagged session gets the tools."

Design D1, verbatim: "The orchestrator tools render only when the flag is true: `orchestrator_allow` adds `ORCHESTRATION_TOOLS`, as with `scale`."

Design D11, verbatim: "The release is the next minor after the version hive-decoupling leaves pinned. The allow-list change lands with the pin in one task, per Matrix D13 (`test_allowed_tools_exist_in_plugin` needs both)."

Needs a merged upstream: the any-mcp-tatara-plugins release tag pushed by plugins-release-orch-tools.

Scope (agents-orchestrator): `settings.py` (`any_mcp_plugins_ref` default the new tag), `pyproject.toml` and `uv.lock` (dev dependency at the new tag), `k8s/on_start.py` (`ORCHESTRATION_TOOLS`, added to a flagged session's list, alone and hive), README (the default ref, the `## Images` plugins tag, the tools only for flagged sessions), `tests/test_settings.py`, `tests/test_on_start.py`, new `tests/test_orchestration_tools_parity.py`.

Test no longer accurate (named): `tests/test_settings.py::test_defaults` pins the plugins ref hive-decoupling left; it asserts the new tag.

## Acceptance conditions

- ac1: the plugins ref settings default is the tag released by plugins-release-orch-tools (updated) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: a flagged session's allow list, alone and hive, ends with the sixteen orchestration tools, and an unflagged session's list has none of them [evidence: test:tests/test_on_start.py::test_orchestration_tools_only_when_flagged]
- ac4: every allowed tool, the orchestration tools included, exists in the pinned plugin [evidence: test:tests/test_on_start.py::test_allowed_tools_exist_in_plugin]
- ac5: the released plugin drives every orchestration tool against the real agent routes and the fake schedule relay, and each result equals the direct route answer [evidence: test:tests/test_orchestration_tools_parity.py::test_orchestration_tools_parity]
- ac6: the README documents the new default ref and that the orchestration tools render only for flagged sessions [evidence: command:grep -q "orchestrator_session_create" README.md]
- ac7: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py tests/test_orchestration_tools_parity.py && mise run lint]

## Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `src/agents_orchestrator/k8s/on_start.py`
- `README.md`
- `tests/test_settings.py`
- `tests/test_on_start.py`
- `tests/test_orchestration_tools_parity.py`

## Interfaces

- `k8s/on_start.py:ORCHESTRATION_TOOLS = ["presets_list", "preset_get", "preset_create", "preset_update", "preset_delete", "sessions_overview", "session_create", "session_scale", "session_delete", "schedules_list", "schedule_create", "schedule_update", "schedule_delete", "schedule_run", "schedule_runs", "orchestration_actions"]`; `orchestrator_allow(spec)` appends it when `spec.session_orchestration`.
- `Settings.any_mcp_plugins_ref` default: the new tag (`ORCH_ANY_MCP_PLUGINS_REF`).

## Expected outcome

Agent pods of flagged sessions install the plugins release with the orchestration tools and may call them; no other session sees them.

## Steps

- Confirm the new tag on any-mcp-tatara-plugins origin (`git ls-remote --tags https://github.com/szymonrychu/any-mcp-tatara-plugins <tag>`); stop and report if absent.
- Red: update `test_defaults`, add `test_orchestration_tools_only_when_flagged` and the parity test; run them: fail.
- Green: settings default, pyproject pin, `uv lock`, `on_start.py`, README; run the task's verify. Quote the summary line.

## Notes

- Dependency-bump TDD exception for the version values; `test_plugins_dev_pin_matches_settings_ref` ties them to one tag.
- Builds on hive-decoupling's and Matrix's versions of `on_start.py` and `settings.py` (shared files); read them first.
- The flag does not change for a running session, so the render stays fixed (D1).
- Changing the default changes the rendered config hash and rolls agent pods on deploy (orchestration-live-smoke).
- The parity test's DB cases run in CI.
