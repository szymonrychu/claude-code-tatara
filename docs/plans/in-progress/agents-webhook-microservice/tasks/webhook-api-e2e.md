---
title: webhook api e2e
status: in-progress
repo: agents-webhook
value: "every capability is proven end to end through HTTP only, without the UI"
files: [tests/e2e/__init__.py, tests/e2e/conftest.py, tests/e2e/test_e2e_api.py]
verify: "uv run pytest tests/e2e -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-cli-entrypoints, webhook-openapi-readme]
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

# webhook api e2e

## Requirement

API-only e2e for headless parity (design D14, user decision). Paths are in code/agents-webhook.

- `tests/e2e/conftest.py`: a testcontainers Postgres; `FakeOrchestrator` served by uvicorn on a free port with a token; `agents-webhook migrate`, then `ingest`, `api` and `worker` started as subprocesses of the installed console script with `WEBHOOK_*` env (short `poll_seconds`); torn down after the session.
- `tests/e2e/test_e2e_api.py`, all through HTTP to the two processes:
  - create a mapping via the api (github mr, repo X, preset P); a signed GitHub `pull_request` opened event -> 202 -> the api shows `new`, then `in-progress` with `cluster_slug wh-<id>`; the fake completes the turn -> `handled`.
  - GitHub issue and comment, GitLab MR, issue and note, Grafana firing: each mapped event handled; Grafana resolved `ignored`/`resolved`.
  - duplicate while `new` (worker paused by cap 0 via a second preset mapping held in progress) -> latest wins and a `duplicate` row; duplicate while `in-progress` -> update message `handled` on the same cluster (the fake shows two messages on one cluster).
  - `no_mapping`, `self_event`, `author_not_allowed`, `action_ignored`, `queue_full` (with `WEBHOOK_MAX_QUEUE=1`) listed with reasons.
  - caps: with `WEBHOOK_MAX_IN_PROGRESS=1`, two mapped events -> one `in-progress`, one `new` until the first is handled.
  - failed: the fake fails the turn -> `failed`/`turn_failed`.
  - bad signature 401, unconfigured source 404, 6 MiB 413; mapping delete -> later events `no_mapping`.
- `mise run test:e2e` runs it; CI's `e2e` job runs it.

## Acceptance conditions

- AC1: every source, dedup rule, ignore reason, limit, mapping operation and failure path is covered through HTTP only [evidence: command:uv run pytest tests/e2e -q]
- AC2: the e2e runs the real console script processes, not in-process apps [evidence: judgement:conftest starts agents-webhook subprocesses]
- AC3: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `tests/e2e/__init__.py`
- `tests/e2e/conftest.py`
- `tests/e2e/test_e2e_api.py`

## Interfaces

- Uses `webhook-cli`, `webhook-api`, `webhook-ingest-api`, `agents-common-fake-orchestrator`.

## Expected outcome

`mise run test:e2e` proves headless parity for every capability.

## Steps

- Red: write the e2e; run it against the wired processes; fix gaps it finds in the owning modules only through this task's diff if trivial, else name them.
- Run the verify command.

## Notes

- Keep timings bounded: every wait polls the api with a 30 s cap.
