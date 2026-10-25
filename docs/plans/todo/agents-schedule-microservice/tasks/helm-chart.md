---
title: helm chart
status: todo
repo: agents-schedule
value: the service deploys as an api and a worker Deployment with its database and orchestrator token wired from Secrets
files: [chart/agents-schedule/Chart.yaml, chart/agents-schedule/values.yaml, chart/agents-schedule/templates/_helpers.tpl, chart/agents-schedule/templates/_config.tpl, chart/agents-schedule/templates/deployment.yaml, chart/agents-schedule/templates/service.yaml, chart/agents-schedule/templates/configmap.yaml, tests/test_chart.py]
verify: "uv run --frozen pytest tests/test_chart.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [service-entrypoints, schedule-settings-model]
owns: [agents-schedule-chart-core]
uses: [sched-entrypoints, agents-schedule-settings-env]
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

# helm chart

## Requirement

Add `chart/agents-schedule` (design D13; approval A1), modelled on `code/agent-orchestrator/chart/agent-orchestrator` (components loop in `templates/deployment.yaml`, postgres source in `_config.tpl`):

- values: `image {repository: harbor.szymonrichert.pl/containers/agents-schedule, tag}`, `postgres {url | existingSecret, existingSecretKey | host, port, database, user, password}` (required), `orchestrator {url, token {existingSecret, key}}` (required), `env` (extra `SCHED_*`), `components {api {replicas, port 8000, podAnnotations, resources}, worker {replicas: 1, resources}}`, `service`, `serviceAccount`, `ingress` (see `chart-ingress-and-test-hook`).
- One Deployment per component: api runs `sched api`, worker `sched worker`; both have a `sched migrate` initContainer (the advisory-locked migrator makes concurrent runs safe); readiness `/readyz` and liveness `/healthz` on the api; the worker has no Service.
- ConfigMap of the non-secret `SCHED_*` settings; `SCHED_DATABASE_URL` and `SCHED_ORCHESTRATOR_TOKEN_FILE` come from the Secrets (token mounted as a file).
- Service `<fullname>-api` port name `http` (the oauth2-proxy injector hands that port to the sidecar).
- `mise run test:chart` and `mise run lint:chart` (defined by `scaffold-project-and-cli`) pass once this task and `chart-ingress-and-test-hook` land.
- tests/test_chart.py renders with `helm template` and asserts the Deployments, commands, initContainers, env sources and that a missing postgres or orchestrator value fails the render.

## Acceptance conditions

- AC1: the api and worker Deployments render with their commands and migrate initContainers [evidence: test:tests/test_chart.py::test_components_render]
- AC2: database URL and orchestrator token come only from Secrets [evidence: test:tests/test_chart.py::test_secrets_wired]
- AC3: a missing postgres or orchestrator value fails the render [evidence: test:tests/test_chart.py::test_required_values]
- AC4: helm lint passes [evidence: command:helm lint chart/agents-schedule --set postgres.url=postgresql://x/y --set orchestrator.url=http://o --set orchestrator.token.existingSecret=t]

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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
