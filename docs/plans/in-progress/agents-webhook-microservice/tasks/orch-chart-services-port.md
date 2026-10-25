---
title: orch chart services port
status: in-progress
repo: agent-orchestrator
value: the service port is reachable in-cluster through its own Service and never through the ingress or the SSO sidecar
files: [chart/agent-orchestrator/templates/service-services.yaml, chart/agent-orchestrator/templates/deployment.yaml, chart/agent-orchestrator/templates/configmap.yaml, chart/agent-orchestrator/templates/secret.yaml, chart/agent-orchestrator/values.yaml, tests/test_chart_services_port.py]
verify: "uv run pytest tests/test_chart_services_port.py tests/test_chart_deployments.py tests/test_chart_config.py -q && helm lint chart/agent-orchestrator -f chart/agent-orchestrator/ci/lint-values.yaml && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-service-port-auth]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch chart services port

## Requirement

Chart support for the service port (design D10). Paths are in code/agent-orchestrator.

- `values.yaml`: `serviceApi: {port: 8002, existingSecret: "", existingSecretKey: "service-tokens", tokenHashes: {}}`; `tokenHashes` maps a service name to the sha256 hex of its token, so each service's SOPS values file adds its own key and helmfile merges them; existingSecret wins when set.
- `templates/service-services.yaml`: ClusterIP Service `<fullname>-services`, port `serviceApi.port`, targetPort and port name `services`, selector the api component; header comment "never referenced by the ingress", like `service-agents.yaml`.
- `templates/deployment.yaml`: the api container gets containerPort `services` (`serviceApi.port`). The port name is never `http`, so the oauth2-proxy injector (which fronts the port named `http`) does not proxy it.
- `templates/configmap.yaml`: `ORCH_SERVICE_PORT`.
- `templates/secret.yaml` / env: `ORCH_SERVICE_TOKENS` from `serviceApi.existingSecret` key `existingSecretKey`, or from the chart Secret as the CSV `<name>:<hash>` of `serviceApi.tokenHashes` sorted by name; absent when neither is set; a hash that is not 64 lowercase hex fails the render.
- `tests/test_chart_services_port.py` (with `tests/helm_render.py`): the Service renders with port 8002 and name `services`; the api container exposes it; the Ingress never references `-services`; env wiring for existingSecret and for two `tokenHashes` entries from two values files (sorted CSV); a malformed hash fails the render; nothing renders the token in a ConfigMap.

## Acceptance conditions

- AC1: the services Service and container port render with name services on 8002 [evidence: test:tests/test_chart_services_port.py::test_services_service_rendered]
- AC2: the ingress never routes to the services Service [evidence: test:tests/test_chart_services_port.py::test_ingress_excludes_services_port]
- AC3: ORCH_SERVICE_TOKENS comes from the Secret, never a ConfigMap [evidence: test:tests/test_chart_services_port.py::test_service_tokens_from_secret]
- AC4: existing chart tests, helm lint and ruff pass [evidence: command:uv run pytest tests/test_chart_deployments.py tests/test_chart_config.py -q && helm lint chart/agent-orchestrator -f chart/agent-orchestrator/ci/lint-values.yaml && uv run ruff check . && uv run ruff format --check .]

## Files

- `chart/agent-orchestrator/templates/service-services.yaml`
- `chart/agent-orchestrator/templates/deployment.yaml`
- `chart/agent-orchestrator/templates/configmap.yaml`
- `chart/agent-orchestrator/templates/secret.yaml`
- `chart/agent-orchestrator/values.yaml`
- `tests/test_chart_services_port.py`

## Interfaces

- Owns `orch-services-service`: Service `<fullname>-services:8002` (port name `services`), values `serviceApi.{port, existingSecret, existingSecretKey, tokenHashes}`; in agents-helmfile the URL is `http://agent-orchestrator-services:8002`.

## Expected outcome

`helm template` shows the services Service and port; the ingress is unchanged.

## Steps

- Red: write `tests/test_chart_services_port.py`; run: fails.
- Green: templates and values; run the verify command.

## Notes

- Model on `templates/service-agents.yaml` and the `agents` port in `deployment.yaml` L79-80.
