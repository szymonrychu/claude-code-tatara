---
title: smoke schedule check
status: done
repo: agents-helmfile
value: "the live smoke proves a schedule can be created, previewed and run against the real orchestrator"
files: [scripts/smoke.sh, tests/test_smoke_script.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py && shellcheck --severity=error scripts/smoke.sh && uv run ruff check ."
depends_on: []
model: ""
review: ""
verified_head: 392e1a3fc3081afe922ff450e0c4660c1160f952
points: 1
expected_minutes: 5
expected_tokens: 678580
points_actual: 2
actual_minutes: 13
actual_tokens: 910137
actual_roles: "impl 7, review 6"
actual_role_tokens: "impl 654896, review 255241"
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

- `scripts/smoke.sh` schedule step; parameters by env as the existing steps (part `agents-schedule-smoke`).

## Expected outcome

`mise run smoke` covers the schedule service end to end with the real orchestrator.

## Steps

- Add the three tests; they fail.
- Add the step and cleanup; they pass.
- shellcheck clean.

## Notes

- The schedule is created disabled so it never fires on its own; only run-now starts a session.
- The orchestrator step's cleanup pattern (`cleanup` trap with manual line) is reused.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule
- Split 2026-10-25: depends_on `api-docs-and-openapi` stays satisfied by the epic blocker agents-schedule-microservice, which owns that task.

- 2026-10-25 done
