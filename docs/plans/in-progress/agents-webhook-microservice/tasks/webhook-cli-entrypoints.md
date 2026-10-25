---
title: webhook cli entrypoints
status: in-progress
repo: agents-webhook
value: each of the three processes and the migration runs from one image as its own command
files: [src/agents_webhook/cli.py, tests/test_cli.py]
verify: "uv run pytest tests/test_cli.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-ingest-http, webhook-dispatch-worker, webhook-ui-api]
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

# webhook cli entrypoints

## Requirement

Wire the subcommands (design D2). Paths are in code/agents-webhook.

- `agents-webhook migrate`: `run_migrations(settings.database_url, "agents_webhook.migrations")`, logs the applied names, exit 0.
- `agents-webhook ingest`: uvicorn on `http_host:http_port` serving `create_ingest_app`, proxy headers off, graceful shutdown.
- `agents-webhook api`: uvicorn serving `create_api_app` with an `OrchestratorClient`.
- `agents-webhook worker`: `run_service(run_worker(...))`.
- Bad settings: exit 78 with the SettingsError on stderr (as any-mcp and agent-orchestrator).
- `tests/test_cli.py`: help lists the four; `migrate` applies against the test DB; bad settings exit 78 naming the variable; `ingest` and `api` build their uvicorn config with the right app and `proxy_headers=False` (no server started).

## Acceptance conditions

- AC1: migrate applies the schema against a database [evidence: command:uv run pytest tests/test_cli.py -q -k migrate]
- AC2: ingest, api and worker start the right app or loop with proxy headers off [evidence: command:uv run pytest tests/test_cli.py -q -k config]
- AC3: bad settings exit 78 naming the variable [evidence: command:uv run pytest tests/test_cli.py -q -k settings]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/cli.py`
- `tests/test_cli.py`

## Interfaces

- Owns `webhook-cli`: `agents-webhook {migrate, ingest, api, worker}`, used by the chart and the e2e.

## Expected outcome

The image runs every process by subcommand.

## Steps

- Red: tests; run: fail. Green: implement; run the verify command.

## Notes

- Pattern: `code/agent-orchestrator/src/agent_orchestrator/cli.py` `build_uvicorn_config`, `_cmd_migrate`.
