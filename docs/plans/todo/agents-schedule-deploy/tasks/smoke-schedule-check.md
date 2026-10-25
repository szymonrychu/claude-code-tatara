---
title: smoke schedule check
status: todo
repo: agents-helmfile
value: "the live smoke proves a schedule can be created, previewed and run against the real orchestrator"
files: [scripts/smoke.sh, tests/test_smoke_script.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py && shellcheck --severity=error scripts/smoke.sh && uv run ruff check ."
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

# smoke schedule check

## Requirement

Add a schedule step to `scripts/smoke.sh` (design D14; approvals A5, A6): port-forward `deploy/agents-schedule-api` (port 8000, like the orchestrator step), then: `GET /readyz` 200; `POST /schedules/api/v1/schedules` a disabled schedule `smoke-<ts>` on the default preset with cron `0 3 * * *`; `POST /schedules/preview` returns 3 times; `POST /schedules/{id}/run` 202; poll `GET /runs/{run_id}` until `in-progress` with a `session_id` (bounded by `SMOKE_TIMEOUT_S`); the cleanup trap deletes that session through the orchestrator API and the schedule through the schedule API, and prints the manual cleanup line when either is unreachable. tests/test_smoke_script.py extends the fake server with the schedule routes and asserts the step passes, fails on a run that goes `failed`, and cleans up.

## Acceptance conditions

- AC1: the smoke step passes against the fake server [evidence: test:tests/test_smoke_script.py::test_schedule_step_passes]
- AC2: a failed run fails the smoke with its reason [evidence: test:tests/test_smoke_script.py::test_schedule_step_failed_run]
- AC3: the cleanup trap deletes the session and the schedule [evidence: test:tests/test_smoke_script.py::test_schedule_step_cleans_up]
- AC4: shellcheck passes [evidence: command:shellcheck --severity=error scripts/smoke.sh]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
