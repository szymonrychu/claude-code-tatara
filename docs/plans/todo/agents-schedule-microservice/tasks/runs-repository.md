---
title: runs repository
status: todo
repo: agents-schedule
value: runs are inserted exactly once per fire and change state only through guarded transitions
files: [src/agents_schedule/db/runs.py, tests/test_runs_repo.py]
verify: "uv run --frozen pytest tests/test_runs_repo.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [schema-migrations]
owns: [sched-runs-repo]
uses: [sched-schema, sched-db-fixture, agents-common-lib]
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

# runs repository

## Requirement

Add `agents_schedule.db.runs` (design D3, D6, D8, D9; approval A3), every status change through the agents-common guarded transition (`UPDATE ... WHERE id = $1 AND status = $expected`, the pattern of `code/agent-orchestrator/src/agent_orchestrator/db/queue.py:_transition`):

- `insert_scheduled(conn, schedule_id, fire_time, status, reason=None) -> Run | None`: `INSERT ... ON CONFLICT (schedule_id, fire_time) DO NOTHING RETURNING`; None means the fire was already recorded. `status` is `new` or `ignored`.
- `insert_manual(conn, schedule_id, now, status, reason=None) -> Run` (fire_time = now, trigger manual).
- `last_scheduled_fire(conn, schedule_id) -> datetime | None`.
- `in_flight(conn, schedule_id) -> int`: runs in `new` or `in-progress`.
- `claim_next(conn, max_in_progress, max_per_schedule) -> Run | None`: the oldest `new` run by `(fire_time, created_at)`, `FOR UPDATE SKIP LOCKED`, only when the global `in-progress` count is below `max_in_progress` and its schedule has fewer than `max_per_schedule` runs `in-progress`.
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
