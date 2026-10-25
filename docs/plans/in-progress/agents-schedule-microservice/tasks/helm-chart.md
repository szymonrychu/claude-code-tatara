---
title: helm chart
status: in-progress
repo: agents-schedule
value: the service deploys as an api and a worker Deployment with its database and orchestrator token wired from Secrets
files: [chart/agents-schedule/Chart.yaml, chart/agents-schedule/values.yaml, chart/agents-schedule/templates/_helpers.tpl, chart/agents-schedule/templates/_config.tpl, chart/agents-schedule/templates/deployment.yaml, chart/agents-schedule/templates/service.yaml, chart/agents-schedule/templates/configmap.yaml, tests/test_chart.py]
verify: "uv run --frozen pytest tests/test_chart.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [service-entrypoints, schedule-settings-model]
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

# helm chart

## Requirement

Add `chart/agents-schedule` (design D13; approval A1), modelled on `code/agents-orchestrator/chart/agents-orchestrator` (components loop in `templates/deployment.yaml`, postgres source in `_config.tpl`):

- values: `image {repository: harbor.szymonrichert.pl/containers/agents-schedule, tag}`, `postgres {url | existingSecret, existingSecretKey | host, port, database, user, password}` (required), `orchestrator {url, token | tokenSecret {name, key}}` (url and one token source required; the agents-webhook chart shape), `env` (extra `SCHED_*`), `components {api {replicas, port 8000, podAnnotations, resources}, worker {replicas: 1, resources}}`, `service`, `serviceAccount`, `ingress` (see `chart-ingress-and-test-hook`).
- One Deployment per component: api runs `sched api`, worker `sched worker`; both have a `sched migrate` initContainer (the advisory-locked migrator makes concurrent runs safe); readiness `/readyz` and liveness `/healthz` on the api; the worker has no Service.
- ConfigMap of the non-secret `SCHED_*` settings; `SCHED_DATABASE_URL` comes from the postgres Secret; the orchestrator token is rendered into the chart's own Secret from `orchestrator.token` (or taken from `orchestrator.tokenSecret`) and mounted as the file `SCHED_ORCHESTRATOR_TOKEN_FILE` names.
- Service `<fullname>-api` port name `http` (the oauth2-proxy injector hands that port to the sidecar).
- `mise run test:chart` and `mise run lint:chart` (defined by `scaffold-project-and-cli`) pass once this task and `chart-ingress-and-test-hook` land.
- tests/test_chart.py renders with `helm template` and asserts the Deployments, commands, initContainers, env sources and that a missing postgres or orchestrator value fails the render.

## Acceptance conditions

- AC1: the api and worker Deployments render with their commands and migrate initContainers [evidence: test:tests/test_chart.py::test_components_render]
- AC2: database URL and orchestrator token reach the pods only through Secrets, never the ConfigMap [evidence: test:tests/test_chart.py::test_secrets_wired]
- AC3: a missing postgres or orchestrator value fails the render [evidence: test:tests/test_chart.py::test_required_values]
- AC4: helm lint passes [evidence: command:helm lint chart/agents-schedule --set postgres.url=postgresql://x/y --set orchestrator.url=http://o --set orchestrator.token=t]

## Files

- `chart/agents-schedule/Chart.yaml`
- `chart/agents-schedule/values.yaml`
- `chart/agents-schedule/templates/_helpers.tpl`
- `chart/agents-schedule/templates/_config.tpl`
- `chart/agents-schedule/templates/deployment.yaml`
- `chart/agents-schedule/templates/service.yaml`
- `chart/agents-schedule/templates/configmap.yaml`
- `tests/test_chart.py`

## Interfaces

- Part `agents-schedule-chart-core`: chart values listed above (file `chart/agents-schedule/values.yaml`).

## Expected outcome

`helm template` renders a working api and worker from values, with no secret in a ConfigMap.

## Steps

- Write tests/test_chart.py; run: fails (no chart).
- Write the chart; `uv run --frozen pytest tests/test_chart.py -q`: `3 passed`.
- `helm lint` clean.

## Notes

- do-not-build: an in-chart CNPG; agents-helmfile deploys `agents-schedule-db` as a separate cnpg/cluster release.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule
