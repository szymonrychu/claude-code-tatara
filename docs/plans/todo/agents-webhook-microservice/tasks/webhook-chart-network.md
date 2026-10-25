---
title: webhook chart network
status: todo
repo: agents-webhook
value: the public ingest paths and the SSO-protected API share the lab host with the right routing
files: [chart/agents-webhook/templates/service.yaml, chart/agents-webhook/templates/ingress.yaml, chart/agents-webhook/values.yaml, chart/agents-webhook/ci/lint-values.yaml, tests/test_chart_network.py]
verify: "uv run pytest tests/test_chart_network.py -q && helm lint chart/agents-webhook -f chart/agents-webhook/ci/lint-values.yaml && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-chart-workloads, webhook-ingest-http]
owns: []
uses: [agents-webhook-chart, webhook-ingest-api]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# webhook chart network

## Requirement

Services and Ingresses (design D12). Paths are in code/agents-webhook.

- `templates/service.yaml`: Services `<fullname>-ingest` and `<fullname>-api`, port 80 to targetPort `http`.
- `templates/ingress.yaml`: two Ingress objects from `ingress.{enabled, className, host, tls.secretName, annotations, ingestAnnotations}`:
  - `<fullname>-api`: path `/webhooks/api` (Prefix) to the api Service.
  - `<fullname>-ingest`: paths `/webhooks/github`, `/webhooks/gitlab`, `/webhooks/grafana` (Exact) to the ingest Service.
  - Neither renders a `cert-manager.io/cluster-issuer` annotation unless set in values; both reference `tls.secretName`.
- `values.yaml`: the `ingress` block (disabled by default). `ci/lint-values.yaml`: enabled with a test host.
- `tests/test_chart_network.py`: the path to Service mapping exactly as above; the ingest Ingress never routes `/webhooks/api`; the api Ingress never routes the three ingest paths; no cert-manager annotation by default; disabled renders no Ingress.

## Acceptance conditions

- AC1: /webhooks/api routes to the api Service and the three exact ingest paths to the ingest Service [evidence: command:uv run pytest tests/test_chart_network.py -q -k paths]
- AC2: no Ingress carries the cert-manager annotation by default and both use the configured TLS secret [evidence: command:uv run pytest tests/test_chart_network.py -q -k tls]
- AC3: helm lint with the CI values and ruff pass [evidence: command:helm lint chart/agents-webhook -f chart/agents-webhook/ci/lint-values.yaml && uv run ruff check . && uv run ruff format --check .]

## Files

- `chart/agents-webhook/templates/service.yaml`
- `chart/agents-webhook/templates/ingress.yaml`
- `chart/agents-webhook/values.yaml`
- `chart/agents-webhook/ci/lint-values.yaml`
- `tests/test_chart_network.py`

## Interfaces

- Paths `/webhooks/api` and `/webhooks/{github,gitlab,grafana}` on the shared host; agents-helmfile sets host `lab.szymonrichert.pl` and TLS secret `agent-orchestrator-tls`.

## Expected outcome

The chart routes public and SSO traffic to different pods.

## Steps

- Red: tests; run: fail. Green: templates and values; run the verify command.

## Notes

- One cert-manager annotation per host (frontend-decoupling brief A4); the orchestrator or agents-web Ingress owns it.
