---
title: common client sessions
status: todo
repo: agents-common
value: "the trigger services' shared client speaks the session API"
files: [src/agents_common/orchestrator.py, src/agents_common/fake_orchestrator.py, src/agents_common/runs.py, README.md, tests/]
verify: "uv run pytest -q tests/test_orchestrator_client.py tests/test_runs.py tests/test_reuse.py tests/test_nomenclature.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# common client sessions

## Requirement

Rename the orchestrator client, its fake and the run tracker from cluster to session (design D2, D12; user decision: cluster is renamed session throughout; contract `orch-sessions-api` as consumer, supersedes `preset-mapping-model`'s RunRef.cluster_id). Paths are in code/agents-common.

- `src/agents_common/orchestrator.py`: model `Session` (was `Cluster`), `create_session(preset_id, slug)` (idempotent on slug as today), `get_session(session_id)`, `list_messages(session_id)`, `post_message(session_id, text)`; routes `/api/v1/sessions`, `/api/v1/sessions/{id}`, `/api/v1/sessions/{id}/messages`; message model field `session_id`; error code `session_deleting`; every docstring says session and agents-orchestrator.
- `src/agents_common/fake_orchestrator.py`: serves the same `/api/v1/sessions` routes; `sessions` store, `discard_session(session_id)`, `remove_session(session_id)`, route labels `list_sessions`/`create_session`/`get_session`; messages carry `session_id`; 409 `session_deleting`.
- `src/agents_common/runs.py`: `RunRef.session_id`, `RunStore.set_session`, `running_session(client, session_id)`, failure reason `session_not_found`; every docstring.
- `README.md`: public names and examples on the new names.
- tests/: `test_orchestrator_client.py`, `test_runs.py`, `test_reuse.py` follow the rename; tests first: `tests/test_orchestrator_client.py::test_session_routes` (the client calls `/api/v1/sessions...` against the fake and never `/clusters`), `tests/test_runs.py::test_missing_session_fails_run` (reason `session_not_found`); new `tests/test_nomenclature.py` (D12) guarding every tracked file except the dated-history files.
- Version and tag belong to common-release-v0-3-0. No alias names.

## Acceptance conditions

- AC1: the client and the fake use /api/v1/sessions routes only [evidence: test:tests/test_orchestrator_client.py::test_session_routes]
- AC2: a missing session fails the run with session_not_found [evidence: test:tests/test_runs.py::test_missing_session_fails_run]
- AC3: no tracked file names the unit cluster or the project agent-orchestrator outside dated history [evidence: command:uv run pytest -q tests/test_nomenclature.py]
- AC4: the touched suites and lint pass [evidence: command:uv run pytest -q tests/test_orchestrator_client.py tests/test_runs.py tests/test_reuse.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_common/orchestrator.py`
- `src/agents_common/fake_orchestrator.py`
- `src/agents_common/runs.py`
- `README.md`
- `tests/`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
