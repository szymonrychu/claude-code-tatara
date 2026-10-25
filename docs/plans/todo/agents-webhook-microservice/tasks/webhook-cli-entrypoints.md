---
title: webhook cli entrypoints
status: todo
repo: agents-webhook
value: each of the three processes and the migration runs from one image as its own command
files: [src/agents_webhook/cli.py, tests/test_cli.py]
verify: "uv run pytest tests/test_cli.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-ingest-http, webhook-dispatch-worker, webhook-ui-api]
owns: [webhook-cli]
uses: [agents-common-settings-runtime, webhook-ingest-api, webhook-api]
model: ""
estimate: 5
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
