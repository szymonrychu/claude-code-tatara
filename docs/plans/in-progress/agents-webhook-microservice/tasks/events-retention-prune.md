---
title: events retention prune
status: todo
repo: agents-webhook
value: the events table stays bounded by the retention window
files: [src/agents_webhook/worker.py, src/agents_webhook/db/events.py, tests/test_worker.py]
verify: "uv run pytest tests/test_worker.py -o addopts= -q -k retention && uv run ruff check ."
depends_on: []
model: ""
review: ""
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 538938
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# events retention prune

## Requirement

Discovered by webhook-docs-memory (2026-10-25): WEBHOOK_EVENTS_RETENTION_DAYS (default 30) is declared in settings but nothing prunes events, so the events table grows without bound. The worker (the single writer that already holds the singleton lock) deletes events in a final state (handled, ignored, failed) whose last update is older than the retention, in bounded batches (e.g. 1000 rows per statement) at most once an hour, never touching new or in-progress rows and never a row another row references through update_of/duplicate_of unless that row is also pruned (or null the reference). Log the count. Tests: old final rows pruned, recent and in-flight rows kept, references handled, batch bound.

## Acceptance conditions

- AC1: final events older than the retention are pruned in bounded batches; new, in-progress and recent rows are kept [evidence: test:tests/test_worker.py::test_retention_prunes_old_final_events]
- AC2: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/worker.py`
- `src/agents_webhook/db/events.py`
- `tests/test_worker.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
