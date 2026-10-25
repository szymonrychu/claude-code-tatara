---
title: chart ingress and test hook
status: done
repo: agents-schedule
value: "the schedule API is routable on the shared host under its own path, behind the shared SSO"
files: [chart/agents-schedule/templates/ingress.yaml, chart/agents-schedule/templates/tests/test-connection.yaml, chart/agents-schedule/values.yaml, tests/test_chart_ingress.py]
verify: "uv run --frozen pytest tests/test_chart_ingress.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [helm-chart]
model: ""
review: ""
verified_head: e2b75eb99625dbc15c2ca39e02708ad02bd6dfe8
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: 1
actual_minutes: 2
actual_tokens: 420519
actual_roles: "impl 2, review 1"
actual_role_tokens: "impl 252349, review 168170"
---

# chart ingress and test hook

## Requirement

Finish the chart (design D13; approvals A1, A6):

- `ingress {enabled: false, className, annotations, denySourceRanges, hosts[].paths[] {path, pathType}, tls}` renders an Ingress to the api Service port `http` (as `code/agents-orchestrator/chart/agents-orchestrator/templates/ingress.yaml`). The chart adds no cert-manager annotation of its own: per the URL layout of frontend-decoupling (contract `agents-web-url-layout`), only one Ingress of the host carries it and the others reference the same TLS secret.
- `templates/tests/test-connection.yaml`: a helm test Pod hitting `/healthz` on the api Service.
- Chart `version: 0.1.0`, `appVersion` set by CI.
- tests/test_chart_ingress.py asserts the Ingress host, path `/schedules` (Prefix) and TLS secret from values, the deny annotation, no cert-manager annotation by default, and the test hook.

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

- Contract `agents-schedule-chart`: `oci://harbor.szymonrichert.pl/charts/agents-schedule` (versions `X.Y.Z` on tag, `X.Y.Z-main.<sha7>` on main), values as in `helm-chart` plus `ingress` (file `code/agents-schedule/chart/agents-schedule/values.yaml`), consumed by agents-helmfile.

## Expected outcome

The chart is complete and publishable; agents-helmfile can route `/schedules` to it on the lab host.

## Steps

- Write tests/test_chart_ingress.py; run: fails.
- Write ingress.yaml, the test hook and the values; `uv run --frozen pytest tests/test_chart_ingress.py -q`: `3 passed`.
- `helm lint` clean.

## Notes

- Prefix `/schedules` owns the service's whole path space per `agents-web-url-layout`; the API answers at `/schedules/api/v1`.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done
