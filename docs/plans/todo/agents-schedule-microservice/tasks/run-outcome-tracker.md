---
title: run outcome tracker
status: todo
repo: agents-schedule
value: "every in-progress run ends handled or failed with a reason, visible in the API and UI"
files: [src/agents_schedule/tracker.py, tests/test_tracker.py]
verify: "uv run --frozen pytest tests/test_tracker.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [runs-repository, schedule-settings-model]
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

# run outcome tracker

## Requirement

Add `agents_schedule.tracker` (design D10; approval A3) on agents-common `runs.track` and `OrchestratorClient` (contracts `preset-mapping-model`, `agents-common-lib`; reference poller `code/agent-orchestrator/bench/runner.py:_finished`).

- `track_once(pool, client, settings, now) -> int`: for each `in-progress` run with a `message_id`, `GET /api/v1/messages/{message_id}`: `turn.status = completed` -> `handled`, `finished_at = turn.completed_at`; message `failed` or `cancelled` -> `failed` reason `message_<status>`; `turn.status = failed` -> `failed` reason `turn_failed`; 404 -> `failed` reason `message_gone`; in progress longer than `SCHED_RUN_TIMEOUT_SECONDS` -> `failed` reason `timeout`; anything else leaves the run in-progress. Transient orchestrator errors leave it unchanged and are logged once per run per minute.
- Every change is the guarded `in-progress -> handled|failed` transition; a run already moved by another process is left alone.
- `run_tracker(pool, client, settings, stop)` loops every `SCHED_POLL_SECONDS`.
- The service never deletes clusters (gate Q8); cleanup is the preset's autoclose from configuration-improvements (contract `orch-cluster-autoclose`).

## Acceptance conditions

- AC1: a completed first turn marks the run handled with finished_at [evidence: test:tests/test_tracker.py::test_completed_turn_handled]
- AC2: failed or cancelled messages, failed turns and timeouts mark the run failed with the reason [evidence: test:tests/test_tracker.py::test_failures_have_reasons]
- AC3: a running turn or a transient error leaves the run in-progress [evidence: test:tests/test_tracker.py::test_running_unchanged]
- AC4: the tracker never calls DELETE on the orchestrator [evidence: test:tests/test_tracker.py::test_never_deletes_clusters]

## Files

- `src/agents_schedule/tracker.py`
- `tests/test_tracker.py`

## Interfaces

- `agents_schedule.tracker:track_once(pool, client, settings, now) -> int`, `run_tracker(pool, client, settings, stop) -> None` (part `sched-tracker`); consumes `agents_common.runs.track`.

## Expected outcome

Runs reach a terminal status that matches the orchestrator's view of their first turn.

## Steps

- Write tests/test_tracker.py against `agents_common.fake_orchestrator`; run: fails.
- Write tracker.py; `uv run --frozen pytest tests/test_tracker.py -q`: `4 passed`.
- Lint clean.

## Notes

- do-not-build: a turn-completion callback in the orchestrator; polling the message gives the outcome (`code/agent-orchestrator/src/agent_orchestrator/api/messages.py` L99).
