---
title: orch chart services port
status: todo
repo: agent-orchestrator
value: the service port is reachable in-cluster through its own Service and never through the ingress or the SSO sidecar
files: [chart/agent-orchestrator/templates/service-services.yaml, chart/agent-orchestrator/templates/deployment.yaml, chart/agent-orchestrator/templates/configmap.yaml, chart/agent-orchestrator/templates/secret.yaml, chart/agent-orchestrator/values.yaml, tests/test_chart_services_port.py]
verify: "uv run pytest tests/test_chart_services_port.py tests/test_chart_deployments.py tests/test_chart_config.py -q && helm lint chart/agent-orchestrator -f chart/agent-orchestrator/ci/lint-values.yaml && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-service-port-auth]
owns: [orch-services-service]
uses: [orch-service-tokens]
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

# orch chart services port

## Requirement

Chart support for the service port (design D10). Paths are in code/agent-orchestrator.

- `values.yaml`: `serviceApi: {port: 8002, existingSecret: "", existingSecretKey: "service-tokens", tokens: ""}` (`tokens` only for dev; existingSecret wins).
- `templates/service-services.yaml`: ClusterIP Service `<fullname>-services`, port `serviceApi.port`, targetPort and port name `services`, selector the api component; header comment "never referenced by the ingress", like `service-agents.yaml`.
- `templates/deployment.yaml`: the api container gets containerPort `services` (`serviceApi.port`). The port name is never `http`, so the oauth2-proxy injector (which fronts the port named `http`) does not proxy it.
- `templates/configmap.yaml`: `ORCH_SERVICE_PORT`.
- `templates/secret.yaml` / env: `ORCH_SERVICE_TOKENS` from `serviceApi.existingSecret` key `existingSecretKey`, or from the chart Secret when `serviceApi.tokens` is set; absent when neither is set.
- `tests/test_chart_services_port.py` (with `tests/helm_render.py`): the Service renders with port 8002 and name `services`; the api container exposes it; the Ingress never references `-services`; env wiring for existingSecret and inline tokens; nothing renders the token in a ConfigMap.

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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
