---
title: mxc chart network
status: todo
repo: agents-matrix-connector
value: the UI API is reachable under /matrix/api on the lab host and the bot is not reachable at all
files: [chart/agents-matrix-connector/templates/service.yaml, chart/agents-matrix-connector/templates/ingress.yaml, chart/agents-matrix-connector/values.yaml, tests/test_chart_network.py]
verify: "helm lint chart/agents-matrix-connector && uv run --frozen pytest tests/test_chart_network.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-chart-workloads]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc chart network

## Requirement

Service and Ingress of the connector chart (design D11, D13). Paths are in code/agents-matrix-connector.

- `chart/agents-matrix-connector/templates/service.yaml`: ClusterIP `<fullname>-api` port 8000 (`http`) selecting the api pods only; the bot has no Service.
- `chart/agents-matrix-connector/templates/ingress.yaml`: when `ingress.enabled`, one Ingress for `ingress.host` with path `/matrix/api` (Prefix) to the api Service, `ingressClassName`, `annotations` (none by default: no cert-manager annotation), `tls.secretName`.
- `chart/agents-matrix-connector/values.yaml`: `service {port: 8000}`, `ingress {enabled: false, className: nginx, host: "", annotations: {}, tls: {secretName: ""}}`.
- `tests/test_chart_network.py` (`helm template`): the Service selects only api pods; the Ingress routes only `/matrix/api` to the api Service, carries no cert-manager annotation by default, and is absent when disabled; no route reaches the bot.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: the api Service selects only api pods and the bot has no Service [evidence: test:tests/test_chart_network.py::test_service_selects_api_only]
- AC2: the Ingress routes only /matrix/api to the api Service with the given host and TLS secret and no cert-manager annotation [evidence: test:tests/test_chart_network.py::test_ingress_routes_api_prefix]
- AC3: no Ingress renders when it is disabled [evidence: test:tests/test_chart_network.py::test_ingress_disabled]

## Files

- `chart/agents-matrix-connector/templates/service.yaml`
- `chart/agents-matrix-connector/templates/ingress.yaml`
- `chart/agents-matrix-connector/values.yaml`
- `tests/test_chart_network.py`

## Interfaces

- Values `service`, `ingress` (contract `agents-matrix-connector-chart`), consumed by helmfile-matrix-releases.

## Expected outcome

With `ingress.enabled` and host `lab.szymonrichert.pl`, `https://lab.szymonrichert.pl/matrix/api/v1/...` reaches the api pods; nothing reaches the bot.

## Steps

- Red: `tests/test_chart_network.py` with the three tests. Fails: no templates.
- Green: write the templates and values. Run the verify.

## Notes

- Follow `code/agents-webhook/chart/agents-webhook/templates/{service,ingress}.yaml` and its `tests/test_chart_network.py`; the connector has no public ingest.
