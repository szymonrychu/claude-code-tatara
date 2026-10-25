---
title: webhook dispatch worker
status: in-progress
repo: agents-webhook
value: queued events start clusters from their presets one by one within the limits and end handled or failed
files: [src/agents_webhook/worker.py, tests/test_worker.py]
verify: "uv run pytest tests/test_worker.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-event-store, webhook-prompt-render]
model: opus
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

# webhook dispatch worker

## Requirement

The singleton worker: dispatch and tracking (design D6, D8). Paths are in code/agents-webhook.

- `worker.py`: `async run_worker(settings, pool, client)` holds `agents_common.runtime.advisory_singleton(pool, "agents-webhook-worker")` and loops every `poll_seconds` or on NOTIFY `webhook_events`:
  1. Resume: every `in-progress` row without `message_id` is dispatched again (crash recovery) before new claims.
  2. Claim with `events.claim_next(max_in_progress)` until it returns None; a first-dispatch row: `runs.dispatch(client, store, RunRef(slug="wh-<id>", ...), prompt.render(event, row.prompt_template), runs.marker("webhook:event", id))`; an update message row: `runs.post_update` to the parent's `cluster_id` with `render(..., update=True)`, then `finish(handled)`.
  3. Track: for each `in-progress` row with `message_id`, `runs.track(..., timeout_seconds=run_timeout_seconds)`.
  4. `OrchestratorUnavailable` leaves the row as it is and is retried next tick (logged once per row per minute); `OrchestratorError` 4xx on create or post -> `finish(failed, "<code>")`.
  5. On `LostLock` the loop stops claiming and exits non-zero (the Deployment restarts it).
- `tests/test_worker.py` with the DB fixture and `FakeOrchestrator` in-process: happy path new -> in-progress -> handled with `cluster_id`, `cluster_slug wh-<id>`, `message_id`; the prompt posted is the rendered one with the marker; the caps (4 mapped events, cap 3 -> the 4th waits until one finishes; 2 events of one mapping run one after the other); an update message reaches the same cluster and is handled; a crash after create and after post resumes without a second cluster or message; failed paths (preset missing 404, turn failed, timeout); orchestrator down -> rows untouched, then recover; two workers -> only one dispatches.

## Acceptance conditions

- AC1: a mapped event creates cluster wh-<id>, posts the rendered prompt and ends handled when the first turn completes [evidence: command:uv run pytest tests/test_worker.py -q -k happy]
- AC2: at most max_in_progress events and one per mapping run at once, the rest wait FIFO [evidence: command:uv run pytest tests/test_worker.py -q -k caps]
- AC3: an update message is posted to the running cluster and ends handled [evidence: command:uv run pytest tests/test_worker.py -q -k update_message]
- AC4: a restart after create or after post never creates a second cluster or posts a second prompt [evidence: command:uv run pytest tests/test_worker.py -q -k restart]
- AC5: a missing preset, a failed turn and a timeout end failed with the reason; an unavailable orchestrator leaves rows for retry [evidence: command:uv run pytest tests/test_worker.py -q -k failed]
- AC6: only one worker dispatches at a time [evidence: command:uv run pytest tests/test_worker.py -q -k singleton]
- AC7: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/worker.py`
- `tests/test_worker.py`

## Interfaces

- `agents_webhook.worker.run_worker(settings, pool, client)`; wired as `agents-webhook worker` by webhook-cli-entrypoints.

## Expected outcome

Queued mapped events run as agent clusters within the limits and end handled or failed.

## Steps

- Red: tests with the fake orchestrator; run: fail. Green: implement; run the verify command.

## Notes

- Never delete clusters (D8, non-goal). The service token goes in `WEBHOOK_ORCHESTRATOR_TOKEN`; the URL is the orchestrator's services Service.
