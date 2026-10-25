---
title: webhook openapi readme
status: done
repo: agents-webhook
value: "the webhook API is documented and its committed schema cannot drift, so the UI and scripts can rely on it"
files: [src/agents_webhook/api/openapi.py, openapi.json, README.md, tests/test_readme_api.py]
verify: "uv run pytest tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-ui-api]
model: ""
review: ""
verified_head: caaa41a
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: 2
actual_minutes: 3
actual_tokens: 1087807
actual_roles: "impl 3, review 1"
actual_role_tokens: "impl 801839, review 285968"
---

# webhook openapi readme

## Requirement

Committed OpenAPI and the API reference (design D14). Paths are in code/agents-webhook.

- `api/openapi.py`: `python -m agents_webhook.api.openapi` prints the api app's OpenAPI JSON (sorted keys, stable), built without a DB.
- `openapi.json`: generated and committed.
- README `## API`: one `###` per route (method, path, body, response, errors) and a curl example for each, including how to call it headless through the SSO sidecar (a Keycloak bearer token, `SKIP_JWT_BEARER_TOKENS`) or by port-forward to the api container port.
- `tests/test_readme_api.py`: `openapi.json` equals the generated output (drift); every route in the app is documented in README `## API` (as `code/agent-orchestrator/tests/test_readme_api.py` L53, L65).

## Acceptance conditions

- AC1: openapi.json matches the app [evidence: command:uv run pytest tests/test_readme_api.py -q -k drift]
- AC2: every route is documented in README API [evidence: command:uv run pytest tests/test_readme_api.py -q -k documented]
- AC3: README has the API section [evidence: doc-section:README.md#API]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/api/openapi.py`
- `openapi.json`
- `README.md`
- `tests/test_readme_api.py`

## Interfaces

- `openapi.json` is vendored by agents-web (web-webhook-api-client).

## Expected outcome

The API is documented and drift-tested.

## Steps

- Red: tests; run: fail. Green: generator, `python -m agents_webhook.api.openapi > openapi.json`, README; run the verify command.

## Notes

- Pattern: `code/agent-orchestrator/src/agent_orchestrator/api/openapi.py`, `tests/test_readme_api.py`.

User requirement (2026-10-25), verbatim: "webhook configuration consists of jinja2 template for initial prompt. Jinja2 must include JSON parsing filter. it must be possible to provide an example JSON to check how Jinja templae compiles."
Orchestrator ruling for this task: document the template language (sandboxed Jinja2, the `from_json` filter, the context variables per type, `template_error`) and the preview route in README and openapi.

- 2026-10-25 done
