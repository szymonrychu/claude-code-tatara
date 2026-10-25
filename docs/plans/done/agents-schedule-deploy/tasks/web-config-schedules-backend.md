---
title: web config schedules backend
status: done
repo: agents-helmfile
value: the deployed UI lists the schedule backend so its menu entry appears
files: [values/agents-web/common.yaml, tests/test_web_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_web_release.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: ""
review: ""
verified_head: ead1cde61c9924f44d54f8d9c43bb85a209a48c0
points: 1
expected_minutes: 5
expected_tokens: 678580
points_actual: 1
actual_minutes: 1
actual_tokens: 226517
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 118722, review 107795"
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

- agents-web `config.json` backend entry `schedules` (part `agents-web-schedules-config`).

## Expected outcome

The live UI shows the Schedules entry once deployed.

## Steps

- Add the test to tests/test_web_release.py; it fails.
- Add the values entry; it passes.
- Lint clean.

## Notes

- `values/agents-web/common.yaml` and `tests/test_web_release.py` are created by frontend-decoupling; this task only adds the entry.

- 2026-10-25 done
