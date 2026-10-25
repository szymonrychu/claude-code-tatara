---
title: run outcome tracker
status: todo
repo: agents-schedule
value: "every in-progress run ends handled or failed with a reason, visible in the API and UI"
files: [src/agents_schedule/tracker.py, tests/test_tracker.py]
verify: "uv run --frozen pytest tests/test_tracker.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [runs-repository, schedule-settings-model]
owns: [sched-tracker]
uses: [sched-runs-repo, agents-common-lib, orch-service-tokens]
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

# run outcome tracker

## Requirement

Add `agents_schedule.tracker` (design D10; approval A3) on the agents-common run tracker and orchestrator client (contract `agents-common-lib`; reference poller `code/agent-orchestrator/bench/runner.py:_finished`).

- `track_once(pool, client) -> int`: for each `in-progress` run, `GET /api/v1/messages/{message_id}`: `turn.status = completed` -> `handled`, `finished_at = turn.completed_at`; message `failed` or `cancelled` -> `failed` reason `message_<status>`; `turn.status = failed` -> `failed` reason `turn_failed`; 404 -> `failed` reason `message_gone`; anything else leaves the run in-progress. Transient orchestrator errors leave it unchanged and are logged once per run per minute.
- Every change is the guarded `in-progress -> handled|failed` transition; a run already moved by another process is left alone.
- `run_tracker(pool, client, settings, stop)` loops every `SCHED_POLL_SECONDS`.
- The service never deletes clusters (gate Q8); cleanup is the preset's autoclose from configuration-improvements.

## Acceptance conditions

- AC1: a completed first turn marks the run handled with finished_at [evidence: test:tests/test_tracker.py::test_completed_turn_handled]
- AC2: failed or cancelled messages and failed turns mark the run failed with the reason [evidence: test:tests/test_tracker.py::test_failures_have_reasons]
- AC3: a running turn or a transient error leaves the run in-progress [evidence: test:tests/test_tracker.py::test_running_unchanged]
- AC4: the tracker never calls DELETE on the orchestrator [evidence: test:tests/test_tracker.py::test_never_deletes_clusters]

## Files

- `src/agents_schedule/tracker.py`
- `tests/test_tracker.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
