---
title: orch service port docs
status: todo
repo: agent-orchestrator
value: operators and the next service know how to get and use a service token
files: [README.md, MEMORY.md, tests/test_readme_api.py]
verify: "uv run pytest tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-service-port-auth, orch-chart-services-port]
owns: []
uses: [orch-service-tokens]
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

# orch service port docs

## Requirement

Document the service port (design D10, D14; the contract `orch-service-tokens` is defined in README). Paths are in code/agent-orchestrator.

- README `## Security`: a `### Service tokens` subsection: why (pod CIDRs stay out of `ORCH_ALLOWED_CIDRS`), the port, the Bearer scheme, hashes only in the orchestrator, the route list, 401 and 403, how to mint a token (`openssl rand -hex 32`, then `printf %s "$T" | sha256sum`).
- README `## Configuration`: `ORCH_SERVICE_PORT`, `ORCH_SERVICE_TOKENS`, `ORCH_SERVICE_TOKENS_FILE`; `## Helm chart`: `serviceApi.*` and the `-services` Service.
- MEMORY.md: dated 2026-10-25 entry: service tokens on a dedicated port instead of Keycloak client credentials, and why (the injector's JWT audience is unknown; the allowlist trust model stays).
- `tests/test_readme_api.py`: a test that the README documents `ORCH_SERVICE_PORT` and `ORCH_SERVICE_TOKENS` and each service-port route; the existing drift test proves `openapi.json` is unchanged (additive-only rule).

## Acceptance conditions

- AC1: README documents the service port, tokens and route list [evidence: test:tests/test_readme_api.py::test_service_port_documented]
- AC2: openapi.json is unchanged and the drift tests pass [evidence: command:uv run pytest tests/test_readme_api.py -q]
- AC3: MEMORY records the decision with its date and why [evidence: command:grep -q "service token" MEMORY.md]
- AC4: README has the Service tokens section [evidence: doc-section:README.md#Service tokens]

## Files

- `README.md`
- `MEMORY.md`
- `tests/test_readme_api.py`

## Interfaces

- README is where `orch-service-tokens` is defined for consumers (agents-webhook, agents-schedule, agents-helmfile).

## Expected outcome

A reader can mint a token, configure both sides and knows which routes the port serves.

## Steps

- Red: add `test_service_port_documented`; run: fails.
- Green: README and MEMORY; run the verify command.

## Notes

- Doc task plus one doc test.
