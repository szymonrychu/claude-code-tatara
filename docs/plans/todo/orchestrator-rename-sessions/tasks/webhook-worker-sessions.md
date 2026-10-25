---
title: webhook worker sessions
status: todo
repo: agents-webhook
value: the webhook worker starts and reuses sessions through agents-common v0.3.0
files: [pyproject.toml, uv.lock, src/agents_webhook/worker.py, README.md, tests/]
verify: "uv run pytest -q tests/test_worker.py tests/test_worker_reuse.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-session-columns, common-release-v0-3-0]
model: opus
review: ""
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# webhook worker sessions

## Requirement

Move agents-webhook onto agents-common v0.3.0 and the session vocabulary in the worker (design D2, D11; contract `agents-common-release-v0-3-0`). Paths are in code/agents-webhook.

- `pyproject.toml`: both `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.3.0` lines (runtime and `[testing]`); `uv.lock` refreshed.
- `src/agents_webhook/worker.py`: `create_session`, `running_session`, `RunRef(session_id=...)`, `set_session`; every log line, docstring and comment says session ("the run's session", "falls back once to a new session `wh-<id>`"); failure reason `session_not_found`.
- `README.md`: the worker behaviour and the failure reasons table (`session_not_found`), session for the unit.
- tests/: `test_worker.py`, `test_worker_reuse.py`, `tests/e2e/` on the v0.3.0 fake orchestrator (`discard_session`, `remove_session`, `/api/v1/sessions`); tests first: `tests/test_worker_reuse.py::test_gone_session_falls_back_to_new_session` and `tests/test_worker.py::test_missing_session_reason`.
- Confirm by reading worker.py that `OrchestratorUnavailable` leaves the row queued for a retry (design Assumptions, needed for the cutover window); when no test pins it, add `tests/test_worker.py::test_orchestrator_unavailable_retries`.

## Acceptance conditions

- AC1: a gone session falls back once to a new session [evidence: test:tests/test_worker_reuse.py::test_gone_session_falls_back_to_new_session]
- AC2: a missing session fails the event with session_not_found [evidence: test:tests/test_worker.py::test_missing_session_reason]
- AC3: an unreachable orchestrator leaves the event for a retry [evidence: judgement:the task notes name the test that pins OrchestratorUnavailable retry, existing or added]
- AC4: the worker suites and lint pass on agents-common v0.3.0 [evidence: command:uv run pytest -q tests/test_worker.py tests/test_worker_reuse.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `src/agents_webhook/worker.py`
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
