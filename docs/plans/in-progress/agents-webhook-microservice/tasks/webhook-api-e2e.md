---
title: webhook api e2e
status: in-progress
repo: agents-webhook
value: every webhook capability is proven headless through HTTP against the real processes
files: [tests/e2e/__init__.py, tests/e2e/conftest.py, tests/e2e/test_e2e_api.py]
verify: "uv run pytest tests/e2e -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-cli-entrypoints, webhook-openapi-readme, webhook-reuse-routing]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 15
expected_tokens: 1836811
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# webhook api e2e

## Requirement

API-only e2e for headless parity (design D14, user decision; re-plan 2026-10-25: endpoints with basic auth and agent reuse). Paths are in code/agents-webhook.

- `tests/e2e/conftest.py`: a testcontainers Postgres; `FakeOrchestrator` (agents-common v0.2.0) served by uvicorn on a free port with a token; `agents-webhook migrate`, then `ingest`, `api` and `worker` started as subprocesses of the installed console script with `WEBHOOK_*` env (short `poll_seconds`); torn down after the session.
- `tests/e2e/test_e2e_api.py`, all through HTTP to the two processes:
  - create a `github-pr` endpoint via the api with defaults -> the response has the URL, username and password; `GET /endpoints` has no password; a signed-in (basic auth) `pull_request` opened event -> 202 -> the api shows `new`, then `in-progress` with `cluster_slug wh-<id>`; the fake completes the turn -> `handled`.
  - each of the five types with a user-supplied suffix and credentials: its own event handled; a mismatched event `ignored`/`type_mismatch`; Grafana resolved `ignored`/`resolved`.
  - duplicate while `new` -> latest wins and a `duplicate` row; a redelivery with the same delivery id -> `duplicate`.
  - agent reuse: with a preset `spec.reuse_running_agent: true`, a comment on the same PR while the cluster runs -> `handled` on the same cluster (two messages on one fake cluster); after the fake discards the cluster, the next event starts a new cluster; with the flag off, the next event starts its own cluster.
  - `self_event`, `author_not_allowed`, `action_ignored`, `queue_full` (with `WEBHOOK_MAX_QUEUE=1`) listed with reasons.
  - caps: with `WEBHOOK_MAX_IN_PROGRESS=1`, two events on two endpoints -> one `in-progress`, one `new` until the first is handled.
  - failed: the fake fails the turn -> `failed`/`turn_failed`.
  - auth: wrong password and unknown suffix both 401 with the same body; 11 failures -> 429; rotate -> the old password 401, the new one 202; 6 MiB -> 413; delete -> later requests 401 and queued events `endpoint_removed`.
- `mise run test:e2e` runs it; CI's `e2e` job runs it.

## Acceptance conditions

- AC1: every endpoint type, auth path, dedup rule, ignore reason, limit, reuse path, endpoint operation and failure path is covered through HTTP only [evidence: command:uv run pytest tests/e2e -q]
- AC2: the e2e runs the real console script processes, not in-process apps [evidence: judgement:conftest starts agents-webhook subprocesses]
- AC3: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `tests/e2e/__init__.py`
- `tests/e2e/conftest.py`
- `tests/e2e/test_e2e_api.py`

## Interfaces

- Consumes `webhook-cli`, `webhook-api`, `webhook-ingest-url`, `agents-common-reuse`.

## Expected outcome

`mise run test:e2e` proves every capability through HTTP against the real processes.

## Steps

- Red: the e2e cases; run `uv run pytest tests/e2e -q`: fail where a capability is missing.
- Green: fix fixtures only (product code belongs to earlier tasks); run the verify command.

## Notes

- Keep timings bounded: every wait polls the api with a 30 s cap.
- Run the 429 case last or with its own client address, so it does not lock out the other cases.

- 2026-10-25 in-progress: re-plan 2026-10-25: added; not started
