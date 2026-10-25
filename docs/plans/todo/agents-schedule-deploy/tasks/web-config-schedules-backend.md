---
title: web config schedules backend
status: todo
repo: agents-helmfile
value: the deployed UI lists the schedule backend so its menu entry appears
files: [values/agents-web/common.yaml, tests/test_web_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_web_release.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 678580
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web config schedules backend

## Requirement

Add the `schedules` backend to the agents-web release values (design D12; approval A4) in the shape of `agents-web-backends-config` (chart value `backends`): `{id: schedules, label: Schedules, basePath: /schedules/api/v1}`. tests/test_web_release.py `test_schedules_backend_configured` asserts the entry next to the orchestrator one.

## Acceptance conditions

- AC1: config.json values list the schedules backend after webhooks [evidence: test:tests/test_web_release.py::test_schedules_backend_configured]

## Files

- `values/agents-web/common.yaml`
- `tests/test_web_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
