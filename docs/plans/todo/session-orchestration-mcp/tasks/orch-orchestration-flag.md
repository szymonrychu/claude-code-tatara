---
title: orch orchestration flag
status: todo
repo: agents-orchestrator
value: the user can mark a preset as allowed to orchestrate other sessions
files: [src/agents_orchestrator/spec.py, src/agents_orchestrator/api/agent.py, README.md, openapi.json, tests/test_spec_session_options.py, tests/test_api_agent.py]
verify: "uv run --frozen pytest tests/test_spec_session_options.py tests/test_api_agent.py tests/test_readme_api.py && mise run lint"
depends_on: [orch-message-origin]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 936557
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch orchestration flag

## Requirement

README Goal G1, verbatim: "A session the user flagged `session_orchestration` (a per-preset or per-spec switch, off by default, set only by the user through agents-web or the public API) has orchestrator MCP tools to list, create, edit and delete presets, list, create, scale and delete sessions, and list, create, edit, delete and run cron schedules, on the user's request; only its leader may call them, and no unflagged session gets the tools."

Design D1, verbatim: "`SessionSpec.session_orchestration: bool | None = Field(default=None, strict=True)`, sparse like `session_messaging` and `kube_access`. Settable only through the public API or UI (preset, or spec at create). [...] `me` gains `orchestration: bool`."

Architect do-not-build, verbatim: "Making the flag editable in place on a running session."

Scope (agents-orchestrator): `spec.py` (the field, with a comment like its siblings), `api/agent.py` (`Me.orchestration`), README (spec option and `GET /agent/v1/me`), committed `openapi.json`. The allow list is orch-orchestration-tools-pin; agent-side refusal of the flag is orch-orchestration-gate (D5).

Tests no longer accurate (named): `tests/test_spec_session_options.py::test_options_sparse_and_strict` and `::test_preset_carries_options_to_session` cover the sibling flags; they are extended with `session_orchestration`.

## Acceptance conditions

- ac1: session_orchestration is a sparse strict bool: unset is neither stored nor dumped in a preset and a non-bool value is refused 422 (extended) [evidence: test:tests/test_spec_session_options.py::test_options_sparse_and_strict]
- ac2: a preset with session_orchestration true carries it to a session created from it (extended) [evidence: test:tests/test_spec_session_options.py::test_preset_carries_options_to_session]
- ac3: GET /agent/v1/me answers orchestration true for a flagged session and false otherwise [evidence: test:tests/test_api_agent.py::test_me_orchestration_flag]
- ac4: the flag stays immutable on a running session: no route changes it after create [evidence: test:tests/test_spec_session_options.py::test_session_orchestration_immutable]
- ac5: the README documents session_orchestration and me.orchestration, and openapi.json matches the app [evidence: command:grep -q session_orchestration README.md && uv run --frozen pytest tests/test_readme_api.py::test_openapi_json_matches_app]
- ac6: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_spec_session_options.py tests/test_api_agent.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agents_orchestrator/spec.py`
- `src/agents_orchestrator/api/agent.py`
- `README.md`
- `openapi.json`
- `tests/test_spec_session_options.py`
- `tests/test_api_agent.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
