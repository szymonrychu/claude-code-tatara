---
title: webhook chart probe port
status: todo
repo: agents-webhook
value: the api pod becomes Ready behind the oauth2-proxy sidecar
files: [chart/agents-webhook/templates/deployment.yaml, tests/test_chart_workloads.py]
verify: "uv run pytest tests/test_chart_workloads.py -o addopts= -q && uv run ruff check ."
depends_on: []
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 691322
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# webhook chart probe port

## Requirement

Live apply 2026-10-25: agents-webhook-api stays 1/2 Ready. The oauth2-proxy admission sidecar renames the api container port `http` to `http-insecure`, so the probes (`port: http`) fail with `strconv.Atoi: parsing "http"`. The orchestrator avoids this with numeric probe ports (values/agent-orchestrator/common.yaml, port 8000).

In agents-webhook chart/agents-webhook/templates/deployment.yaml, the liveness and readiness probes of the api and ingest containers use the numeric container port 8000, not the port name. Check the Service targetPort the same way, mirroring how the agent-orchestrator chart's api Service survives the sidecar. Change only what the sidecar breaks. A chart render test asserts numeric probe ports for both components. Bump nothing else.

## Acceptance conditions

- AC1: api and ingest probes use the numeric port 8000 [evidence: test:tests/test_chart_workloads.py::test_probes_use_numeric_port]
- AC2: the suite and lint pass [evidence: command:mise run test && mise run lint]

## Files

- `chart/agents-webhook/templates/deployment.yaml`
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
