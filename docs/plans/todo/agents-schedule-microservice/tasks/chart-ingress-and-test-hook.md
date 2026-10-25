---
title: chart ingress and test hook
status: todo
repo: agents-schedule
value: "the schedule API is routable on the shared host under its own path, behind the shared SSO"
files: [chart/agents-schedule/templates/ingress.yaml, chart/agents-schedule/templates/tests/test-connection.yaml, chart/agents-schedule/values.yaml, tests/test_chart_ingress.py]
verify: "uv run --frozen pytest tests/test_chart_ingress.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [helm-chart]
owns: [agents-schedule-chart]
uses: [agents-schedule-chart-core, web-ingress-path-layout]
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

# chart ingress and test hook

## Requirement

Finish the chart (design D13; approvals A1, A6):

- `ingress {enabled: false, className, annotations, hosts[].paths[] {path, pathType}, tls}` renders an Ingress to the api Service port `http` (as `code/agent-orchestrator/chart/agent-orchestrator/templates/ingress.yaml`). The chart adds no cert-manager annotation of its own: per the frontend-decoupling path layout (contract `web-ingress-path-layout`), only the web Ingress carries it and the others reference the shared TLS secret.
- `templates/tests/test-connection.yaml`: a helm test Pod hitting `/healthz` on the api Service.
- Chart `version: 0.1.0`, `appVersion` set by CI.
- tests/test_chart_ingress.py asserts the Ingress host, path `/schedules/api` (Prefix) and TLS secret from values, no cert-manager annotation by default, and the test hook.

## Acceptance conditions

- AC1: an enabled ingress routes the configured host and path to the api Service [evidence: test:tests/test_chart_ingress.py::test_ingress_routes_path]
- AC2: the chart adds no cert-manager annotation by default [evidence: test:tests/test_chart_ingress.py::test_no_cert_manager_annotation]
- AC3: the helm test hook hits /healthz [evidence: test:tests/test_chart_ingress.py::test_connection_hook]

## Files

- `chart/agents-schedule/templates/ingress.yaml`
- `chart/agents-schedule/templates/tests/test-connection.yaml`
- `chart/agents-schedule/values.yaml`
- `tests/test_chart_ingress.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
