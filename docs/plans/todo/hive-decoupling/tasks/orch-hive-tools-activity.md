---
title: orch hive tools activity
status: todo
repo: agents-orchestrator
value: hive agents see orchestrator_activity and the plugin advice always shows the real threshold
files: [src/agents_orchestrator/k8s/on_start.py, tests/test_on_start.py, README.md]
verify: "uv run --frozen pytest tests/test_on_start.py tests/test_render.py && mise run lint"
depends_on: [orch-plugins-pin-0-4-0]
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

# orch hive tools activity

## Requirement

README Goal G2, verbatim: "Any hive agent pulls recent activity on demand: `GET /agent/v1/activity` (optional `agent`, `limit` 1..200) and the plugin tool `orchestrator_activity`."

README Goal G3, verbatim (the plugin part): "the `hive_state` hint and the plugin advice always use the effective threshold."

Design D9, verbatim: "`activity` joins `HIVE_TOOLS` after `me`; the rendered plugin config carries the effective `auto_compact_pct` (`spec.auto_compact_pct or settings.default_auto_compact_pct`) so the plugin advice always shows (fix-as-ac)".

Scope (agents-orchestrator):
- `src/agents_orchestrator/k8s/on_start.py`: `HIVE_TOOLS = ["me", "activity", "leadership_handover", ...]`; `_orchestrator_entry` config `auto_compact_pct: spec.auto_compact_pct or settings.default_auto_compact_pct`.
- `tests/test_on_start.py`: its `HIVE_TOOLS` list is no longer accurate (named): it gains `activity` after `me`; `test_hive_entry_and_allow` keeps 70 from the spec; new `test_plugin_config_effective_auto_compact` (a spec without `auto_compact_pct` renders `settings.default_auto_compact_pct`, 95 by default).
- `README.md` `### Hive` tool gating bullet: the allowlist reads `me`, `activity`, `leadership_handover`, ...
- Read the file as merged by matrix-connector-agent-initi first (it adds its chat tools to `orchestrator_allow`); keep them.
- Changing the rendered config rolls agent pods on deploy (README Images); the deploy is helmfile-apply-live-proof.

## Acceptance conditions

- ac1: a hive session's allowlist has activity right after me (test list updated, named) [evidence: test:tests/test_on_start.py::test_hive_session_tools]
- ac2: a spec without auto_compact_pct renders the settings default in the plugin config [evidence: test:tests/test_on_start.py::test_plugin_config_effective_auto_compact]
- ac3: a spec auto_compact_pct is rendered unchanged [evidence: test:tests/test_on_start.py::test_hive_entry_and_allow]
- ac4: every allowed tool exists in the pinned plugin [evidence: test:tests/test_on_start.py::test_allowed_tools_exist_in_plugin]
- ac5: the README tool gating lists activity after me [evidence: command:grep -qF '`me`, `activity`, `leadership_handover`' README.md]
- ac6: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_on_start.py tests/test_render.py && mise run lint]

## Files

- `src/agents_orchestrator/k8s/on_start.py`
- `tests/test_on_start.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
