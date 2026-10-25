---
title: mxc service entrypoints
status: done
repo: agents-matrix-connector
value: "the connector runs as a migrate step, an API and one singleton bot that refuses a wrong identity"
files: [src/agents_matrix_connector/cli.py, src/agents_matrix_connector/bot.py, tests/test_cli.py, tests/test_bot_process.py]
verify: "uv run --frozen pytest tests/test_cli.py tests/test_bot_process.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [matrix-sync-loop, dispatch-worker, reply-tracker, api-rules-and-settings]
model: sonnet
review: full
verified_head: f9e1156b903abad4cf6735f7e91dcc8f2e703928
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: 3
actual_minutes: 5
actual_tokens: 1275430
actual_roles: "impl 5, review 2"
actual_role_tokens: "impl 1008403, review 267027"
---

# mxc service entrypoints

## Requirement

Wire the `migrate`, `api` and `bot` subcommands (design D1, D2, D5). Paths are in code/agents-matrix-connector.

- `src/agents_matrix_connector/cli.py`: `SUBCOMMANDS` gains `migrate` (apply migrations), `api` (run the UI API) and `bot` (run sync, worker and tracker); settings errors exit 78 (`EXIT_BAD_SETTINGS`) with every bad `MATRIX_*` variable named on stderr; `migrate` runs `run_migrations(url, "agents_matrix_connector.migrations")` with `ConnectorSettings` minus orchestrator and Matrix requirements (a `MigrateSettings` with only the database URL required); `api` serves `create_api_app` with uvicorn on `MATRIX_HTTP_HOST:MATRIX_HTTP_PORT` through `agents_common.runtime.run_service`.
- `src/agents_matrix_connector/bot.py`: `async run_bot(settings: BotSettings) -> int`: opens the pool, the orchestrator client and the Matrix client; `whoami` must equal `MATRIX_USER_ID` (else log and return 78); holds `agents_common.runtime.advisory_singleton("agents-matrix-connector-bot")`; runs `SyncLoop.run` and a loop calling `Worker.tick` then `Tracker.tick` every `MATRIX_POLL_SECONDS` as tasks of one event loop; serves `/healthz` (process up) and `/readyz` (200 when `SyncLoop.last_sync_at` is within three times `MATRIX_SYNC_TIMEOUT_SECONDS`, else 503) on `MATRIX_HTTP_PORT`; a `MatrixAuthError` or a lost lock stops everything and returns 1 with a log line naming the cause (never the token); SIGTERM stops cleanly within `MATRIX_SHUTDOWN_GRACE_SECONDS`.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: --help lists migrate, api and bot, and a bad setting exits 78 naming the variable [evidence: test:tests/test_cli.py::test_subcommands_and_bad_settings]
- AC2: migrate applies the schema on an empty database [evidence: test:tests/test_cli.py::test_migrate_applies_schema]
- AC3: the bot refuses to start when whoami differs from MATRIX_USER_ID [evidence: test:tests/test_bot_process.py::test_whoami_mismatch_exits_78]
- AC4: the bot answers readyz 503 before the first sync and 200 after it, and a revoked token stops it with exit 1 [evidence: test:tests/test_bot_process.py::test_readiness_and_auth_failure]
- AC5: a second bot instance waits on the advisory lock and processes nothing [evidence: test:tests/test_bot_process.py::test_singleton]

## Files

- `src/agents_matrix_connector/cli.py`
- `src/agents_matrix_connector/bot.py`
- `tests/test_cli.py`
- `tests/test_bot_process.py`

## Interfaces

- Console script `agents-matrix-connector {migrate, api, bot}` (contract `agents-matrix-connector-image` entrypoint, used by the chart).
- `src/agents_matrix_connector/bot.py`: `run_bot`.

## Expected outcome

`agents-matrix-connector bot` against the fake homeserver and fake orchestrator syncs, dispatches and replies; `agents-matrix-connector api` serves `/matrix/api/v1`.

## Steps

- Red: extend `tests/test_cli.py` and add `tests/test_bot_process.py` (run `run_bot` in-process with the fakes on ASGI transports, or the fakes served by uvicorn on free ports). Fails: no subcommands.
- Green: write `bot.py` and the cli wiring. Run the verify (Docker).

## Notes

- Follow `code/agents-webhook/src/agents_webhook/cli.py` (`run_service`, exit 78) and `agents_common.runtime` (`advisory_singleton`, `LostLock`).

- 2026-10-25 done
