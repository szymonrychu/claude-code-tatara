---
title: mxc chart agent port
status: todo
repo: agents-matrix-connector
value: "the deployed connector exposes its agent listener to the orchestrator through its own Service, the hash only in a Secret"
files: [chart/agents-matrix-connector/templates/deployment.yaml, chart/agents-matrix-connector/templates/service-agents.yaml, chart/agents-matrix-connector/templates/_config.tpl, chart/agents-matrix-connector/templates/secret.yaml, chart/agents-matrix-connector/values.yaml, chart/agents-matrix-connector/ci/lint-values.yaml, tests/test_chart_network.py, tests/test_chart_workloads.py]
verify: "uv run pytest tests/test_chart_network.py tests/test_chart_workloads.py && mise run lint"
depends_on: [mxc-agent-listener]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 9
expected_tokens: 1836811
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc chart agent port

## Requirement

README Goal, verbatim: "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

Design D3, verbatim (chart): "The chart adds a container port `agents` 8001 on the api pod only and a Service `<fullname>-api-agents`; the bot still has no Service."

Design D3, verbatim: "the sha256 hex of the presented token must equal `MATRIX_AGENT_TOKEN_SHA256` [...] The token never reaches a log line or an error body."

Design D14, verbatim (value shape): "`values/agents-matrix-connector/agent-token.secrets.yaml` (`{agentApi: {tokenSha256}}`)".

Scope (agents-matrix-connector chart): values `agentApi.port` (8001), `agentApi.tokenSha256` (empty) or `agentApi.tokenSecret.{name,key}` (the secret wins), `limits.agentRatePerMinute` (20); the api container gets port `agents` and env `MATRIX_AGENT_TOKEN_SHA256` from the chart Secret or the named Secret (api only, never in the ConfigMap; a value that is not 64 lowercase hex fails the render); the ConfigMap gets `MATRIX_AGENT_PORT` and `MATRIX_AGENT_RATE_PER_MINUTE`; new template `service-agents.yaml` (`<fullname>-api-agents`, ClusterIP, port 8001, targetPort `agents`, api selector). `tests/test_chart_network.py::test_service_selects_api_only` is no longer accurate (named): it asserts the chart has exactly one Service; it is rewritten as `test_services_select_api_only` asserting the two Services, both selecting only the api component, and that no Service selects the bot.

## Acceptance conditions

- ac1: the chart renders the -api and -api-agents Services, the agents Service on port 8001 targeting port agents, both selecting only the api component, and no Service selects the bot (updated) [evidence: test:tests/test_chart_network.py::test_services_select_api_only]
- ac2: the api container exposes port agents 8001 and the bot container does not [evidence: test:tests/test_chart_workloads.py::test_agent_port_only_on_api]
- ac3: MATRIX_AGENT_TOKEN_SHA256 reaches only the api container through a secretKeyRef (chart Secret from agentApi.tokenSha256, or agentApi.tokenSecret, which wins), never the ConfigMap, and a malformed hash fails the render [evidence: test:tests/test_chart_workloads.py::test_agent_token_hash_secret_on_api_only]
- ac4: the ConfigMap renders MATRIX_AGENT_PORT and MATRIX_AGENT_RATE_PER_MINUTE (extended) [evidence: test:tests/test_chart_workloads.py::test_config_rendered]
- ac5: the Ingress still routes only /matrix/api to the -api Service [evidence: test:tests/test_chart_network.py::test_ingress_routes_api_prefix]
- ac6: helm lint passes with the CI lint values [evidence: command:mise run lint:chart]
- ac7: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_chart_network.py tests/test_chart_workloads.py && mise run lint]

## Files

- `chart/agents-matrix-connector/templates/deployment.yaml`
- `chart/agents-matrix-connector/templates/service-agents.yaml`
- `chart/agents-matrix-connector/templates/_config.tpl`
- `chart/agents-matrix-connector/templates/secret.yaml`
- `chart/agents-matrix-connector/values.yaml`
- `chart/agents-matrix-connector/ci/lint-values.yaml`
- `tests/test_chart_network.py`
- `tests/test_chart_workloads.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
