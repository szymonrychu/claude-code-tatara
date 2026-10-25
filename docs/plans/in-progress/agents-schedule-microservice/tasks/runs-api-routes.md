---
title: runs api routes
status: in-progress
repo: agents-schedule
value: run history and run now are available over HTTP for every schedule
files: [src/agents_schedule/api/runs.py, src/agents_schedule/api/app.py, src/agents_schedule/api/schemas.py, tests/test_api_runs.py]
verify: "uv run --frozen pytest tests/test_api_runs.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [schedules-api-routes]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# runs api routes

## Requirement

Add the run routes under `/schedules/api/v1` (design D6, D11; approvals A3, A5):

- `POST /schedules/{id}/run` -> 202 `RunView`: inserts a manual run (`trigger manual`, `fire_time` now) as `new`, or as `ignored` with reason `previous_running` when the schedule already has `SCHED_MAX_PER_SCHEDULE` runs in flight (same rule as a scheduled fire, so history shows it). Allowed on a disabled schedule (my call, design D11). Notifies the dispatcher.
- `GET /schedules/{id}/runs?limit=20` (1..100, newest first); `GET /runs?status=&limit=50` (1..200, newest first, status filter one of the five); `GET /runs/{id}`.
- 404 `not_found` for a missing schedule or run; 422 `invalid_request` for a bad limit or status.

## Acceptance conditions

- AC1: run now creates a manual new run and answers 202 [evidence: test:tests/test_api_runs.py::test_run_now_creates_manual_run]
- AC2: run now while a run is in flight records ignored previous_running [evidence: test:tests/test_api_runs.py::test_run_now_overlap_ignored]
- AC3: per-schedule and global run lists are newest first, limited and filtered [evidence: test:tests/test_api_runs.py::test_run_lists]
- AC4: missing ids answer 404 and bad parameters 422 [evidence: test:tests/test_api_runs.py::test_run_errors]

## Files

- `src/agents_schedule/api/runs.py`
- `src/agents_schedule/api/app.py`
- `src/agents_schedule/api/schemas.py`
- `tests/test_api_runs.py`

## Interfaces

- Router `agents_schedule.api.runs:router` included by `create_app`; `RunView` from `api/schemas.py` (part `sched-runs-api`).

## Expected outcome

Every run and the run-now control are reachable headlessly.

## Steps

- Write tests/test_api_runs.py; run: fails.
- Write runs.py and include it in app.py; `uv run --frozen pytest tests/test_api_runs.py -q`: `4 passed`.
- Lint clean.

## Notes

- The api inserts only `new` or `ignored` manual runs; the worker moves them on.
