---
title: webhook chart network
status: done
repo: agents-webhook
value: the public /webhook/ ingest prefix and the SSO-protected API share the lab host with the right routing
files: [chart/agents-webhook/templates/service.yaml, chart/agents-webhook/templates/ingress.yaml, chart/agents-webhook/values.yaml, chart/agents-webhook/ci/lint-values.yaml, tests/test_chart_network.py]
verify: "uv run pytest tests/test_chart_network.py -q && helm lint chart/agents-webhook -f chart/agents-webhook/ci/lint-values.yaml && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-chart-workloads, webhook-ingest-http]
model: ""
review: full
verified_head: 1f676e1
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: 2
actual_minutes: 2
actual_tokens: 346609
actual_roles: "impl 2, review 1"
actual_role_tokens: "impl 246865, review 99744"
---

# webhook chart network

## Requirement

Services and Ingresses (design D12; re-plan 2026-10-25: the public ingest is `https://<base>/webhook/<suffix>`). Paths are in code/agents-webhook.

- `templates/service.yaml`: Services `<fullname>-ingest` and `<fullname>-api`, port 80 to targetPort `http`.
- `templates/ingress.yaml`: two Ingress objects from `ingress.{enabled, className, host, tls.secretName, annotations, ingestAnnotations}`:
  - `<fullname>-api`: path `/webhooks/api` (Prefix) to the api Service.
  - `<fullname>-ingest`: path `/webhook` (Prefix, so it matches `/webhook/<suffix>` and never `/webhooks/...`) to the ingest Service.
  - Neither renders a `cert-manager.io/cluster-issuer` annotation unless set in values; both reference `tls.secretName`.
- `values.yaml`: the `ingress` block (disabled by default). `ci/lint-values.yaml`: enabled with a test host.
- `tests/test_chart_network.py`: the path to Service mapping exactly as above; the ingest Ingress never routes `/webhooks/api`; the api Ingress never routes `/webhook`; no cert-manager annotation by default; disabled renders no Ingress.

## Acceptance conditions

- AC1: /webhooks/api routes to the api Service and the /webhook prefix to the ingest Service [evidence: command:uv run pytest tests/test_chart_network.py -q -k paths]
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

- 2026-10-25 amended: re-plan 2026-10-25: per-webhook endpoints (/webhook/<suffix>, one type, one preset, basic auth) replace per-source secrets and mappings; agent reuse is opt-in per preset (design D3, D7, D16-D19)

Security review of ingest (2026-10-25): WEBHOOK_TRUSTED_PROXIES must be set to the ingress controller pod CIDR / node CIDR (the hop that sets X-Forwarded-For) for the ingest Deployment; with it empty every caller shares the proxy key and one client can get all forges rate-limited (429). Make it a chart value and set it in the helmfile values; test the render. Also set ingress proxy body size >= the 5 MiB cap and read/send timeouts.

Orchestrator note (2026-10-25): add the chart tests the workloads review found missing: imagePullSecrets duplicated between `global.imagePullSecrets` and `imagePullSecrets` renders once (this exact case broke the agents-web live apply), and assertions for allowPrivilegeEscalation false, drop ALL, seccomp RuntimeDefault on every container incl. the migrate init container.

- 2026-10-25 done
