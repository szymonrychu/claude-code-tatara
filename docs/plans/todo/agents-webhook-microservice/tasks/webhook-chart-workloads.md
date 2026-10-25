---
title: webhook chart workloads
status: todo
repo: agents-webhook
value: "the service deploys as three Deployments, with the public ingest kept out of SSO"
files: [chart/agents-webhook/Chart.yaml, chart/agents-webhook/values.yaml, chart/agents-webhook/templates/_helpers.tpl, chart/agents-webhook/templates/_config.tpl, chart/agents-webhook/templates/deployment.yaml, chart/agents-webhook/templates/configmap.yaml, chart/agents-webhook/templates/secret.yaml, tests/test_chart_workloads.py]
verify: "uv run pytest tests/test_chart_workloads.py -q && helm lint chart/agents-webhook && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-cli-entrypoints]
owns: [agents-webhook-chart]
uses: [webhook-cli, webhook-settings-env]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# webhook chart workloads

## Requirement

Helm chart workloads (design D2, D13). Paths are in code/agents-webhook.

- `Chart.yaml`: `agents-webhook`, version `0.1.0`, appVersion `0.1.0`.
- `values.yaml`: `image {repository harbor.szymonrichert.pl/containers/agents-webhook, tag, pullPolicy}`, `imagePullSecrets`, `postgres {url | existingSecret, existingSecretKey}` (required; no in-chart CNPG), `orchestrator {url, tokenSecret {name, key}}`, `sources {existingSecret, githubKey, gitlabKey, grafanaKey}`, `env` (extra WEBHOOK_*), `components {ingest {replicas 2, podAnnotations {}, resources}, api {replicas 1, podAnnotations {}, resources}, worker {replicas 1, resources}}`, `service`, `ingress` (used by webhook-chart-network), security contexts as agent-orchestrator (non-root 1000, read-only root FS).
- `templates/deployment.yaml`: one Deployment per component running `agents-webhook <component>`, port `http` 8000 for ingest and api, liveness/readiness on `/healthz`/`/readyz` (worker: exec probe or none), an initContainer `agents-webhook migrate`, env from the ConfigMap plus secrets: `WEBHOOK_DATABASE_URL` from `postgres`, `WEBHOOK_ORCHESTRATOR_TOKEN` from `orchestrator.tokenSecret` (api and worker only), source secrets as `WEBHOOK_*_FILE` mounted only into ingest. `podAnnotations` per component, so oauth2-proxy annotations go on `api` only.
- `templates/configmap.yaml`: `WEBHOOK_ORCHESTRATOR_URL`, limits and `env`. `templates/secret.yaml`: only for an inline `postgres.url` in dev.
- `tests/test_chart_workloads.py` (helm template via a small `helm_render` helper as agent-orchestrator's `tests/helm_render.py`): three Deployments with the right args; migrate initContainer; ingest gets the source secrets and no orchestrator token, worker and api get the token and no source secrets; component podAnnotations land only on their pods; missing postgres fails the render with a clear message; no secret value in the ConfigMap.

## Acceptance conditions

- AC1: ingest, api and worker Deployments run their subcommands after a migrate initContainer [evidence: command:uv run pytest tests/test_chart_workloads.py -q -k deployments]
- AC2: only ingest mounts source secrets and only api and worker get the orchestrator token [evidence: command:uv run pytest tests/test_chart_workloads.py -q -k secrets]
- AC3: pod annotations are per component, so SSO can be put on api only [evidence: command:uv run pytest tests/test_chart_workloads.py -q -k annotations]
- AC4: helm lint and ruff pass [evidence: command:helm lint chart/agents-webhook && uv run ruff check . && uv run ruff format --check .]

## Files

- `chart/agents-webhook/Chart.yaml`
- `chart/agents-webhook/values.yaml`
- `chart/agents-webhook/templates/_helpers.tpl`
- `chart/agents-webhook/templates/_config.tpl`
- `chart/agents-webhook/templates/deployment.yaml`
- `chart/agents-webhook/templates/configmap.yaml`
- `chart/agents-webhook/templates/secret.yaml`
- `tests/test_chart_workloads.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
