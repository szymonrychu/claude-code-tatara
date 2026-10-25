---
title: webhook event store
status: todo
repo: agents-webhook
value: "events queue FIFO with latest-wins and update message dedup and the concurrency and queue limits, safe under concurrent deliveries"
files: [src/agents_webhook/db/events.py, tests/test_event_store.py]
verify: "uv run pytest tests/test_event_store.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-mappings-repo]
owns: [webhook-event-queue]
uses: [webhook-events-schema, agents-common-db, webhook-normalized-event, agents-common-run-tracker]
model: opus
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

# webhook event store

## Requirement

The event queue: recording deliveries with dedup, claiming under limits, guarded transitions (design D5, D6). Paths are in code/agents-webhook.

- `record(conn, event: NormalizedEvent, payload, *, mapping, ignore_reason, max_queue) -> Recorded{id, status, reason, duplicate_of, update_of}` in one transaction:
  1. `ignore_reason` set, or no mapping (`no_mapping`): insert `ignored` with the reason.
  2. Count of `new` rows >= `max_queue`: insert `ignored`, `queue_full`.
  3. `INSERT ... status 'new' ... ON CONFLICT (dedup_key) WHERE status IN ('new','in-progress') AND update_of IS NULL DO NOTHING RETURNING id`; inserted -> done.
  4. Else lock the live row (`SELECT ... FOR UPDATE`): if `new`, replace its payload, title, body, url, labels, `updated_at`, `deliveries+1` with `WHERE id=%s AND status='new'` and insert the delivery as `ignored`, `duplicate`, `duplicate_of`; if `in-progress`, insert an update message row (`status 'new'`, `update_of` = live id, copying its mapping and preset). If the live row left both statuses meanwhile, retry from 3, at most 3 times, then raise.
  Ignored rows still store the normalised fields and payload, so the UI lists them.
- `claim_next(conn, *, max_in_progress) -> Event | None`: in one transaction pick the update message `new` row whose parent has a `message_id`, else the oldest first-dispatch `new` row by `(priority, seq)` whose mapping has no in-progress row, only when the count of in-progress first-dispatch rows < `max_in_progress`; `FOR UPDATE SKIP LOCKED`; move it `new -> in-progress` with `started_at` via `agents_common.db.transition`. A `new` first-dispatch row whose `mapping_id` became null is moved `new -> ignored`, `mapping_removed` instead.
- `RunStore` implementation for `agents_common.runs`: `set_cluster`, `set_message` (`WHERE status='in-progress'`), `finish(id, status, reason)` (`in-progress -> handled|failed`, `finished_at`).
- `list_events(conn, *, status, source, limit, before_id)` newest first; `get_event(conn, id)`; `in_progress(conn)` for the tracker.
- `tests/test_event_store.py`: each step of record; latest-wins keeps `seq` and position; update message when in-progress; 20 concurrent `record` calls with one key from separate connections leave exactly one live row and the rest duplicates or update messages; the retry when the live row finishes mid-record; FIFO with alert priority; the overall cap and the per-mapping cap; mapping_removed; guarded transitions refuse wrong source statuses; two concurrent `claim_next` never return the same row.

## Acceptance conditions

- AC1: a duplicate of a new event replaces its payload, keeps its FIFO place and is listed as ignored duplicate [evidence: command:uv run pytest tests/test_event_store.py -q -k latest_wins]
- AC2: a duplicate of an in-progress event becomes an update message row [evidence: command:uv run pytest tests/test_event_store.py -q -k update_message]
- AC3: concurrent deliveries with one key leave exactly one live row [evidence: command:uv run pytest tests/test_event_store.py -q -k concurrent_record]
- AC4: claims are FIFO by priority then sequence and respect the overall and per-mapping caps [evidence: command:uv run pytest tests/test_event_store.py -q -k claim]
- AC5: the queue cap, no mapping and mapping removed produce ignored rows with those reasons [evidence: command:uv run pytest tests/test_event_store.py -q -k ignored]
- AC6: every status change is status-guarded [evidence: command:uv run pytest tests/test_event_store.py -q -k guarded]
- AC7: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/db/events.py`
- `tests/test_event_store.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
