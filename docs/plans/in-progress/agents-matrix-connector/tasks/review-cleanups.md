---
title: review cleanups
status: todo
repo: agents-matrix-connector
value: "one clock helper, no upstream error text in API bodies, pinned build images"
files: [src/agents_matrix_connector/clock.py, src/agents_matrix_connector/worker.py, src/agents_matrix_connector/tracker.py, src/agents_matrix_connector/sync.py, src/agents_matrix_connector/api/rooms.py, src/agents_matrix_connector/api/rules.py, Dockerfile, tests/test_api_rules.py, tests/test_ci.py, openapi.json, README.md]
verify: "uv run --frozen pytest tests/test_api_rules.py tests/test_ci.py tests/test_worker.py tests/test_tracker.py tests/test_sync.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [matrix-identity-spoofing-gua]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 531208
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# review cleanups

## Requirement

Findings of the epic scope audit and security review (2026-10-25). Paths are in code/agents-matrix-connector. No behaviour change except item 2.

1. `utcnow()` is defined three times with an identical body (worker.py:57, tracker.py:53, sync.py:78): keep one definition in a small shared module (for example `src/agents_matrix_connector/clock.py`) and import it in all three, keeping the injectable-clock tests green.
2. `api/rooms.py:184` and `api/rules.py:86` return `str(exc)` of an `OrchestratorError` in the 502 body: return a fixed message (for example "orchestrator request failed") with code `orchestrator_error`, and log the detail server-side without tokens; update openapi.json/README only if the documented text changes.
3. `Dockerfile`: pin `ghcr.io/astral-sh/uv` to the uv version that produced `uv.lock` (no `latest`) and pin the Python base image to an exact patch tag; `tests/test_ci.py` asserts neither image uses `latest` or a floating tag.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: utcnow is defined once and imported by worker, tracker and sync [evidence: command:test "$(grep -rn 'def utcnow' src | wc -l | tr -d ' ')" = 1]
- AC2: an orchestrator error answers 502 orchestrator_error with a fixed message that does not echo the upstream error text [evidence: test:tests/test_api_rules.py::test_orchestrator_error_message_is_generic]
- AC3: the Dockerfile pins the uv image and the Python base image to exact versions [evidence: test:tests/test_ci.py::test_images_pinned]

## Files

- `src/agents_matrix_connector/clock.py`
- `src/agents_matrix_connector/worker.py`
- `src/agents_matrix_connector/tracker.py`
- `src/agents_matrix_connector/sync.py`
- `src/agents_matrix_connector/api/rooms.py`
- `src/agents_matrix_connector/api/rules.py`
- `Dockerfile`
- `tests/test_api_rules.py`
- `tests/test_ci.py`
- `openapi.json`
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
