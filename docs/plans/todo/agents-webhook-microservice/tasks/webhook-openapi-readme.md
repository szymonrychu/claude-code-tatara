---
title: webhook openapi readme
status: todo
repo: agents-webhook
value: "the webhook API is documented and its committed schema cannot drift, so the UI and scripts can rely on it"
files: [src/agents_webhook/api/openapi.py, openapi.json, README.md, tests/test_readme_api.py]
verify: "uv run pytest tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-ui-api]
owns: []
uses: [webhook-api]
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
