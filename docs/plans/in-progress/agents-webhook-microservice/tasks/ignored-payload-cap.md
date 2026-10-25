---
title: ignored payload cap
status: done
repo: agents-webhook
value: ignored webhook deliveries cannot grow the database without bound
files: [src/agents_webhook/db/events.py, tests/test_event_store.py]
verify: "uv run pytest tests/test_event_store.py -o addopts= -q && uv run ruff check ."
depends_on: [webhook-reuse-routing]
model: ""
review: ""
verified_head: 2a7c246
points: 1
expected_minutes: 5
expected_tokens: 702990
points_actual: 1
actual_minutes: 2
actual_tokens: 351351
actual_roles: impl 2
actual_role_tokens: impl 351351
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

Ignored rows hold a payload of at most about 4 KiB; new rows keep the full payload; the events list still shows the reason.

## Steps

- Write `test_ignored_rows_store_truncated_payload` (each ignored path) and a new-row full-payload assertion; run `uv run pytest tests/test_event_store.py -o addopts= -q -k truncated`: fails.
- Truncate ignored payloads in db/events.py record(); rerun: passes.
- Run the verify command: tests pass, ruff clean.

## Notes

Origin: ingest security review 2026-10-25 (scratchpad wh-sec-ingest.md). DB tests use the local Postgres at postgresql://test@127.0.0.1:55433/postgres via a temporary, uncommitted pg_url override.

- 2026-10-25 done
