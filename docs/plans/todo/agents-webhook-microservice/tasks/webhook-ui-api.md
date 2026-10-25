---
title: webhook ui api
status: todo
repo: agents-webhook
value: the UI and any headless client can list recent events and create and remove event-to-preset mappings
files: [src/agents_webhook/api/__init__.py, src/agents_webhook/api/app.py, src/agents_webhook/api/schemas.py, src/agents_webhook/api/routes.py, tests/test_api.py]
verify: "uv run pytest tests/test_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-event-store, webhook-prompt-render]
owns: [webhook-api]
uses: [webhook-events-schema, webhook-event-queue, webhook-mapping-match, webhook-prompt, agents-common-orchestrator-client, agents-common-fake-orchestrator]
model: ""
estimate: 6
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

# webhook ui api

## Requirement

The UI API under `/webhooks/api/v1` (design D7, D11, D12, D14). Paths are in code/agents-webhook.

- `api/app.py`: `create_api_app(settings, pool, client)` (FastAPI, `openapi_url="/webhooks/api/v1/openapi.json"`), routes only under `/webhooks/api/v1` plus `/healthz`, `/readyz`; error body `{error: {code, message}}` as agent-orchestrator.
- `api/schemas.py`: `EventView{id, received_at, updated_at, source, kind, action, repo, number, title, url, author, status, reason, dedup_key, deliveries, mapping_id, preset_id, cluster_id, cluster_slug, message_id, update_of, duplicate_of, started_at, finished_at}` (no payload), `EventDetail(EventView){payload, labels}`, `MappingIn{source, kind, repo?, labels?, preset_id, prompt_template?}`, `MappingView(MappingIn){id, created_at}`, `Meta{sources: {github, gitlab, grafana: bool configured}, limits: {max_in_progress, max_queue, max_body_bytes, run_timeout_seconds}, ingest_paths}`.
- `api/routes.py`:
  - `GET /webhooks/api/v1/events?status=&source=&limit=50(<=200)&before_id=` newest first -> `list[EventView]`.
  - `GET /webhooks/api/v1/events/{id}` -> `EventDetail`, 404 `not_found`.
  - `GET /webhooks/api/v1/mappings` -> `list[MappingView]`.
  - `POST /webhooks/api/v1/mappings` -> 201 `MappingView`; 422 `invalid_request` (field combos, unknown template placeholder via `prompt.validate_template`), 422 `unknown_preset` when `client.get_preset` is NotFound, 503 `orchestrator_unavailable`.
  - `DELETE /webhooks/api/v1/mappings/{id}` -> 204, 404 `not_found`.
  - `GET /webhooks/api/v1/meta` -> `Meta`.
- `tests/test_api.py` (DB fixture, FakeOrchestrator): each route and error; filters and pagination; creating a mapping from an ignored event's fields; deleting it; unknown preset; template validation; no route outside the prefix besides health; the payload is only in the detail view.

## Acceptance conditions

- AC1: recent events list newest first with status and source filters and pagination [evidence: command:uv run pytest tests/test_api.py -q -k events]
- AC2: mappings are created, listed and deleted, with the preset checked against the orchestrator [evidence: command:uv run pytest tests/test_api.py -q -k mappings]
- AC3: invalid mappings and unknown presets get 422 with the code [evidence: command:uv run pytest tests/test_api.py -q -k invalid]
- AC4: meta reports configured sources and limits [evidence: command:uv run pytest tests/test_api.py -q -k meta]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/api/__init__.py`
- `src/agents_webhook/api/app.py`
- `src/agents_webhook/api/schemas.py`
- `src/agents_webhook/api/routes.py`
- `tests/test_api.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
