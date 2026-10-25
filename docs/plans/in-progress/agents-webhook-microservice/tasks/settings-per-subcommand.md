---
title: settings per subcommand
status: todo
repo: agents-webhook
value: the public ingest and migrate run without the orchestrator token
files: [src/agents_webhook/settings.py, src/agents_webhook/cli.py, tests/test_cli.py, tests/test_schema_settings.py]
verify: "uv run pytest tests/test_cli.py tests/test_schema_settings.py -o addopts= -q && uv run ruff check ."
depends_on: []
model: ""
review: ""
verified_head: ""
points: 2
expected_minutes: 10
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
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

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
