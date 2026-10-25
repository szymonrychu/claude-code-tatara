---
title: webhook ui api
status: in-progress
repo: agents-webhook
value: the UI and any headless client can create, list, rotate and delete webhook endpoints and list recent events
files: [src/agents_webhook/api/__init__.py, src/agents_webhook/api/app.py, src/agents_webhook/api/schemas.py, src/agents_webhook/api/routes.py, tests/test_api.py]
verify: "uv run pytest tests/test_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-event-store, webhook-prompt-render]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# webhook ui api

## Requirement

The UI API under `/webhooks/api/v1` (design D7, D11, D12, D14, D17; re-plan 2026-10-25: the UI manages per-webhook endpoints, created with a type, a required preset, an optional suffix and optional credentials). Paths are in code/agents-webhook.

- `api/app.py`: `create_api_app(settings, pool, client)` (FastAPI, `openapi_url="/webhooks/api/v1/openapi.json"`), routes only under `/webhooks/api/v1` plus `/healthz`, `/readyz`; error body `{error: {code, message}}` as agent-orchestrator.
- `api/schemas.py`: `EndpointIn{type, preset_id, suffix?, username?, password?, prompt_template?}`, `EndpointView{id, suffix, url, type, preset_id, prompt_template, username, created_at, credentials_rotated_at}` (`url` = `public_base_url + "/webhook/" + suffix`; never a password or hash), `EndpointCreated(EndpointView){password}`, `RotateIn{username?, password?}`, `EventView{id, received_at, updated_at, endpoint_id, endpoint_suffix, type, source, kind, action, repo, number, title, url, author, status, reason, dedup_key, deliveries, preset_id, cluster_id, cluster_slug, message_id, update_of, duplicate_of, started_at, finished_at}` (no payload), `EventDetail(EventView){payload, labels}`, `Meta{public_base_url, ingest_path_prefix: "/webhook/", types: [grafana-alert, gitlab-issue, gitlab-mr, github-issue, github-pr], limits: {max_in_progress, max_in_progress_per_endpoint, max_queue, max_body_bytes, run_timeout_seconds, auth_failures_per_minute}}`.
- `api/routes.py`:
  - `GET /webhooks/api/v1/endpoints` -> `list[EndpointView]`.
  - `POST /webhooks/api/v1/endpoints` -> 201 `EndpointCreated` (the only response besides rotate that carries the password; header `Cache-Control: no-store`); 409 `suffix_taken`; 422 `invalid_request` (suffix pattern, password shorter than `min_password_length`, unknown template placeholder via `prompt.validate_template`); 422 `unknown_preset` when `client.get_preset` is NotFound; 503 `orchestrator_unavailable`.
  - `POST /webhooks/api/v1/endpoints/{id}/rotate` -> 200 `EndpointCreated` with new credentials (random unless given; `Cache-Control: no-store`), 404 `not_found`, 422 as above.
  - `DELETE /webhooks/api/v1/endpoints/{id}` -> 204, 404 `not_found`; past events stay listed.
  - `GET /webhooks/api/v1/events?status=&endpoint_id=&limit=50(<=200)&before_id=` newest first -> `list[EventView]`.
  - `GET /webhooks/api/v1/events/{id}` -> `EventDetail`, 404 `not_found`.
  - `GET /webhooks/api/v1/meta` -> `Meta`.
- Logs never carry a password, a hash or an Authorization header.
- `tests/test_api.py` (DB fixture, FakeOrchestrator): each route and error; create with defaults returns a random suffix, username and password and the full URL; create with a user suffix and credentials; a taken suffix 409; a short password 422; unknown preset 422; template validation; list and get never contain a password or hash; rotate returns new credentials and the old password stops authenticating (`endpoints.authenticate`); delete; event filters and pagination; no route outside the prefix besides health; the payload is only in the detail view.

## Acceptance conditions

- AC1: endpoints are created with a random or user-supplied unique suffix and credentials, and the full URL and password are returned only by create and rotate [evidence: command:uv run pytest tests/test_api.py -q -k endpoints]
- AC2: rotate replaces the credentials and delete removes the endpoint while its events stay listed [evidence: command:uv run pytest tests/test_api.py -q -k "rotate or delete"]
- AC3: invalid suffixes, short passwords, unknown placeholders and unknown presets get 4xx with the code [evidence: command:uv run pytest tests/test_api.py -q -k invalid]
- AC4: recent events list newest first with status and endpoint filters and pagination [evidence: command:uv run pytest tests/test_api.py -q -k events]
- AC5: meta reports the base URL, the ingest prefix, the types and the limits [evidence: command:uv run pytest tests/test_api.py -q -k meta]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/api/__init__.py`
- `src/agents_webhook/api/app.py`
- `src/agents_webhook/api/schemas.py`
- `src/agents_webhook/api/routes.py`
- `tests/test_api.py`

## Interfaces

- Owns `webhook-api` (cross-epic, consumer agents-web): `/webhooks/api/v1` endpoints (GET, POST, POST /{id}/rotate, DELETE /{id}), events (GET list, GET /{id}), meta; openapi.json committed by webhook-openapi-readme; vendored in agents-web as `openapi/webhooks.json`.

## Expected outcome

Everything the UI does is a documented HTTP call.

## Steps

- Red: tests; run: fail. Green: implement; run the verify command.

## Notes

- The api is the only writer of `endpoints`; it never writes `events`. A password leaves the service only in the create and rotate responses.

- 2026-10-25 amended: re-plan 2026-10-25: per-webhook endpoints (/webhook/<suffix>, one type, one preset, basic auth) replace per-source secrets and mappings; agent reuse is opt-in per preset (design D3, D7, D16-D19)

User requirement (2026-10-25), verbatim: "webhook configuration consists of jinja2 template for initial prompt. Jinja2 must include JSON parsing filter. it must be possible to provide an example JSON to check how Jinja templae compiles."
Orchestrator ruling for this task: endpoint create validates the template syntax with the shared renderer (422 naming `prompt_template` and the Jinja error line); add `POST /webhooks/api/v1/templates/preview` taking `{template, type, example}` (example = a JSON payload as the provider would send it; it is normalized for the given type, then rendered) and returning `{prompt}` or a 422 with the render error; preview never stores anything and is behind SSO like the rest of the UI API. Tests for both.
