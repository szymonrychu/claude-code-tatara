---
title: scheduler loop
status: todo
repo: agents-schedule
value: "enabled schedules fire on time, once per fire time, with missed runs collapsed and overlaps recorded"
files: [src/agents_schedule/scheduler.py, tests/test_scheduler.py]
verify: "uv run --frozen pytest tests/test_scheduler.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [cron-expressions, schedules-repository, runs-repository]
owns: [sched-scheduler]
uses: [sched-cron, sched-schedules-repo, sched-runs-repo]
model: opus
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

# scheduler loop

## Requirement

Add `agents_schedule.scheduler` (design D5, D6, D9; approval A3). `tick(pool, settings, now) -> TickResult` runs one pass; `run_scheduler(pool, settings, stop)` loops it.

- For each enabled schedule: `stamp = max(last_scheduled_fire, armed_at)`; `cron.due(expr, tz, stamp, now)`. Nothing due: skip. Due: in one transaction, when `in_flight(schedule) >= SCHED_MAX_PER_SCHEDULE` insert the run as `ignored` with reason `previous_running`, else as `new`. Either insert advances the stamp, because the stamp is the latest scheduled fire time (tatara-new: the stamp advances even when a run is skipped).
- `skipped > 0` logs one line per schedule `missed <n> fire times of <name> before <fire_time>` and creates no rows for them (one catch-up run, gate Q2).
- Exactly once: the insert is keyed on `(schedule_id, fire_time)`, so a restart or a second process re-running the same tick never creates a second row; `run_scheduler` runs only under the advisory singleton (`service-entrypoints`).
- Wake-up: sleep until the earliest next fire time over enabled schedules or `SCHED_TICK_SECONDS`, whichever is sooner, and wake early on the agents-common LISTEN channel `schedules_changed` when the api notifies it (if the library has no LISTEN helper, the tick interval alone is the bound).
- One schedule failing (bad stored cron after a library upgrade) logs and is skipped; the others still fire.

## Acceptance conditions

- AC1: a due schedule gets one new run at the fire time [evidence: test:tests/test_scheduler.py::test_due_schedule_creates_new_run]
- AC2: running the same tick twice, or from two connections at once, creates one row [evidence: test:tests/test_scheduler.py::test_tick_is_exactly_once]
- AC3: after downtime over several fire times one run is created for the latest and the rest are logged [evidence: test:tests/test_scheduler.py::test_missed_runs_collapse]
- AC4: a fire while the previous run is in flight is recorded ignored previous_running and the stamp advances [evidence: test:tests/test_scheduler.py::test_overlap_recorded_ignored_and_stamp_advances]
- AC5: disabled schedules and a re-enabled schedule's disabled period never fire [evidence: test:tests/test_scheduler.py::test_disabled_and_rearmed]
- AC6: one broken schedule does not stop the others [evidence: test:tests/test_scheduler.py::test_bad_schedule_isolated]

## Files

- `src/agents_schedule/scheduler.py`
- `tests/test_scheduler.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
