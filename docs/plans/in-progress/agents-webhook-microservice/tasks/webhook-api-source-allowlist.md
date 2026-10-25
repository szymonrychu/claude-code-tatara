---
title: webhook api source allowlist
status: todo
repo: agents-webhook
value: only the SSO sidecar can reach the webhook management API
files: [src/agents_webhook/settings.py, src/agents_webhook/api/app.py, chart/agents-webhook/values.yaml, chart/agents-webhook/templates/_config.tpl, tests/test_api_source_allowlist.py, tests/test_chart_workloads.py, README.md]
verify: "uv run pytest tests/test_api_source_allowlist.py tests/test_chart_workloads.py -o addopts= -q && uv run ruff check ."
depends_on: []
model: ""
review: ""
verified_head: ""
points: 2
expected_minutes: 9
expected_tokens: 538938
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# webhook api source allowlist

## Requirement

Epic security review 2026-10-25: the oauth2-proxy admission sidecar adds Service port `http-insecure` (8080), which goes straight to the api container port 8000. No NetworkPolicy exists in namespace agents, so any in-cluster pod (a prompt-injected agent pod included) can call `/webhooks/api/v1/*` without SSO: create endpoints, rotate credentials and read the password, and use template preview. The orchestrator closes the same hole with `allowed_cidrs` (agent-orchestrator settings.py `allowed_cidrs`, helmfile `ORCH_ALLOWED_CIDRS: 127.0.0.1/32`).

In agents-webhook, add the same control for the api component:
- A setting `WEBHOOK_API_ALLOWED_CIDRS`: a CSV list of CIDRs, validated at startup.
- A middleware on the api app that answers 403 for a client address outside the list. Use the direct peer address, never X-Forwarded-For. `/healthz` and `/readyz` stay open, so the kubelet probes work.
- A chart value `api.allowedCidrs`, rendered into the api env only, with the default `127.0.0.1/32` so the sidecar is the only caller.

Ingest and worker are unaffected. Follow the orchestrator's implementation shape (read it at /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agents-webhook-microservice/agent-orchestrator/src/agent_orchestrator) and reuse agents-common if it has a helper. Document it in the README and docs.

## Acceptance conditions

- AC1: the api answers 403 to a peer outside WEBHOOK_API_ALLOWED_CIDRS and serves a peer inside it; probes stay open [evidence: test:tests/test_api_source_allowlist.py::test_api_rejects_peer_outside_allowed_cidrs]
- AC2: the chart renders WEBHOOK_API_ALLOWED_CIDRS on the api only, default 127.0.0.1/32 [evidence: test:tests/test_chart_workloads.py::test_api_allowed_cidrs_rendered]
- AC3: the suite and lint pass [evidence: command:mise run test && mise run lint]

## Files

- `src/agents_webhook/settings.py`
- `src/agents_webhook/api/app.py`
- `chart/agents-webhook/values.yaml`
- `chart/agents-webhook/templates/_config.tpl`
- `tests/test_api_source_allowlist.py`
- `tests/test_chart_workloads.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
