---
title: webhook event store
status: done
repo: agents-webhook
value: "events queue FIFO per endpoint with dedup, limits and per-key order, ready for agent reuse"
files: [src/agents_webhook/db/events.py, tests/test_event_store.py]
verify: "uv run pytest tests/test_event_store.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-endpoints-repo, webhook-normalize]
model: opus
review: full
verified_head: 6c068c7
points: 5
expected_minutes: 15
expected_tokens: 1836811
points_actual: 5
actual_minutes: 11
actual_tokens: 2885184
actual_roles: "impl 10, review 5"
actual_role_tokens: "impl 2108921, review 776263"
---

# webhook event store

## Requirement

The event queue: recording deliveries with dedup, claiming under limits with per-key order, guarded transitions (design D5, D6, D16; re-plan 2026-10-25: events belong to an endpoint, keys are per endpoint, reuse is decided by the worker). Paths are in code/agents-webhook.

- `record(conn, endpoint, event: NormalizedEvent, payload, *, ignore_reason, max_queue) -> Recorded{id, status, reason, duplicate_of}` in one transaction; every row copies `endpoint_id`, `endpoint_suffix`, `type`, `preset_id` and `prompt_template` from the endpoint:
  1. `ignore_reason` set (`type_mismatch`, `unsupported_event`, `self_event`, `author_not_allowed`, `action_ignored`, `resolved`): insert `ignored` with the reason.
  2. `delivery_id` already recorded for this endpoint: insert `ignored`, `duplicate`, `duplicate_of` the first row (provider redelivery).
  3. Count of `new` rows >= `max_queue`: insert `ignored`, `queue_full`.
  4. `INSERT ... status 'new' ... ON CONFLICT (endpoint_id, dedup_key) WHERE status = 'new' DO NOTHING RETURNING id`; inserted -> done.
  5. Else lock the `new` row (`SELECT ... FOR UPDATE`), replace its payload, title, body, url, labels, `updated_at`, `deliveries+1` with `WHERE id=%s AND status='new'` (latest wins, it keeps its `seq`) and insert the delivery as `ignored`, `duplicate`, `duplicate_of`. If the row was claimed meanwhile, retry from 4, at most 3 times, then raise.
  Ignored rows still store the normalised fields and payload, so the UI lists them.
- `claim_next(conn, *, max_in_progress, max_per_endpoint, reuse_endpoints: set[int]) -> Claimed{event, prior: Event | None} | None`: in one transaction, `FOR UPDATE SKIP LOCKED`, the oldest `new` row by `(priority, seq)` that is eligible:
  - per key order: no same-endpoint same-key row is `in-progress` and still without `cluster_id`, and no same-key update row (`update_of` set) is `in-progress`; for an endpoint not in `reuse_endpoints`, no same-key row is `in-progress` at all;
  - `prior` = the newest same-key first-dispatch row with a `cluster_id` (`latest_run`); a row of a `reuse_endpoints` endpoint with a `prior` is a reuse candidate and bypasses the caps; any other row needs fewer than `max_in_progress` in-progress first-dispatch rows overall and fewer than `max_per_endpoint` on its endpoint.
  It moves the row `new -> in-progress` with `started_at` via `agents_common.db.transition`. A `new` row whose `endpoint_id` became null is moved `new -> ignored`, `endpoint_removed` instead.
- `mark_update(conn, id, parent_id)` (sets `update_of`, guarded `in-progress`), `clear_update(conn, id)`, `release(conn, id)` (`in-progress -> new`, keeps `seq`, clears `started_at`; used when a reuse candidate must fall back while the caps are full).
- `RunStore` implementation for `agents_common.runs`: `set_cluster`, `set_message` (`WHERE status='in-progress'`), `finish(id, status, reason)` (`in-progress -> handled|failed`, `finished_at`).
- `list_events(conn, *, status, endpoint_id, limit, before_id)` newest first; `get_event(conn, id)`; `in_progress(conn)` for the tracker; `latest_run(conn, endpoint_id, dedup_key)`.
- `tests/test_event_store.py`: each step of record; redelivery by delivery id; latest-wins keeps `seq` and position; the same key on two endpoints is two rows; 20 concurrent `record` calls with one key from separate connections leave exactly one `new` row and the rest duplicates; the retry when the row is claimed mid-record; FIFO with alert priority; the overall and per-endpoint caps; per-key order with and without reuse; a reuse candidate bypasses full caps; `prior` is the newest run with a cluster; release keeps the FIFO place; endpoint_removed; guarded transitions refuse wrong source statuses; two concurrent `claim_next` never return the same row.

## Acceptance conditions

- AC1: a duplicate of a new event replaces its payload, keeps its FIFO place and is listed as ignored duplicate, and provider redeliveries are ignored [evidence: command:uv run pytest tests/test_event_store.py -q -k "latest_wins or redelivery"]
- AC2: concurrent deliveries with one key leave exactly one new row per endpoint [evidence: command:uv run pytest tests/test_event_store.py -q -k concurrent_record]
- AC3: claims are FIFO by priority then sequence, respect the overall and per-endpoint caps and keep per-key order [evidence: command:uv run pytest tests/test_event_store.py -q -k claim]
- AC4: a reuse candidate carries its prior run, bypasses full caps and can be released keeping its place [evidence: command:uv run pytest tests/test_event_store.py -q -k reuse]
- AC5: the queue cap and a removed endpoint produce ignored rows with those reasons [evidence: command:uv run pytest tests/test_event_store.py -q -k ignored]
- AC6: every status change is status-guarded [evidence: command:uv run pytest tests/test_event_store.py -q -k guarded]
- AC7: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/db/events.py`
- `tests/test_event_store.py`

## Interfaces

- Owns `webhook-event-queue`: `agents_webhook.db.events.{record, Recorded, claim_next, Claimed, Event, mark_update, clear_update, release, latest_run, EventStore (RunStore), list_events, get_event, in_progress}`.
- Implements `agents_common.runs.RunStore`.

## Expected outcome

Deliveries are stored per endpoint with dedup, and the worker claims them FIFO under the caps in per-key order with the prior run attached.

## Steps

- Red: `tests/test_event_store.py`; run `uv run pytest tests/test_event_store.py -q`: fail.
- Green: record, then claim_next and the transitions; run the verify command.

## Notes

- Multi-writer queue table: ingest inserts and replaces `new` payloads, the worker transitions; every UPDATE carries `AND status=<expected>` (hard rule). Pattern: `code/agent-orchestrator/src/agent_orchestrator/db/queue.py` header L1-9, `_PICK` L196-209.

- 2026-10-25 in-progress: re-plan 2026-10-25: added; not started

- 2026-10-25 done
