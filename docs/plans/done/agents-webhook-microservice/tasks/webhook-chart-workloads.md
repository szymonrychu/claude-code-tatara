---
title: webhook chart workloads
status: done
repo: agents-webhook
value: "the service deploys as three Deployments, with the public ingest kept out of SSO"
files: [chart/agents-webhook/Chart.yaml, chart/agents-webhook/values.yaml, chart/agents-webhook/templates/_helpers.tpl, chart/agents-webhook/templates/_config.tpl, chart/agents-webhook/templates/deployment.yaml, chart/agents-webhook/templates/configmap.yaml, chart/agents-webhook/templates/secret.yaml, tests/test_chart_workloads.py]
verify: "uv run pytest tests/test_chart_workloads.py -q && helm lint chart/agents-webhook && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-cli-entrypoints]
model: ""
review: full
verified_head: 5e4a480
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: 2
actual_minutes: 6
actual_tokens: 928985
actual_roles: "impl 5, review 1"
actual_role_tokens: "impl 797807, review 131178"
---

# webhook chart workloads

## Requirement

Helm chart workloads (design D2, D13; re-plan 2026-10-25: no per-source secrets; ingest authenticates endpoints from the database). Paths are in code/agents-webhook.

- `Chart.yaml`: `agents-webhook`, version `0.1.0`, appVersion `0.1.0`.
- `values.yaml`: `image {repository harbor.szymonrichert.pl/containers/agents-webhook, tag, pullPolicy}`, `imagePullSecrets`, `postgres {url | existingSecret, existingSecretKey}` (required; no in-chart CNPG), `orchestrator {url, token | tokenSecret {name, key}}`, `publicBaseUrl` (`WEBHOOK_PUBLIC_BASE_URL`), `trustedProxies` (list of CIDRs, `WEBHOOK_TRUSTED_PROXIES`), `env` (extra WEBHOOK_*), `components {ingest {replicas 2, podAnnotations {}, resources}, api {replicas 1, podAnnotations {}, resources}, worker {replicas 1, resources}}`, `service`, `ingress` (used by webhook-chart-network), security contexts as agent-orchestrator (non-root 1000, read-only root FS). No `sources` block.
- `templates/deployment.yaml`: one Deployment per component running `agents-webhook <component>`, port `http` 8000 for ingest and api, liveness/readiness on `/healthz`/`/readyz` (worker: exec probe or none), an initContainer `agents-webhook migrate`, env from the ConfigMap plus secrets: `WEBHOOK_DATABASE_URL` from `postgres` (all three), `WEBHOOK_ORCHESTRATOR_TOKEN` from `orchestrator.tokenSecret` (api and worker only, never ingest). `podAnnotations` per component, so oauth2-proxy annotations go on `api` only.
- `templates/configmap.yaml`: `WEBHOOK_ORCHESTRATOR_URL`, `WEBHOOK_PUBLIC_BASE_URL`, `WEBHOOK_TRUSTED_PROXIES`, limits and `env`. `templates/secret.yaml`: the inline `orchestrator.token` and `postgres.url` values, when set.
- `tests/test_chart_workloads.py` (helm template via a small `helm_render` helper as agent-orchestrator's `tests/helm_render.py`): three Deployments with the right args; migrate initContainer; ingest gets the database URL and no orchestrator token; worker and api get the token; component podAnnotations land only on their pods; missing postgres fails the render with a clear message; no secret value in the ConfigMap; no `sources` value or `WEBHOOK_*_SECRET`/`_TOKEN` source variable rendered.

## Acceptance conditions

- AC1: ingest, api and worker Deployments run their subcommands after a migrate initContainer [evidence: command:uv run pytest tests/test_chart_workloads.py -q -k deployments]
- AC2: only api and worker get the orchestrator token and no source secrets are rendered [evidence: command:uv run pytest tests/test_chart_workloads.py -q -k secrets]
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

- Owns `agents-webhook-chart`: values shape above; published as `oci://harbor.szymonrichert.pl/charts/agents-webhook` by webhook-ci-images.

## Expected outcome

`helm template` renders the three workloads with the right secrets split.

## Steps

- Red: tests; run: fail. Green: chart; run the verify command.

## Notes

- Model on `code/agent-orchestrator/chart/agent-orchestrator/templates/{deployment.yaml,_config.tpl}` (components loop, postgres source).

- 2026-10-25 amended: re-plan 2026-10-25: per-webhook endpoints (/webhook/<suffix>, one type, one preset, basic auth) replace per-source secrets and mappings; agent reuse is opt-in per preset (design D3, D7, D16-D19)

Gate Q23 answer (user, 2026-10-25): the limits (max in progress overall, max in progress per endpoint, queue cap, body cap) are settings with defaults 3, 1, 500 and 5 MiB, each set from an agents-webhook Helm chart value (for example `limits.maxInProgress`, `limits.maxInProgressPerEndpoint`, `limits.queueCap`, `limits.maxBodyBytes`) rendered into the ingest and worker env, and documented. This task delivers its part of that.

- 2026-10-25 done
