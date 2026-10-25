---
title: mxc chart workloads
status: todo
repo: agents-matrix-connector
value: the connector deploys as an API and a singleton bot with its token only as a bot file mount
files: [chart/agents-matrix-connector/Chart.yaml, chart/agents-matrix-connector/values.yaml, chart/agents-matrix-connector/templates/_helpers.tpl, chart/agents-matrix-connector/templates/_config.tpl, chart/agents-matrix-connector/templates/configmap.yaml, chart/agents-matrix-connector/templates/deployment.yaml, chart/agents-matrix-connector/templates/secret.yaml, tests/test_chart_workloads.py]
verify: "helm lint chart/agents-matrix-connector && uv run --frozen pytest tests/test_chart_workloads.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-service-entrypoints]
model: sonnet
review: full
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc chart workloads

## Requirement

Helm chart workloads of the connector (design D1, D13; contract `agents-matrix-connector-chart`). Paths are in code/agents-matrix-connector.

`chart/agents-matrix-connector/`:

- `Chart.yaml` (name `agents-matrix-connector`, version `0.1.0`, appVersion `0.1.0`).
- `values.yaml`: `image {repository: harbor.szymonrichert.pl/containers/agents-matrix-connector, tag, pullPolicy}`, `imagePullSecrets`, `postgres {url | existingSecret, existingSecretKey}`, `orchestrator {url, token | tokenSecret {name, key}}`, `matrix {homeserverUrl, userId, deviceId, selfIdentities: [], bridgeBots: ["@facebookbot:szymonrichert.pl"], puppetPattern, accessToken | accessTokenSecret {name, key}}`, `policy {default: deny, groupTrigger: mention}`, `limits {maxNewSessions, maxQueuedPerRoom, maxInboundChars, replyChunkChars, runTimeoutSeconds, pollSeconds, syncTimeoutSeconds, retentionDays}`, `api {allowedCidrs}`, `env: {}` (extra `MATRIX_*`), `components {api {replicas: 1, podAnnotations: {}, resources}, bot {podAnnotations: {}, resources}}`, `securityContext` (non-root 1000, read-only root filesystem, no privilege escalation, drop ALL).
- `templates/_helpers.tpl` (names, labels) and `templates/_config.tpl` (the shared env block).
- `templates/configmap.yaml`: every non-secret `MATRIX_*` setting from values.
- `templates/secret.yaml`: created only when `postgres.url`, `orchestrator.token` or `matrix.accessToken` are given inline; keys `database-url`, `orchestrator-token`, `matrix-access-token`.
- `templates/deployment.yaml`: two Deployments: `<fullname>-api` (`agents-matrix-connector api`, port 8000 `http`, probes `/healthz` and `/readyz`, `components.api.replicas`) and `<fullname>-bot` (`agents-matrix-connector bot`, `replicas: 1`, `strategy: Recreate`, probes on port 8000); both with initContainer `agents-matrix-connector migrate`, env from the ConfigMap, `MATRIX_DATABASE_URL` and `MATRIX_ORCHESTRATOR_TOKEN` from the inline Secret or the named existing Secrets; the Matrix access token mounted only into the bot as a file (`MATRIX_ACCESS_TOKEN_FILE=/var/run/secrets/matrix/token`, Secret volume mode 0440), never as an env var or in the ConfigMap; `/tmp` as emptyDir.
- `tests/test_chart_workloads.py` (`helm template`): both Deployments render with the right args; bot has one replica and Recreate; the access token is a file mount in the bot only and absent from env, the api pod and the ConfigMap; existing-secret and inline variants; security context; migrate initContainer on both.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: api and bot Deployments render with their subcommands, probes and the migrate initContainer [evidence: test:tests/test_chart_workloads.py::test_deployments_render]
- AC2: the bot runs one replica with the Recreate strategy [evidence: test:tests/test_chart_workloads.py::test_bot_singleton_strategy]
- AC3: the Matrix access token reaches only the bot, as a file, never an env var or ConfigMap value [evidence: test:tests/test_chart_workloads.py::test_access_token_file_only_in_bot]
- AC4: existing secrets and inline values both wire the database URL and the orchestrator token [evidence: test:tests/test_chart_workloads.py::test_secret_variants]
- AC5: pods run non-root with a read-only root filesystem and dropped capabilities [evidence: test:tests/test_chart_workloads.py::test_security_context]
- AC6: the chart lints [evidence: command:helm lint chart/agents-matrix-connector]

## Files

- `chart/agents-matrix-connector/Chart.yaml`
- `chart/agents-matrix-connector/values.yaml`
- `chart/agents-matrix-connector/templates/_helpers.tpl`
- `chart/agents-matrix-connector/templates/_config.tpl`
- `chart/agents-matrix-connector/templates/configmap.yaml`
- `chart/agents-matrix-connector/templates/deployment.yaml`
- `chart/agents-matrix-connector/templates/secret.yaml`
- `tests/test_chart_workloads.py`

## Interfaces

- `chart/agents-matrix-connector/values.yaml` (contract `agents-matrix-connector-chart`): the values shape above, consumed by helmfile-matrix-releases; env names from contract `matrix-connector-settings-env`.

## Expected outcome

`helm template` renders an api and a singleton bot wired to Postgres, the orchestrator service port and the homeserver, with the Matrix token only as a bot file mount.

## Steps

- Red: `tests/test_chart_workloads.py` with the five tests. Fails: no chart.
- Green: write the chart files. Run the verify.

## Notes

- Copy the structure of `code/agents-webhook/chart/agents-webhook/` and its `tests/test_chart_workloads.py`.
- Service and Ingress are task mxc-chart-network.
