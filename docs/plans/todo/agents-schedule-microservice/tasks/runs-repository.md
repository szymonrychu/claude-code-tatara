---
title: runs repository
status: todo
repo: agents-schedule
value: runs are inserted exactly once per fire and change state only through guarded transitions
files: [src/agents_schedule/db/runs.py, tests/test_runs_repo.py]
verify: "uv run --frozen pytest tests/test_runs_repo.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [schema-migrations]
model: ""
review: ""
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

# runs repository

## Requirement

Add `agents_schedule.db.runs` (design D3, D6, D8, D9; approval A3); every status change goes through agents-common `transition()` and the claim through its `claim()` with `FOR UPDATE SKIP LOCKED` (contract `agents-common-lib`):

- `insert_scheduled(conn, schedule_id, fire_time, status, reason=None) -> Run | None`: `INSERT ... ON CONFLICT (schedule_id, fire_time) DO NOTHING RETURNING`; None means the fire was already recorded. `status` is `new` or `ignored`.
- `insert_manual(conn, schedule_id, now, status, reason=None) -> Run` (fire_time = now, trigger manual).
- `last_scheduled_fire(conn, schedule_id) -> datetime | None`.
- `in_flight(conn, schedule_id) -> int`: runs in `new` or `in-progress`.
- `claim_next(conn, max_in_progress, max_per_schedule, now) -> Run | None`: moves the oldest `new` run by `(fire_time, created_at)` to `in-progress` (`started_at = now`), only when the global `in-progress` count is below `max_in_progress` and its schedule has fewer than `max_per_schedule` runs `in-progress`.
- `transition(conn, run_id, expected, new, **fields) -> bool` (False when the row was not in `expected`); `set_fields(conn, run_id, expected, **fields) -> bool` for `cluster_slug`, `cluster_id`, `message_id`, `attempts` without a status change.
- `list_for_schedule(conn, schedule_id, limit)`, `list_recent(conn, status=None, limit=50)`, `get(conn, run_id)`, `list_in_progress(conn)`.

## Acceptance conditions

- AC1: a second insert_scheduled for the same fire returns None and leaves one row [evidence: test:tests/test_runs_repo.py::test_insert_scheduled_once]
- AC2: a transition from a stale status changes nothing and returns False [evidence: test:tests/test_runs_repo.py::test_transition_is_status_guarded]
- AC3: claim_next honours the global and per-schedule caps and FIFO order [evidence: test:tests/test_runs_repo.py::test_claim_next_caps_and_fifo]
- AC4: two concurrent claimers never get the same run [evidence: test:tests/test_runs_repo.py::test_claim_skip_locked]
- AC5: last_scheduled_fire ignores manual runs [evidence: test:tests/test_runs_repo.py::test_last_scheduled_fire_ignores_manual]

## Files

- `src/agents_schedule/db/runs.py`
- `tests/test_runs_repo.py`

## Interfaces

- `agents_schedule.db.runs`: `Run` dataclass, the functions above (part `sched-runs-repo`).

## Expected outcome

The scheduler, dispatcher, tracker and api share one runs module whose writes are exactly-once and status-guarded.

## Steps

- Write tests/test_runs_repo.py; run: fails.
- Write runs.py; `uv run --frozen pytest tests/test_runs_repo.py -q`: `5 passed`.
- Lint clean.

## Notes

- `runs` is the only multi-writer table (api inserts manual runs, worker the rest), and every change is status-guarded (AGENTS.md hard rule).
