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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
