# agents-webhook microservice design

## Summary

A new Python service, agents-webhook, with its own CNPG Postgres database, receives GitHub and
GitLab PR/MR, issue and comment webhooks and Grafana alerts on public endpoints, stores them in a
FIFO queue table with content-aware dedup and limits, and starts agent clusters from presets
through the orchestrator API ("scheduler API" in the request). A Webhooks page in the web UI, between
Clusters and Presets, lists recent events with their status and manages event-to-preset mappings.
Headline decisions: a new library component agents-common holds what agents-schedule-microservice
reuses (D1); the public ingest runs in its own Deployment without SSO (D2); the orchestrator gains
bearer service tokens on a dedicated internal port (D10); the UI lands in agents-web, built by
frontend-decoupling (D11).

## Intent and why

The user wants more of tatara-new's behaviour in this system: forge and alert events start agent
clusters automatically, as tatara-new's operator did with webhooks, a queue and Tasks. Here the
unit of work is an agent cluster from a preset, the services talk only over HTTP, and each owns its
database (AGENTS.md hard rules). The webhook service is the first trigger service; the schedule
service follows and reuses its parts.

## Goals

- G1: `POST https://lab.szymonrichert.pl/webhooks/{github,gitlab,grafana}` accept signed events and answer 202 for accepted or ignored, 401 bad signature, 404 unconfigured source, 413 over 5 MiB, 5xx only when the DB write fails.
- G2: GitHub `pull_request`, `issues`, `issue_comment`, `pull_request_review_comment`; GitLab Merge Request, Issue and Note hooks; Grafana alert webhooks are normalised into one event shape with a dedup key: `<platform>/<repo>/mr/<n>`, `<platform>/<repo>/issue/<n>`, `grafana/<sha256 of the sorted commonLabels>[:16]`.
- G3: events are a FIFO queue (alerts first, then by sequence) with dedup per D5 and limits per D6.
- G4: a mapped event creates a cluster from its preset, posts the rendered prompt and tracks the first turn; statuses new, in-progress, handled, ignored, failed, each with a reason where relevant.
- G5: `/webhooks/api/v1` lists events and lists, creates and deletes mappings; documented in the README, committed `openapi.json`, drift-tested.
- G6: the Webhooks UI entry sits between Clusters and Presets (just above Presets until configuration-improvements adds Clusters).
- G7: the orchestrator accepts the service's calls with a bearer service token on port 8002; every other caller sees no change.
- G8: released, pinned and applied with its CNPG database; the live smoke is green.

## Non-goals

- Forge write-back (comments, statuses), cluster deletion, rate limiting per minute, per-project routing, a prompt field on presets, any change to the shape of existing `/api/v1` routes.

## Anti-goals

- The public ingest Deployment reaching the UI API or carrying the SSO sidecar's session.
- A restart or a duplicate delivery posting a second prompt or starting a second cluster for the same event.
- Event text reaching an agent as instructions instead of framed, escaped data.
- Any new caller of the orchestrator main port, or the CIDR allowlist loosened.
- Copies of the DB, settings or client code in agents-schedule later (the reason for agents-common).

## Constraints

- Python only for services; TypeScript only in agents-web (AGENTS.md hard rules).
- Services talk only through HTTP; each table has one writer except queue tables, which change rows only through status-guarded updates (`code/agent-orchestrator/MEMORY.md` L19).
- `/api/v1` of the orchestrator is additive-only (`code/agent-orchestrator/MEMORY.md` L17).
- The oauth2-proxy injector has no skip-auth annotation (`infrastructure/code/containers/apps/oauth2proxy-injector/webhook.go` L404-450), so a public endpoint cannot share a pod with SSO.
- The orchestrator `SourceAllowlist` reads only the socket peer; live `ORCH_ALLOWED_CIDRS` is `127.0.0.1/32` (`code/agents-helmfile/values/agent-orchestrator/common.yaml`).
- Plan-execute needs every task repo under `code/` when the run starts (`ticket.py:_integration_plan`) and refuses an epic mixing superrepo and component tasks, so the two new repos are created by the meta epic agents-webhook-component (D15).
- Runs after frontend-decoupling (orchestrator ruling) and agents-webhook-component; this epic's README blocks on both.

## Decisions

### D1: New components agents-common (library) and agents-webhook (service)

agents-common is a Python library repo pinned by git tag (`agents-common @ git+https://github.com/szymonrychu/agents-common@v0.1.0`), the any-mcp pattern. It holds `settings` (BaseServiceSettings with a per-service env prefix, SettingsError naming each bad variable, `*_FILE` secrets), `db` (open_pool, notify, listen, run_migrations over a package's `migrations/` dir under an advisory lock, `transition()` status-guarded update, `claim()` with `FOR UPDATE SKIP LOCKED`, and a pytest plugin `agents_common.testing` for a migrated template DB on testcontainers), `runtime` (advisory_singleton, run_service), `orchestrator` (OrchestratorClient), `fake_orchestrator` (a Starlette app with the same routes, for tests and e2e) and `runs` (PresetBinding, RunStore protocol, dispatch and track). agents-webhook depends only on the tag. Alternatives: agents-schedule importing agents-webhook (couples two services' releases), copying code (two drifting copies). Serves working answer Q10. Approvals A1, A10.

### D2: One image, three Deployments, migrate initContainer

`agents-webhook ingest` (public, port 8000, no SSO annotations), `agents-webhook api` (UI API, port 8000, oauth2-proxy annotations as agent-orchestrator's api), `agents-webhook worker` (singleton dispatcher and tracker); `agents-webhook migrate` runs as the initContainer of each. The ingest Deployment serves only `/webhooks/{github,gitlab,grafana}`, `/healthz`, `/readyz`; the api only `/webhooks/api/v1/*`, `/healthz`, `/readyz`. Serves Q3. Approvals A1, A7.

### D3: Ingest authentication and responses

Per source one secret: `WEBHOOK_GITHUB_SECRET` (HMAC-SHA256 of the raw body against `X-Hub-Signature-256`, `sha256=` prefix), `WEBHOOK_GITLAB_TOKEN` (`X-Gitlab-Token`), `WEBHOOK_GRAFANA_TOKEN` (`Authorization: Bearer`), each also as `*_FILE`. All compared with `hmac.compare_digest`; an empty or unset secret makes that source answer 404 `not_found`. Body capped at 5 MiB (413 before parsing); provider events not in G2 get 202 with status `ignored`, reason `unsupported_event`; a bad signature 401; a DB failure 503 so the forge retries. Serves Q3. Approvals A1, A7.

### D4: Normalised event and ignore rules

`NormalizedEvent{source github|gitlab|grafana, kind mr|issue|comment|alert, action, repo, number, title, body, comment_body, url, author, actor, labels, dedup_key, priority}`; alert priority 0, everything else 1. Ignored with a reason, and still stored and listed: `no_mapping`, `self_event` (actor in `WEBHOOK_BOT_LOGINS`), `author_not_allowed` (issue and comment events when `WEBHOOK_ALLOWED_AUTHORS` is set and the author is not in it), `action_ignored` (closed, merged, labeled, unlabeled, a title-only edit, drafts), `resolved` (Grafana status not firing), `duplicate`, `queue_full`, `mapping_removed`, `unsupported_event`. Handled actions: MR/PR opened, reopened, synchronize/update, ready_for_review; issue opened, reopened, edited (body); comment created. Serves Q4, Q8. Approvals A1, A2.

### D5: Dedup semantics

Partial unique index on `events(dedup_key) WHERE status IN ('new','in-progress') AND update_of IS NULL`. On a delivery whose key has a live row: if the live row is `new`, its payload, title, body and `updated_at` are replaced (latest wins, it keeps its sequence) and the delivery is stored `ignored`, reason `duplicate`, `duplicate_of` the live row; if it is `in-progress`, the delivery is stored as an update message row (`update_of` the live row, status `new`) that the worker posts to the live row's cluster as a message and then marks `handled`. A row that changed status between read and update is retried at most 3 times. Serves Q1. Approvals A2.

### D6: Limits and FIFO

At most `WEBHOOK_MAX_IN_PROGRESS` (default 3) first-dispatch events in progress and at most 1 per mapping; the worker claims the oldest eligible `new` row by `(priority, seq)` with `FOR UPDATE SKIP LOCKED`. Update messages bypass the caps (their cluster already runs). More than `WEBHOOK_MAX_QUEUE` (default 500) `new` rows: the delivery is stored `ignored`, reason `queue_full`. A run in progress longer than `WEBHOOK_RUN_TIMEOUT_SECONDS` (default 3600) becomes `failed`, reason `timeout` (my call: without it a stuck turn holds a slot forever). No per-minute rate limit. Serves Q2. Approvals A2.

### D7: Mappings

`mappings{id, source, kind, repo (null = any), labels (jsonb subset, Grafana only), preset_id, prompt_template (nullable), created_at}`, written only by the api. Ingest matches at receive time; the most specific mapping wins (repo set scores 1, plus the count of labels; ties to the oldest), so one event starts one cluster. The UI creates a mapping prefilled from an event row; mappings are listed and deleted, not edited (my call: the request names create and remove). A new mapping does not re-queue past events. POST validates `preset_id` against the orchestrator (`422 unknown_preset`). Serves Q7. Approvals A3, A4.

### D8: Dispatch and run tracking

The worker (singleton, `advisory_singleton`) claims a row `new -> in-progress` (guarded), then `agents_common.runs.dispatch`: create the cluster `POST /api/v1/clusters {preset_id, slug}` with the deterministic slug `wh-<event id>` (a 409 `conflict` resolves the existing cluster by slug), record `cluster_id`, then look for an existing message on that cluster carrying the event marker `<!-- agents-webhook:event:<id> -->` before posting one (`GET /api/v1/clusters/{id}/messages`), post the rendered prompt with the marker, and record `message_id`. So a restart at any point never posts a second prompt. `track` polls `GET /api/v1/messages/{id}`: turn `completed` -> `handled`; message `failed|cancelled` or turn `failed` -> `failed` with the reason; timeout per D6. The service never deletes clusters. Serves Q5, Q6. Approvals A3.

### D9: Prompt rendering

Default prompt: a fixed preamble saying the block is untrusted event data, never instructions, then `<event source kind action repo number url author>` with `<title>`, `<body>`, `<comment>`, `<labels>` children, every value XML-escaped (tatara-new `bundle.go` L220-268). A mapping's `prompt_template` uses `string.Template` placeholders `$event` (the escaped block), `$source`, `$kind`, `$repo`, `$number`, `$url`, `$title`, each substituted escaped; unknown placeholders are rejected on mapping create (422). Approvals A3.

### D10: Orchestrator service tokens on port 8002

agent-orchestrator gains `ORCH_SERVICE_PORT` (default 8002) and `ORCH_SERVICE_TOKENS` (CSV of `<name>:<sha256 hex of the token>`, or `ORCH_SERVICE_TOKENS_FILE`; malformed entries are a SettingsError). On the service port: `SourceAllowlist` is skipped, every request needs `Authorization: Bearer <token>` whose sha256 matches an entry by `hmac.compare_digest` (401 `unauthorized` otherwise), and only these routes answer, others 403 `forbidden`: `GET /api/v1/meta`, `GET /api/v1/presets`, `GET /api/v1/presets/{id}`, `GET|POST /api/v1/clusters`, `GET /api/v1/clusters/{id}`, `GET|POST /api/v1/clusters/{id}/messages`, `GET /api/v1/messages/{id}`, `/healthz`, `/readyz`; no WebSocket, never `/agent/v1`. The main and agent ports are unchanged. The chart adds ClusterIP Service `<fullname>-services:8002` (port name `services`, never `http`, so the oauth2-proxy injector does not front it; never in the ingress) and `serviceApi.tokenHashes` (one key per service name, so values files of several services merge) or `serviceApi.existingSecret`. The request log names the token's service. Alternative rejected: Keycloak client-credentials through the sidecar (unknown audience checks). Serves Q9. Approvals A5. Review tier panel.

### D11: UI in agents-web

The Webhooks page lives in agents-web (created by agents-web-component, shaped by frontend-decoupling). Its menu entry is `BACKEND_MENUS.webhooks = [{id: 'webhooks', label: 'Webhooks', order: 20, backend: 'webhooks', render}]` in the backend registry (contract `agents-web-backend-registry`: slots 10 Clusters, 20 Webhooks, 40 Presets), shown only when `config.json` lists backend `{id: webhooks, label: Webhooks, basePath: /webhooks/api/v1}` (contract `agents-web-backends-config`); so it sits between Clusters and Presets, and just above Presets while configuration-improvements has not added Clusters. Types come from `openapi/webhooks.json` vendored with `npm run sync:api -- webhooks` (contract `agents-web-openapi-vendor`; this epic adds the `webhooks` backend id to `scripts/sync-api.mjs`). The page polls events every 5 s, filters by status, shows source, kind, repo and number, title, status chip, reason and the cluster slug; mappings are listed with the preset name, removed after a confirm, and created from an event row in a dialog with a preset select. The shared trigger page pattern (`RunStatusChip`, `PresetSelect`, `usePoll`, form error display; contract `trigger-ui-page-pattern`) is owned here for agents-schedule. Approvals A4, A10.


### D12: URL layout

One host, `lab.szymonrichert.pl`. UI API at `/webhooks/api/v1` (served natively, no rewrite) behind SSO; public ingest at `/webhooks/github`, `/webhooks/gitlab`, `/webhooks/grafana` (Exact paths). Two Ingress objects in the chart; neither carries the cert-manager annotation, both use TLS secret `agent-orchestrator-tls` (frontend-decoupling A4). Serves Q3. Approvals A4, A7.

### D13: Deploy

agents-helmfile gets the release pair `agents-webhook-db` (`cnpg/cluster` 0.9.0) and `agents-webhook` (`oci://harbor.szymonrichert.pl/charts/agents-webhook`, pinned `0.1.0-main.<sha7>`, `needs: agents/agents-webhook-db`), values under `values/agents-webhook{,-db}/`, the DB URL from Secret `agents-webhook-db-cluster-app` key `uri`; `scripts/bootstrap-secrets.sh` generates the three source secrets and the service token into new SOPS files only (raw token and source secrets into `values/agents-webhook/default.secrets.yaml`, the token sha256 into `values/agent-orchestrator/service-token-agents-webhook.secrets.yaml` as `serviceApi.tokenHashes.agents-webhook`; existing secret files are never touched, so nothing rotates); the orchestrator pin moves to the build with the service port; agents-web gets the webhooks backend entry; the smoke checks ingest, api and the service port; then `mise run apply` and `mise run smoke`. Approvals A8.

### D14: Headless parity

Every capability has a documented route (README `## API`, committed `openapi.json`, drift test) and an API-only e2e (`tests/e2e/test_e2e_api.py` in agents-webhook: real Postgres, the three processes, `agents_common.fake_orchestrator`), covering each source, each ignore reason, dedup both ways, the caps, the queue cap, mapping create and delete, handled and failed. The orchestrator's service port has a kind e2e check. Approvals A9.

### D15: Repo creation and visibility

The repos are created by the separate meta epic agents-webhook-component (tasks create-agents-common-repo, create-agents-webhook-repo), a blocker of this epic, because ticket.py refuses an epic that mixes superrepo and component tasks and needs `code/<repo>` before the run. Each runs `mise run component:add -- --component <name>:python --remote github --forge-owner szymonrychu --public --confirm-forge --role ...` (public, like every other component; my call). The scaffold tasks here then add what the scaffold lacks (pyproject, Dockerfile, CI, chart). Harbor `containers/agents-webhook` and `charts/agents-webhook` use the same robot secrets as agent-orchestrator, set with `gh secret set` on the new repo. Approvals A6.


## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| start-discovery (code, tatara-new, deploy) | ran, `discovery.md` 2026-10-25 | drop-or-forward dedup (`TN/internal/queue/enqueue.go:dedupExists`, `TN/internal/controller/task_events.go`); capacity with FIFO by (priority, seq) (`TN/internal/controller/queue_controller.go:admit`); Grafana firing-only dedup on labels (`TN/internal/webhook/grafana.go:incidentDedupKey`); bot-actor drop (`TN/internal/webhook/server.go:isBotActor`) | CRD queue and per-project routing (`TN/api/v1alpha1/queuedevent_types.go`); agent-side outcome API with forge comments (`TN/internal/restapi/outcome.go`) |
| research-code-internal | ran as discovery lane 4 (reuse list in `discovery.md` Plan inputs) | the reuse map below | none |
| research-code-external | skipped: tatara-new is the parity target and was read directly | - | - |
| research-papers | skipped: CRUD, queue and HTTP plumbing, no algorithmic core | - | - |
| research-docs | skipped: no external library used in a new way; GitHub, GitLab and Grafana payload shapes come from tatara-new's tested parsers | - | - |
| frontend-decoupling brief | read | one host with path routing, runtime `config.json` backends, vendored openapi per backend | BFF, subdomains, micro-frontends |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| discovery reuse | `_create_from_preset` (create with deterministic slug, 409) | common-orchestrator-client |
| discovery reuse | `post_message` | common-orchestrator-client, common-run-tracker |
| discovery reuse | `bench/runner.py:_finished` polling | common-run-tracker |
| discovery reuse | `bench/runner.py:_follow_stream` SSE wake-up | rejected: polling every 5 s is enough for 3 concurrent runs; no SSE client in the worker |
| discovery reuse | `SourceAllowlist` bypass point | orch-service-port-auth |
| discovery reuse | `PortGate` dedicated port | orch-service-port-auth |
| discovery reuse | `db/queue.py:_transition` | common-db-helpers |
| discovery reuse | `db/migrate.py:run_migrations` | common-db-helpers |
| discovery reuse | `db/pool.py:open_pool` | common-db-helpers |
| discovery reuse | `runtime/singleton.py:advisory_singleton` | common-settings-runtime |
| discovery reuse | `runtime/run.py:run_service` | common-settings-runtime |
| discovery reuse | `settings.py:Settings` | common-settings-runtime |
| discovery reuse | `tests/conftest.py` template DB | common-db-helpers |
| discovery reuse | `tests/test_readme_api.py` drift test | webhook-openapi-readme |
| discovery reuse | chart components loop `deployment.yaml` | webhook-chart-workloads |
| discovery reuse | chart postgres source `_config.tpl` | webhook-chart-workloads |
| discovery reuse | CI workflow `ci.yaml` | webhook-ci-images, common-scaffold |
| discovery reuse | `SessionsMenu` settings menu | web-webhook-menu-entry |
| discovery reuse | component scaffold `scaffold.py:write` | common-scaffold, webhook-scaffold |
| discovery reuse | db + app release pair `helmfile.yaml.gotmpl` | helmfile-webhook-releases |
| discovery reuse | `scripts/bootstrap-secrets.sh` | helmfile-service-token |
| discovery do-not-build | SQLAlchemy / alembic | rejected: not built; psycopg 3 and the forward-only migrator (common-db-helpers) |
| discovery do-not-build | prompt field on presets | rejected: not built; prompt sent as a message (common-run-tracker) |
| discovery do-not-build | turn-completion callback in the orchestrator | rejected: not built; polling (common-run-tracker) |
| discovery do-not-build | writes into orchestrator tables | rejected: not built; HTTP only (common-orchestrator-client) |
| discovery do-not-build | skip-auth route in the SSO sidecar | rejected: not built; separate ingest Deployment (webhook-chart-workloads) |
| discovery do-not-build | in-chart CNPG | rejected: not built; helmfile cnpg release (helmfile-webhook-releases) |
| discovery fix-as-ac | non-idempotent create+message | common-run-tracker, webhook-dispatch-worker |
| discovery fix-as-ac | signature compare in constant time, empty secret refuses | webhook-ingest-http |
| discovery fix-as-ac | 413 before parsing | webhook-ingest-http |
| discovery fix-as-ac | 202 for accepted and ignored, 5xx only on DB failure | webhook-ingest-http |
| discovery fix-as-ac | untrusted event text framed as data | webhook-prompt-render |
| discovery fix-as-ac | status-guarded updates, SKIP LOCKED claims | webhook-event-store |
| discovery fix-as-ac | public ingest without SSO annotations | webhook-chart-workloads |
| discovery fix-as-ac | orchestrator API additive-only, openapi and README regenerated | orch-service-port-docs |
| discovery ideas | adopted: drop-or-forward dedup | webhook-event-store |
| discovery ideas | adopted: capacity with FIFO by (priority, seq) | webhook-event-store, webhook-dispatch-worker |
| discovery ideas | adopted: Grafana dedup on labels, firing only | webhook-normalize |
| discovery ideas | adopted: bot-actor self-event drop | webhook-normalize |
| discovery ideas | rejected: CRD queue and per-project routing | rejected: service-owned DB, one deployment per forge (D1) |
| discovery ideas | rejected: outcome API posting forge comments | rejected: out of scope (Non-goals) |
| discovery ideas | open Q9: Keycloak client-credentials vs service tokens | orch-service-port-auth (D10) |
| frontend-decoupling brief | runtime `config.json` backend entry | web-webhook-menu-entry, helmfile-web-webhooks-entry |
| frontend-decoupling brief | vendored openapi per backend | web-webhook-api-client |
| frontend-decoupling brief | one host, path routing, single cert-manager annotation (A4) | webhook-chart-network |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 New components agents-common and agents-webhook | common-scaffold, common-db-helpers, common-settings-runtime, common-orchestrator-client, common-run-tracker, common-release-v0-1-0, webhook-scaffold |
| D2 One image, three Deployments | webhook-cli-entrypoints, webhook-chart-workloads |
| D3 Ingest authentication and responses | webhook-ingest-http, webhook-schema-settings |
| D4 Normalised event and ignore rules | webhook-normalize, webhook-ingest-http |
| D5 Dedup semantics | webhook-schema-settings, webhook-event-store |
| D6 Limits and FIFO | webhook-event-store, webhook-dispatch-worker |
| D7 Mappings | webhook-mappings-repo, webhook-ui-api, web-webhook-mappings |
| D8 Dispatch and run tracking | common-run-tracker, webhook-dispatch-worker |
| D9 Prompt rendering | webhook-prompt-render |
| D10 Orchestrator service tokens on port 8002 | orch-service-port-auth, orch-chart-services-port, orch-service-port-e2e, orch-service-port-docs |
| D11 UI in agents-web | web-trigger-ui-kit, web-webhook-api-client, web-webhook-events-page, web-webhook-mappings, web-webhook-menu-entry |
| D12 URL layout | webhook-chart-network, webhook-ui-api |
| D13 Deploy | helmfile-service-token, deploy-pin-orch-service-port, helmfile-webhook-releases, helmfile-web-webhooks-entry, smoke-webhook-check, apply-smoke-webhook, webhook-ci-images |
| D14 Headless parity | webhook-openapi-readme, webhook-api-e2e, orch-service-port-e2e, webhook-docs-memory |
| D15 Repo creation and visibility | common-scaffold, webhook-scaffold, webhook-ci-images |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `agents-common-db` | common-db-helpers | common-settings-runtime, webhook-schema-settings, webhook-mappings-repo, webhook-event-store | `code/agents-common/src/agents_common/db/__init__.py` |
| `agents-common-settings-runtime` | common-settings-runtime | webhook-schema-settings, webhook-dispatch-worker, webhook-cli-entrypoints | `code/agents-common/src/agents_common/settings.py` |
| `agents-common-orchestrator-client` | common-orchestrator-client | common-run-tracker, webhook-ui-api, webhook-dispatch-worker | `code/agents-common/src/agents_common/orchestrator.py` |
| `agents-common-fake-orchestrator` | common-orchestrator-client | common-run-tracker, webhook-ui-api, webhook-dispatch-worker, webhook-api-e2e | `code/agents-common/src/agents_common/fake_orchestrator.py` |
| `agents-common-run-tracker` | common-run-tracker | webhook-event-store, webhook-dispatch-worker | `code/agents-common/src/agents_common/runs.py` |
| `agents-common-lib` | common-release-v0-1-0 | webhook-scaffold | `code/agents-common/pyproject.toml` |
| `orch-service-tokens` | orch-service-port-auth | orch-chart-services-port, orch-service-port-e2e, orch-service-port-docs, helmfile-service-token, smoke-webhook-check | `code/agent-orchestrator/README.md` |
| `orch-services-service` | orch-chart-services-port | orch-service-port-e2e, deploy-pin-orch-service-port, helmfile-webhook-releases | `code/agent-orchestrator/chart/agent-orchestrator/templates/service-services.yaml` |
| `webhook-events-schema` | webhook-schema-settings | webhook-mappings-repo, webhook-event-store, webhook-ui-api | `code/agents-webhook/src/agents_webhook/migrations/0001_init.sql` |
| `webhook-settings-env` | webhook-schema-settings | webhook-ingest-http, webhook-dispatch-worker, webhook-chart-workloads | `code/agents-webhook/src/agents_webhook/settings.py` |
| `webhook-normalized-event` | webhook-normalize | webhook-event-store, webhook-ingest-http, webhook-prompt-render | `code/agents-webhook/src/agents_webhook/normalize.py` |
| `webhook-mapping-match` | webhook-mappings-repo | webhook-ingest-http, webhook-ui-api, webhook-dispatch-worker | `code/agents-webhook/src/agents_webhook/db/mappings.py` |
| `webhook-event-queue` | webhook-event-store | webhook-ingest-http, webhook-dispatch-worker, webhook-ui-api | `code/agents-webhook/src/agents_webhook/db/events.py` |
| `webhook-prompt` | webhook-prompt-render | webhook-dispatch-worker, webhook-ui-api | `code/agents-webhook/src/agents_webhook/prompt.py` |
| `webhook-ingest-api` | webhook-ingest-http | webhook-chart-network, webhook-api-e2e, smoke-webhook-check | `code/agents-webhook/README.md` |
| `webhook-api` | webhook-ui-api | webhook-openapi-readme, webhook-api-e2e, web-webhook-api-client | `code/agents-webhook/README.md` |
| `webhook-cli` | webhook-cli-entrypoints | webhook-chart-workloads, webhook-api-e2e | `code/agents-webhook/src/agents_webhook/cli.py` |
| `agents-webhook-chart` | webhook-chart-workloads | webhook-chart-network, webhook-ci-images, helmfile-webhook-releases | `code/agents-webhook/chart/agents-webhook/values.yaml` |
| `agents-webhook-image` | webhook-ci-images | helmfile-webhook-releases | `code/agents-webhook/.github/workflows/ci.yaml` |
| `trigger-ui-page-pattern` | web-trigger-ui-kit | web-webhook-events-page, web-webhook-mappings | `code/agents-web/src/triggers/index.ts` |
| `web-webhook-client` | web-webhook-api-client | web-webhook-events-page, web-webhook-mappings, web-webhook-menu-entry | `code/agents-web/src/webhooks/api.ts` |

Cross-epic (in `docs/plans/contracts.json`): the agents-common parts, `orch-service-tokens`, `orch-services-service` and `trigger-ui-page-pattern` list agents-schedule-microservice as consumer; `webhook-api`, `agents-webhook-chart` and `agents-webhook-image` list agents-web and agents-helmfile. Consumed from other epics: `agents-web-url-layout`, `agents-web-backends-config`, `agents-web-backend-registry`, `agents-web-openapi-vendor`, `agents-web-chart` (owner frontend-decoupling), `orch-presets-api` and `orch-cluster-create-api` (owner cluster-presets, done).

## Review focus

- orch-service-port-auth (panel): the service port must never serve `/agent/v1`, WebSockets or routes outside the list; the main port's `SourceAllowlist` and the agent port must behave exactly as before; token hashes compared in constant time; no token value in logs.
- webhook-event-store: dedup under concurrent deliveries (two ingest replicas), guarded transitions, the partial unique index, FIFO and caps in one claim query.
- common-run-tracker and webhook-dispatch-worker: crash points between create, record and post never produce a second cluster or prompt.
- webhook-ingest-http: raw-body HMAC, 413 before parsing, 404 for an unconfigured source, no secret in logs.
- webhook-prompt-render: every event field escaped; a template cannot pull unescaped text.
- webhook-chart-workloads: the ingest Deployment has no oauth2-proxy annotations; the api has them.

## Left to the builder

- Internal module layout inside each package beyond the files named in tasks, as long as the contract files stay where the Contracts table says.
- Pool sizes, poll intervals below 5 s, log formats.
- agents-web component structure inside `src/webhooks/` and `src/triggers/`, within frontend-decoupling's conventions.
- The exact CI job layout of agents-common (lint and test at least).

## Assumptions and unknowns

- frontend-decoupling delivers the registry, runtime config and openapi vendoring as registered (`agents-web-backend-registry`, `agents-web-backends-config`, `agents-web-openapi-vendor`); if its final shape differs, web-webhook-menu-entry, web-webhook-api-client and helmfile-web-webhooks-entry follow the registered contract. Probe: read its tasks before the run.
- configuration-improvements may not have added the Clusters entry when this epic runs; the Webhooks entry then sits just above Presets (D11).
- GitLab may be unused in the lab; the endpoint ships anyway and answers 404 while its token is unset (D3).
- The CI robot secrets for Harbor are the same as agent-orchestrator's; the user sets them on the new repo if the agent cannot (webhook-ci-images ends `blocked`, whoCanClear user).
- Local testcontainers Postgres failed in the frontend-decoupling baseline (Docker readiness); implementers rely on a working Docker or CI.

## Open questions
- Q1: Dedup: while the earlier event with the same key is new, does the newer payload replace it (keeping its FIFO place), and while it is in-progress, is the newer one sent as an update message to the same cluster and recorded handled? [recommended: yes, latest wins while new; update message while in-progress (D5)]
- Q2: Do limits mean concurrency caps (3 in progress, 1 per mapping, FIFO with alerts first), a 5 MiB body cap and a 500-event queue cap, with no per-minute rate limit? [recommended: yes (D6)]
- Q3: Is incoming auth tatara-new parity (GitHub HMAC, GitLab token, Grafana bearer), one SOPS secret per source, with public ingest at https://lab.szymonrichert.pl/webhooks/<source> in its own Deployment without SSO? [recommended: yes (D3, D12)]
- Q4: Are events ignored (still listed with the reason) when no mapping matches, the actor is a bot login, the action is closed/merged/labeled/title-only edit, the alert is resolved, a duplicate, or the queue is full? [recommended: yes (D4)]
- Q5: Add a fifth status failed (create, message or turn failed, or a 1 h timeout) with a reason? [recommended: yes (D5 of the brief, D8)]
- Q6: Is an event handled when its first turn completes, with the service never deleting clusters (cleanup via configuration-improvements autoclose)? [recommended: yes (D8)]
- Q7: Is a mapping (source, kind, repo or any, Grafana label subset) to a preset plus optional prompt template, most specific wins, created from an event row and removable, not re-queuing past events? [recommended: yes (D7)]
- Q8: Add an optional global author allowlist that ignores issue and comment events from other authors when set (off by default)? [recommended: yes (D4)]
- Q9: Use bearer service tokens on a dedicated orchestrator port 8002 (sha256 hashes in ORCH_SERVICE_TOKENS) serving only the routes a trigger service needs? [recommended: yes (D10)]

## Irreversible operations in scope

- Creating public GitHub repos `szymonrychu/agents-common` and `szymonrychu/agents-webhook` (D15); covered by approval A6, done by the meta epic agents-webhook-component before this run.
- Pushing tag `v0.1.0` on agents-common's main merge commit (common-release-v0-1-0); tags are never re-pointed. Approval A10.
- Publishing images and charts to Harbor from the new repo's main CI (webhook-ci-images). Approval A8.
- `mise run apply` in agents-helmfile: creates the CNPG cluster `agents-webhook-db`, the agents-webhook release and its public Ingress paths `/webhooks/{github,gitlab,grafana}`, and rotates nothing (apply-smoke-webhook). Approvals A7, A8.
- Writing new SOPS secrets (source secrets, service token) with `scripts/bootstrap-secrets.sh` (helmfile-service-token); new values only, no existing secret rotated. Approval A8.
