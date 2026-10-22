---
title: helm chart config postgres
status: todo
repo: agent-orchestrator
value: "The chart wires settings, secrets and any Postgres (or an optional CNPG) without homelab assumptions"
files: [chart/agent-orchestrator/values.yaml, chart/agent-orchestrator/templates/_config.tpl, chart/agent-orchestrator/templates/configmap.yaml, chart/agent-orchestrator/templates/secret.yaml, chart/agent-orchestrator/templates/cnpg-cluster.yaml, tests/test_chart_config.py, README.md]
verify: "uv run pytest tests/test_chart_config.py -q && mise run lint && mise run lint:chart"
depends_on: [helm-chart-scaffold, settings-model]
owns: []
uses: [helm-render, agent-orchestrator-chart, agent-orchestrator-settings-env]
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

# helm chart config postgres

## Requirement

The chart's settings, Secrets and Postgres connection (D28, D7, D15). By default the chart requires a Postgres connection; CNPG is an optional feature.

New `values.yaml` keys, documented inline:
- `agentImage: ""` (required; becomes `ORCH_AGENT_IMAGE`)
- `env: {}`: extra `ORCH_*` variables, passed verbatim. A key that does not start with `ORCH_` fails the render naming it.
- `postgres`: `{url: "", host: "", port: 5432, database: "", user: "", password: "", sslmode: "", existingSecret: "", existingSecretKey: uri}`
- `cnpg`: `{enabled: false, instances: 1, imageName: "", database: agent_orchestrator, owner: agent_orchestrator, storage: {size: 10Gi, storageClass: ""}, walStorage: {enabled: false, size: 2Gi, storageClass: ""}, resources: {}, backup: {}}`
- `masterKey`: `{existingSecret: "", existingSecretKey: master-key, value: ""}`
- `claude`: `{existingSecret: "", existingSecretKey: CLAUDE_CODE_OAUTH_TOKEN, token: ""}`

Postgres resolution, in `templates/_config.tpl` as `agent-orchestrator.databaseUrlEnv`. Exactly one source may be set, and the sources are:
1. `cnpg.enabled`: `secretKeyRef` on the CNPG app Secret `<fullname>-db-app`, key `uri`.
2. `postgres.existingSecret`: `secretKeyRef` with `existingSecretKey`.
3. `postgres.url`: stored in the chart Secret `<fullname>-database`.
4. `postgres.host`, `user` and `database` (with `password`, `port`, `sslmode`): composed into `postgresql://<user>:<password>@<host>:<port>/<database>[?sslmode=]`, with user and password URL-escaped, and stored in `<fullname>-database`.

No source fails the render with `agent-orchestrator: a Postgres connection is required: set postgres.url, postgres.host/user/database/password, postgres.existingSecret, or cnpg.enabled=true`. Two or more sources fail it naming them.

Templates:
- `templates/configmap.yaml` (ConfigMap `<fullname>-settings`):
  - `ORCH_NAMESPACE` = `.Release.Namespace` (the one namespace, D26)
  - `ORCH_AGENT_IMAGE`
  - `ORCH_CLAUDE_SECRET_NAME` = `claude.existingSecret` or `<fullname>-claude`
  - every `env` entry
  - never a secret value
- `templates/secret.yaml`:
  - `<fullname>-database` (source 3 or 4)
  - `<fullname>-master-key` with key `master-key` when `masterKey.value` is set
  - `<fullname>-claude` with key `CLAUDE_CODE_OAUTH_TOKEN` when `claude.token` is set; the agent pods in the same namespace read it
  - Each Secret is replaced by its `existingSecret`. A master key or Claude token with neither a value nor an existingSecret fails the render.
- `templates/_config.tpl`, `agent-orchestrator.env`: the container env every component Deployment includes. It holds `envFrom` the settings ConfigMap, `ORCH_DATABASE_URL` from the resolved source, and `ORCH_MASTER_KEY` from its Secret.
- `templates/cnpg-cluster.yaml`, only when `cnpg.enabled`: a `postgresql.cnpg.io/v1` Cluster `<fullname>-db` with instances, imageName, storage, walStorage, resources and `bootstrap.initdb {database, owner}`. `backup` is rendered verbatim when non-empty, so agents-helmfile can copy the existing CNPG backup config (user answer Q13).

README.md gains `## Helm chart`, covering:
- an install example
- the four Postgres options and the CNPG feature
- the Secrets and their existingSecret overrides
- the settings ConfigMap and `env`

## Acceptance conditions

- AC1: rendering without any Postgres source fails with the documented message [evidence: test:tests/test_chart_config.py::test_requires_postgres_connection]
- AC2: postgres.url and postgres parts each yield ORCH_DATABASE_URL from the chart Secret, with user and password URL-escaped [evidence: test:tests/test_chart_config.py::test_postgres_url_and_parts]
- AC3: postgres.existingSecret yields a secretKeyRef with the configured key and no chart database Secret [evidence: test:tests/test_chart_config.py::test_postgres_existing_secret_ref]
- AC4: two Postgres sources at once fail naming both [evidence: test:tests/test_chart_config.py::test_multiple_postgres_sources_rejected]
- AC5: CNPG is off by default; enabled, it renders the Cluster with backup passed through verbatim and wires ORCH_DATABASE_URL to <fullname>-db-app uri [evidence: test:tests/test_chart_config.py::test_cnpg_optional_with_backup_passthrough]
- AC6: the settings ConfigMap sets ORCH_NAMESPACE to the release namespace, ORCH_AGENT_IMAGE and ORCH_CLAUDE_SECRET_NAME, passes env through and rejects a non-ORCH_ key [evidence: test:tests/test_chart_config.py::test_settings_configmap]
- AC7: the master key and Claude token come from a chart Secret or an existingSecret, and missing both fails [evidence: test:tests/test_chart_config.py::test_master_key_and_claude_secrets]
- AC8: no secret value appears in the ConfigMap [evidence: test:tests/test_chart_config.py::test_no_secret_values_in_configmap]
- AC9: README documents the chart [evidence: doc-section:README.md#Helm chart]

## Files

- `chart/agent-orchestrator/values.yaml`
- `chart/agent-orchestrator/templates/_config.tpl`
- `chart/agent-orchestrator/templates/configmap.yaml`
- `chart/agent-orchestrator/templates/secret.yaml`
- `chart/agent-orchestrator/templates/cnpg-cluster.yaml`
- `tests/test_chart_config.py`
- `README.md`

## Interfaces

- values `agentImage`, `env`, `postgres.*`, `cnpg.*`, `masterKey.*`, `claude.*` (contract `agent-orchestrator-chart`)
- template helpers `agent-orchestrator.env` and `agent-orchestrator.databaseUrlEnv` in `templates/_config.tpl`, used by helm-chart-deployments
- ConfigMap `<fullname>-settings` carrying the `ORCH_*` names of contract `agent-orchestrator-settings-env`

## Expected outcome

`helm template` renders the settings, the Secrets and the database wiring from any one of the four Postgres sources. It fails loudly when there is none.

## Steps

- Write tests/test_chart_config.py with the eight named tests over `tests/helm_render.py`. Run `uv run pytest tests/test_chart_config.py -q` and expect failures.
- Write the values keys, _config.tpl, configmap.yaml, secret.yaml, cnpg-cluster.yaml and the README section.
- Rerun and expect `8 passed`, then run `mise run lint` and `mise run lint:chart`.

## Notes

agents-helmfile runs its own CNPG release (agent-orchestrator-db) and points `postgres.existingSecret` at `agent-orchestrator-db-app` key `uri`, so cnpg stays off there. Release name `agent-orchestrator` gives the Claude Secret `agent-orchestrator-claude`, the settings default.

Object names derived from `<fullname>` must never take the form `agent-<slug>-ccw`. The reconciler deletes Secrets of that form by name (D26).
