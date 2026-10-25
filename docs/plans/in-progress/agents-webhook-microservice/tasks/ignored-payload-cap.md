---
title: ignored payload cap
status: todo
repo: agents-webhook
value: ignored webhook deliveries cannot grow the database without bound
files: [src/agents_webhook/db/events.py, tests/test_event_store.py]
verify: "uv run pytest tests/test_event_store.py -o addopts= -q && uv run ruff check ."
depends_on: [webhook-reuse-routing]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 702990
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# ignored payload cap

## Requirement

Security review of ingest (2026-10-25): ignored events (type mismatch, unsupported, action ignored, duplicate, redelivery, endpoint removed) are stored with their full payload (up to the 5 MiB body cap) and are not counted against any cap, so a credential holder can grow the DB without bound until retention. In agents-webhook db/events.py record(): for rows stored as `ignored`, keep only the normalized fields plus a payload truncated to 4 KiB (a JSON object `{"truncated": true, "size": <bytes>, "head": "<first 4096 chars>"}`), and keep full payloads only for `new` rows. The UI events list must still show the reason. Tests for each ignored path storing a truncated payload and new rows keeping the full one.

## Acceptance conditions

- AC1: ignored rows store a truncated payload, new rows keep the full payload [evidence: test:tests/test_event_store.py::test_ignored_rows_store_truncated_payload]
- AC2: the suite and lint pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

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

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
