---
title: chart agents service
status: todo
repo: agent-orchestrator
value: agent pods reach the agent port through a cluster-internal Service that never sits on the ingress
files: [chart/agent-orchestrator/templates/service-agents.yaml, chart/agent-orchestrator/templates/deployment.yaml, chart/agent-orchestrator/templates/_config.tpl, chart/agent-orchestrator/values.yaml, tests/test_chart_deployments.py]
verify: "uv run pytest tests/test_chart_deployments.py tests/test_chart_config.py tests/test_chart_rbac_ingress.py -q && mise run lint:chart && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [orch-agents-service]
uses: []
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

# chart agents service

## Requirement

Foundation part F4, chart (D1). In `chart/agent-orchestrator`:

- the api container gets `containerPort` named `agents` (values `agentApi.port`, default 8001) and `ORCH_AGENT_PORT` in the settings ConfigMap;
- new `templates/service-agents.yaml`: ClusterIP Service `<fullname>-agents`, port 8001, targetPort `agents`, selecting the api component only; the ingress never references it;
- `_config.tpl` sets `ORCH_AGENT_API_URL` to `http://<fullname>-agents.<namespace>.svc:<port>` unless `env.ORCH_AGENT_API_URL` overrides it;
- values.yaml documents `agentApi.port`.

## Acceptance conditions

- AC1: the agents Service renders as ClusterIP on 8001 targeting the api's agents port [evidence: test:tests/test_chart_deployments.py::test_agents_service]
- AC2: the ingress backends reference only the http Service [evidence: test:tests/test_chart_deployments.py::test_ingress_excludes_agents_service]
- AC3: the settings ConfigMap carries ORCH_AGENT_PORT and the default ORCH_AGENT_API_URL, overridable through env [evidence: test:tests/test_chart_deployments.py::test_agent_api_settings]
- AC4: chart lint and the other chart suites pass [evidence: command:mise run lint:chart && uv run pytest tests/test_chart_config.py tests/test_chart_rbac_ingress.py -q]

## Files

- `chart/agent-orchestrator/templates/service-agents.yaml`
- `chart/agent-orchestrator/templates/deployment.yaml`
- `chart/agent-orchestrator/templates/_config.tpl`
- `chart/agent-orchestrator/values.yaml`
- `tests/test_chart_deployments.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
