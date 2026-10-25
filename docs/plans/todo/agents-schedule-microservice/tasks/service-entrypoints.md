---
title: service entrypoints
status: todo
repo: agents-schedule
value: "the image runs as three commands, and only one worker ever fires schedules"
files: [src/agents_schedule/cli.py, src/agents_schedule/runtime.py, tests/test_entrypoints.py]
verify: "uv run --frozen pytest tests/test_entrypoints.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [scheduler-loop, run-dispatcher, run-outcome-tracker, runs-api-routes]
owns: [sched-entrypoints]
uses: [sched-cli, sched-scheduler, sched-dispatch, sched-tracker, sched-api-app, agents-common-lib]
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# service entrypoints

## Requirement

Register the service commands (design D9, D13; approval A1) through `sched-cli`, on agents-common `run_service` and `advisory_singleton` (patterns `code/agent-orchestrator/src/agent_orchestrator/runtime/run.py:run_service`, `runtime/singleton.py:advisory_singleton`):

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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
