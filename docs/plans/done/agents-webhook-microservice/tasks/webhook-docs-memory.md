---
title: webhook docs memory
status: done
repo: agents-webhook
value: "operators know how to create endpoints and wire GitHub, GitLab and Grafana to them, the exposure, reuse and limits, and the decisions are recorded"
files: [README.md, MEMORY.md, AGENTS.md, tests/test_readme_config.py]
verify: "uv run pytest tests/test_readme_config.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-ci-images, webhook-openapi-readme]
model: ""
review: ""
verified_head: 9b070e3
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: 2
actual_minutes: 7
actual_tokens: 871024
actual_roles: "impl 4, review 3"
actual_role_tokens: "impl 676647, review 194377"
---

# webhook docs memory

## Requirement

Service documentation (design D2, D3, D7, D12, D14, D16, D18; re-plan 2026-10-25). Paths are in code/agents-webhook.

- README sections: `## Overview` (what, the three processes, the queue), `## Configuration` (every `WEBHOOK_*` variable with default, from `settings.py`), `## Endpoints` (the five types and which provider events each accepts; creating one in the UI or API; the URL `https://lab.szymonrichert.pl/webhook/<suffix>`; how to configure basic auth in GitHub (credentials in the payload URL), GitLab (credentials in the URL) and Grafana (contact point webhook username and password); the password is shown once, rotate to replace it), `## Agent reuse` (the preset field `reuse_running_agent`, what counts as running, ordering, the fallback when the cluster goes away), `## Statuses and reasons` (the five statuses and every reason), `## Security` (public ingest without SSO in its own Deployment, scrypt password hashes, constant-time checks, identical 401 for unknown suffixes and wrong credentials, the failed-auth limit and `WEBHOOK_TRUSTED_PROXIES`, 5 MiB cap, prompt framing, the orchestrator service token), `## Commands`, `## Helm chart`, `## Development` (mise tasks); the existing `## API` stays.
- MEMORY.md dated 2026-10-25 lines: per-webhook endpoints replace source secrets and mappings (D3, D7), dedup semantics (D5), agent reuse opt-in (D16), limits (D6), the ingest/api split and why (D2), the marker idempotency (D8).
- AGENTS.md: points at mise test/lint and names the highest-risk surface (public ingest and its basic auth, prompt framing).
- `tests/test_readme_config.py`: every settings field appears in README Configuration as its env name; every status and reason constant appears in README Statuses and reasons; every endpoint type appears in README Endpoints.

## Acceptance conditions

- AC1: every WEBHOOK_ variable, every status and reason and every endpoint type is documented [evidence: command:uv run pytest tests/test_readme_config.py -q]
- AC2: README has the Security section naming the public ingest exposure and the credential handling [evidence: doc-section:README.md#Security]
- AC3: README has the Agent reuse section [evidence: doc-section:README.md#Agent reuse]
- AC4: MEMORY records the endpoint, dedup, reuse, limits, split and idempotency decisions [evidence: command:grep -q "2026-10-25" MEMORY.md && grep -qi "reuse" MEMORY.md]

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

- 2026-10-25 amended: re-plan 2026-10-25: per-webhook endpoints (/webhook/<suffix>, one type, one preset, basic auth) replace per-source secrets and mappings; agent reuse is opt-in per preset (design D3, D7, D16-D19)

Gate Q23 answer (user, 2026-10-25): the limits (max in progress overall, max in progress per endpoint, queue cap, body cap) are settings with defaults 3, 1, 500 and 5 MiB, each set from an agents-webhook Helm chart value (for example `limits.maxInProgress`, `limits.maxInProgressPerEndpoint`, `limits.queueCap`, `limits.maxBodyBytes`) rendered into the ingest and worker env, and documented. This task delivers its part of that.

Orchestrator note (2026-10-25): README must also cover agent reuse (preset reuse_running_agent, same-item routing to a running cluster, ordering, fallback and the `reuse_fallback` reason) and the per-subcommand settings (migrate/ingest need no orchestrator token).

- 2026-10-25 done
