---
title: orch orchestration presets
status: todo
repo: agents-orchestrator
value: a flagged leader can read every preset safely and manage its own
files: [src/agents_orchestrator/api/orchestration_presets.py, src/agents_orchestrator/db/presets.py, src/agents_orchestrator/api/presets.py, src/agents_orchestrator/api/schemas.py, src/agents_orchestrator/api/app.py, README.md, openapi.json, tests/test_orchestration_presets.py]
verify: "uv run --frozen pytest tests/test_orchestration_presets.py tests/test_api_presets.py tests/test_readme_api.py && mise run lint"
depends_on: [orch-orchestration-gate]
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

# orch orchestration presets

## Requirement

README Goal G1, verbatim: "A session the user flagged `session_orchestration` (a per-preset or per-spec switch, off by default, set only by the user through agents-web or the public API) has orchestrator MCP tools to list, create, edit and delete presets, list, create, scale and delete sessions, and list, create, edit, delete and run cron schedules, on the user's request; only its leader may call them, and no unflagged session gets the tools."

README Goal G3, verbatim: "A flagged session changes only the sessions, presets and schedules it created; it reads all of them, with preset secrets masked except on its own; it cannot grant more privilege than it holds (`session_orchestration` is never grantable), cannot delete itself, and cannot delete a superleader or orchestrating session."

Design D4, verbatim: "Writes only on objects owned by the caller session: [...] `presets.created_by_session_id` and `created_by_slug` [...]. Otherwise 403 `not_owner` [...]. Presets: spec with `env` values, `wrapper.hooks.*.secret`, header values and command `env` values masked, except on own presets. No copy tool. [...] The public `SessionView` and `PresetView` gain `created_by_slug` (additive; null for objects the user made) so agents-web can show it (Q7; my call pending the gate)."

Design D5, verbatim: "Applies to an agent-written preset spec, an agent-created session spec (from a spec or a preset) and the preset named by an agent-written schedule (the relay reads it first)."

Design D6, verbatim: "Preset delete: own only; the `PresetDefault` and `LastPreset` refusals still apply."

Architect fix-as-ac, verbatim: "Masked secrets in non-owned preset views." and "No escalation through presets, specs or schedule presets (`privilege_escalation`)."

Architect do-not-build, verbatim: "A preset copy tool."

Scope (agents-orchestrator): new `api/orchestration_presets.py` (`GET /presets`, `GET /presets/{id}`, `POST /presets`, `PUT /presets/{id}`, `DELETE /presets/{id}` under `/agent/v1/orchestration`), `db/presets.py` (store and read `created_by_*`), `api/presets.py` and `api/schemas.py` (`PresetView.created_by_slug`), `api/app.py`, README, `openapi.json`.

## Acceptance conditions

- ac1: the preset list and get return every preset, and on presets the caller did not create the env values, wrapper hook secrets, webhook and MCP header values and command and MCP stdio env values are masked with their keys kept, while the caller's own presets are unmasked [evidence: test:tests/test_orchestration_presets.py::test_masked_except_own]
- ac2: preset create validates like POST /api/v1/presets, stores the caller's created_by_session_id and created_by_slug and refuses privilege_escalation [evidence: test:tests/test_orchestration_presets.py::test_create_owned_and_validated]
- ac3: preset update and delete act only on presets the caller created (403 not_owner, 404 not_found for a missing id), update refuses privilege_escalation, and the PresetDefault and LastPreset refusals still apply [evidence: test:tests/test_orchestration_presets.py::test_update_delete_own_only]
- ac4: no copy route exists under /agent/v1/orchestration [evidence: test:tests/test_orchestration_presets.py::test_no_copy_route]
- ac5: every preset write, refusals included, writes an audit row with target_kind preset and the preset id and name [evidence: test:tests/test_orchestration_presets.py::test_preset_writes_audited]
- ac6: the public PresetView carries created_by_slug, null for presets the user made [evidence: test:tests/test_orchestration_presets.py::test_public_view_created_by]
- ac7: the README documents every preset orchestration route and the masked fields, and openapi.json matches the app [evidence: command:uv run --frozen pytest tests/test_readme_api.py]
- ac8: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_orchestration_presets.py tests/test_api_presets.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agents_orchestrator/api/orchestration_presets.py`
- `src/agents_orchestrator/db/presets.py`
- `src/agents_orchestrator/api/presets.py`
- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/api/app.py`
- `README.md`
- `openapi.json`
- `tests/test_orchestration_presets.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
