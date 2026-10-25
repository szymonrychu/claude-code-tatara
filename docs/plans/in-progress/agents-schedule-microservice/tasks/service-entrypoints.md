---
title: service entrypoints
status: in-progress
repo: agents-schedule
value: "the image runs as three commands, and only one worker ever fires schedules"
files: [src/agents_schedule/cli.py, src/agents_schedule/runtime.py, tests/test_entrypoints.py]
verify: "uv run --frozen pytest tests/test_entrypoints.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [scheduler-loop, run-dispatcher, run-outcome-tracker, runs-api-routes]
model: ""
review: full
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# service entrypoints

## Requirement

Register the service commands (design D9, D13; approval A1) through `sched-cli`, on agents-common `runtime.run_service` and `runtime.advisory_singleton` (contract `agents-common-lib`):

- `sched migrate`: runs `db.migrate.migrate`, exits 0, prints applied file names.
- `sched api`: uvicorn on `SCHED_PORT` serving `create_app`.
- `sched worker`: under the advisory singleton lock `agents-schedule-worker` runs `run_scheduler`, `run_dispatcher` and `run_tracker` concurrently; a second worker process waits for the lock and takes over when the first dies (heartbeat loss); SIGTERM stops all three and releases the lock.
- A bad configuration exits 78 with the SettingsError lines.

## Acceptance conditions

- AC1: sched migrate applies the schema and exits 0 [evidence: test:tests/test_entrypoints.py::test_migrate_command]
- AC2: two worker processes against one database: only the lock holder fires a due schedule [evidence: test:tests/test_entrypoints.py::test_single_worker_fires]
- AC3: the standby worker takes over after the holder stops [evidence: test:tests/test_entrypoints.py::test_standby_takes_over]
- AC4: a bad configuration exits 78 naming the variable [evidence: test:tests/test_entrypoints.py::test_bad_config_exits_78]
- AC5: sched --help lists migrate, api and worker [evidence: command:uv run sched --help | grep -q worker]

## Files

- `src/agents_schedule/cli.py`
- `src/agents_schedule/runtime.py`
- `tests/test_entrypoints.py`

## Interfaces

- Commands `sched migrate`, `sched api`, `sched worker` (part `sched-entrypoints`); `agents_schedule.runtime:worker_main(settings) -> int`, `api_main(settings) -> int`.

## Expected outcome

The image's three commands run the service; firing is single-instance with failover.

## Steps

- Write tests/test_entrypoints.py; run: fails.
- Write runtime.py and register the commands in cli.py; `uv run --frozen pytest tests/test_entrypoints.py -q`: `4 passed`.
- Lint clean.

## Notes

- The singleton plus the unique `(schedule_id, fire_time)` key together make a double fire impossible (design D9).
