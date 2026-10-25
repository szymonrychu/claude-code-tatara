---
title: settings per subcommand
status: done
repo: agents-webhook
value: the public ingest and migrate run without the orchestrator token
files: [src/agents_webhook/settings.py, src/agents_webhook/cli.py, tests/test_cli.py, tests/test_schema_settings.py]
verify: "uv run pytest tests/test_cli.py tests/test_schema_settings.py -o addopts= -q && uv run ruff check ."
depends_on: []
model: ""
review: ""
verified_head: d8d1322
points: 2
expected_minutes: 10
expected_tokens: 542616
points_actual: 2
actual_minutes: 2
actual_tokens: 329491
actual_roles: impl 2
actual_role_tokens: impl 329491
---

# settings per subcommand

## Requirement

Discovered by webhook-chart-workloads (2026-10-25): WebhookSettings requires WEBHOOK_ORCHESTRATOR_TOKEN and cli.main loads the full settings for every subcommand, so the `ingest` container and the `migrate` init container (which by design get no orchestrator token: least privilege, the public ingest never talks to the orchestrator) exit 78. Make the settings per subcommand: `migrate` needs only the database URL; `ingest` needs the database URL, limits, rate-limit and trusted-proxy settings, base URL, but no orchestrator URL or token; `api` and `worker` keep requiring the orchestrator URL and token. Error messages still name every missing variable for the subcommand that needs it. Tests for each subcommand with only its own variables set, and that ingest never constructs an orchestrator client.

## Acceptance conditions

- AC1: migrate and ingest start without orchestrator settings; api and worker refuse without them, naming the variables [evidence: test:tests/test_cli.py::test_settings_per_subcommand]
- AC2: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/settings.py`
- `src/agents_webhook/cli.py`
- `tests/test_cli.py`
- `tests/test_schema_settings.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

`agents-webhook migrate` and `agents-webhook ingest` run with no WEBHOOK_ORCHESTRATOR_* variables; api and worker still require them.

## Steps

- Write `test_settings_per_subcommand`; run `uv run pytest tests/test_cli.py -o addopts= -q -k per_subcommand`: fails (exit 78 for ingest/migrate).
- Split the settings per subcommand; rerun: passes.
- Run the verify command.

## Notes

agents-common BaseServiceSettings requires the orchestrator token; a subclass or a separate settings class without it for migrate/ingest is fine. DB tests: local Postgres postgresql://test@127.0.0.1:55433/postgres via a temporary uncommitted pg_url override.

- 2026-10-25 done
