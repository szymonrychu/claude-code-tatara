---
title: web config schedules backend
status: todo
repo: agents-helmfile
value: the deployed UI lists the schedule backend so its menu entry appears
files: [values/agents-web/common.yaml, tests/test_web_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_web_release.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [agents-web-schedules-config]
uses: [agents-web-backends-config]
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
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
