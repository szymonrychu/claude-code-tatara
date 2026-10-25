---
title: webhook docs memory
status: todo
repo: agents-webhook
value: "operators know how to configure each source, the exposure and the limits, and the decisions are recorded"
files: [README.md, MEMORY.md, AGENTS.md, tests/test_readme_config.py]
verify: "uv run pytest tests/test_readme_config.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-ci-images, webhook-openapi-readme]
owns: []
uses: [webhook-settings-env, webhook-ingest-api]
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

# webhook docs memory

## Requirement

Service documentation (design D2, D3, D12, D14). Paths are in code/agents-webhook.

- README sections: `## Overview` (what, the three processes, the queue), `## Configuration` (every `WEBHOOK_*` variable with default, from `settings.py`), `## Sources` (GitHub, GitLab, Grafana setup: URL `https://lab.szymonrichert.pl/webhooks/<source>`, events to select, where the secret goes), `## Statuses and reasons` (the five statuses and every reason), `## Security` (public ingest without SSO in its own Deployment, constant-time checks, 5 MiB cap, prompt framing, the orchestrator service token), `## Commands`, `## Helm chart`, `## Development` (mise tasks); the existing `## API` stays.
- MEMORY.md dated 2026-10-25 lines: dedup semantics (D5), limits (D6), the ingest/api split and why (D2), the marker idempotency (D8).
- AGENTS.md: points at mise test/lint and names the highest-risk surface (public ingest, prompt framing).
- `tests/test_readme_config.py`: every settings field appears in README Configuration as its env name; every status and reason constant appears in README Statuses and reasons.

## Acceptance conditions

- AC1: every WEBHOOK_ variable and every status and reason is documented [evidence: command:uv run pytest tests/test_readme_config.py -q]
- AC2: README has the Security section naming the public ingest exposure [evidence: doc-section:README.md#Security]
- AC3: MEMORY records the dedup, limits, split and idempotency decisions [evidence: command:grep -q "2026-10-25" MEMORY.md]

## Files

- `README.md`
- `MEMORY.md`
- `AGENTS.md`
- `tests/test_readme_config.py`

## Interfaces

- README defines `webhook-ingest-api` and `webhook-api` for consumers.

## Expected outcome

A new operator can wire a forge or Grafana from the README alone.

## Steps

- Red: `tests/test_readme_config.py`; run: fails. Green: docs; run the verify command.

## Notes

- Doc task plus one doc test.
