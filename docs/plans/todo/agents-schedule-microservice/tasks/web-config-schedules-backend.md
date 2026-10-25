---
title: web config schedules backend
status: todo
repo: agents-helmfile
value: the deployed UI lists the schedule backend so its menu entry appears
files: [values/agents-web/common.yaml, tests/test_web_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_web_release.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [agents-web-schedules-config]
uses: [web-backends-config]
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

Add the `schedules` backend to the agents-web release values (design D12; approval A4) in the shape of `web-backends-config`: `{id: schedules, label: Schedules, basePath: /schedules/api/v1}` placed after the webhooks entry. tests/test_web_release.py asserts the entry and its order.

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

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
