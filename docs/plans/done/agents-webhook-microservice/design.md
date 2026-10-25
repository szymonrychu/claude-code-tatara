# agents-webhook microservice design

## Summary

A new Python service, agents-webhook, with its own CNPG Postgres database, receives GitHub and
GitLab PR/MR, issue and comment webhooks and Grafana alerts on per-webhook public endpoints
`https://lab.szymonrichert.pl/webhook/<suffix>`, each created with exactly one type, one required
preset and HTTP basic-auth credentials. Events are stored in a FIFO queue table with content-aware
dedup and limits and start agent clusters from the endpoint's preset through the orchestrator API
("scheduler API" in the request). A preset may opt in to agent reuse: while the agent handling an
item runs, later events for that item go to it instead of a new cluster. A Webhooks page in the web
UI, between Clusters and Presets, manages the endpoints and lists recent events with their status.
Headline decisions: a library component agents-common holds what agents-schedule-microservice
reuses (D1, D19); the public ingest runs in its own Deployment without SSO (D2); per-webhook
endpoints with basic auth are the only ingest path (D3, D7); agent reuse is a preset field (D16,
D17); the orchestrator gains bearer service tokens on a dedicated internal port (D10); the UI lands
in agents-web (D11).

Re-planned in place on 2026-10-25 (user requirement in the scratchpad `wh-userreq2.md`, quoted in
D3, D7, D16, D17): per-webhook endpoints replace the per-source `/webhooks/<source>` HMAC and token
ingest and the mapping table; agent reuse added. Done tasks are untouched.

## Intent and why

The user wants more of tatara-new's behaviour in this system: forge and alert events start agent
clusters automatically, as tatara-new's operator did with webhooks, a queue and Tasks. Here the
unit of work is an agent cluster from a preset, the services talk only over HTTP, and each owns its
database (AGENTS.md hard rules). One URL per assignment makes the routing explicit (the URL is the
mapping) and lets each forge or Grafana contact point carry its own credentials. Agent reuse keeps
one agent on one PR, MR, issue or alert for as long as it runs. The webhook service is the first
trigger service; the schedule service follows and reuses its parts.

## Goals

- G1: `POST https://lab.szymonrichert.pl/webhook/<suffix>` accepts an event only with that endpoint's basic-auth credentials and answers 202 for accepted or ignored, 401 for an unknown suffix or wrong credentials (identical), 413 over 5 MiB, 429 after repeated failed authentications, 5xx only when the DB write fails.
- G2: endpoints of type `github-pr`, `github-issue`, `gitlab-mr`, `gitlab-issue` and `grafana-alert` normalise their provider events (PR/MR created and updated, issue created and updated, comments added, Grafana alerts) into one event shape with a dedup key: `<platform>/<repo>/mr/<n>`, `<platform>/<repo>/issue/<n>`, `grafana/<sha256 of the sorted commonLabels>[:16]`.
- G3: events are a FIFO queue (alerts first, then by sequence) with dedup per D5 and limits per D6.
- G4: an endpoint event creates a cluster from the endpoint's preset, posts the rendered prompt and tracks the first turn; with agent reuse on, a later event for the same item goes to the cluster still running for it (D16); statuses new, in-progress, handled, ignored, failed, each with a reason where relevant.
- G5: `/webhooks/api/v1` creates, lists, rotates and deletes endpoints (URL and password shown once) and lists events; documented in the README, committed `openapi.json`, drift-tested.
- G6: the Webhooks UI entry sits between Clusters and Presets and manages endpoints and recent events; the preset form has a Reuse running agent switch.
- G7: the orchestrator accepts the service's calls with a bearer service token on port 8002; every other caller sees no change; presets carry the optional `reuse_running_agent` field.
- G8: released, pinned and applied with its CNPG database; the live smoke is green.

## Non-goals

- Forge write-back (comments, statuses), cluster deletion, rate limiting of successful deliveries, editing an endpoint's type or preset after creation (delete and recreate), revealing a password after creation, any change to the shape of existing `/api/v1` routes beyond the additive spec field.

## Anti-goals

- The public ingest Deployment reaching the UI API or carrying the SSO sidecar's session.
- A plaintext password stored anywhere, logged, or returned outside the create and rotate responses.
- A response that lets a caller tell an existing suffix from a missing one.
- A restart or a duplicate delivery posting a second prompt or starting a second cluster for the same event.
- An event lost when the cluster it was routed to goes away mid-delivery.
- Event text reaching an agent as instructions instead of framed, escaped data.
- Any new caller of the orchestrator main port, or the CIDR allowlist loosened.
- Copies of the DB, settings, client or reuse code in agents-schedule later (the reason for agents-common).

## Constraints

- Python only for services; TypeScript only in agents-web (AGENTS.md hard rules).
- Services talk only through HTTP; each table has one writer except queue tables, which change rows only through status-guarded updates (`code/agent-orchestrator/MEMORY.md` L19).
- `/api/v1` of the orchestrator is additive-only (`code/agent-orchestrator/MEMORY.md` L17).
- The oauth2-proxy injector has no skip-auth annotation (`infrastructure/code/containers/apps/oauth2proxy-injector/webhook.go` L404-450), so a public endpoint cannot share a pod with SSO.
- The orchestrator `SourceAllowlist` reads only the socket peer; live `ORCH_ALLOWED_CIDRS` is `127.0.0.1/32` (`code/agents-helmfile/values/agent-orchestrator/common.yaml`).
- agents-common v0.1.0 is tagged and published; tags are never re-pointed, so new shared code ships as v0.2.0 (D19).
- Live applies run in the orchestrator's main session; the classifier refuses them in subagents, so no AC evidence runs `mise run apply` (apply-smoke-webhook).
- Raw `sops` is blocked in agent shells; secret files change through the project's secret helper.

## Decisions

### D1: New components agents-common (library) and agents-webhook (service)

agents-common is a Python library repo pinned by git tag (`agents-common @ git+https://github.com/szymonrychu/agents-common@v0.1.0`), the any-mcp pattern. It holds `settings`, `db`, `runtime`, `orchestrator`, `fake_orchestrator`, `runs` and the `testing` plugin (built and released, tasks common-*). agents-webhook depends only on a tag. Alternatives: agents-schedule importing agents-webhook (couples two services' releases), copying code (two drifting copies). Serves working answer Q10. Approvals A1, A10.

### D2: One image, three Deployments, migrate initContainer

`agents-webhook ingest` (public, port 8000, no SSO annotations, no orchestrator token), `agents-webhook api` (UI API, port 8000, oauth2-proxy annotations as agent-orchestrator's api), `agents-webhook worker` (singleton dispatcher and tracker); `agents-webhook migrate` runs as the initContainer of each. The ingest Deployment serves only `/webhook/{suffix}`, `/healthz`, `/readyz`; the api only `/webhooks/api/v1/*`, `/healthz`, `/readyz`. Serves Q3 (kept) and Q25. Approvals A1, A7.

### D3: Ingest is per-webhook endpoints with HTTP basic auth

User request (2026-10-25), verbatim: "Add an ability to create webhook url in form of https://<base>/webhook/<random string>. Such webhook will be defined as one of the supported types on creation. When creating such webhook url user can provide: <random string> url suffix (by default it's random, user can supply any unique string); basic-auth credentials (by default random u/p are provided, user can override both). User is required to provide a preset that will be used to run the webhook along with a type of the webhook (grafana alert/gitlab-issue/gitlab-mr/github-issue/github-pr). only these sink endpoints will be used onwards for any webhooks and such url will be unique for each assignment."

So `POST /webhook/{suffix}` is the only ingest path; the per-source `/webhooks/{github,gitlab,grafana}` routes, the GitHub HMAC, GitLab token and Grafana bearer checks and their three SOPS secrets are dropped (old D3, gate Q3's auth part; the secrets bootstrapped by done task helmfile-service-token are removed by helmfile-drop-source-secrets, never applied live). Per request, in order: failed-auth limit (429, D18), `authenticate(suffix, Authorization)` (401, D18), the 5 MiB cap (413, after auth so an anonymous caller cannot make the pod buffer a body), GitHub `ping` (202 pong), JSON parse (400), `normalize(endpoint.type, ...)` (D4), `classify`, record, NOTIFY, 202 `{id, status, reason}`; a DB failure 503 so the forge retries. GitHub and GitLab send basic auth from credentials in the hook URL; Grafana's webhook contact point has username and password fields. Alternatives: keep HMAC per source alongside (rejected: "only these sink endpoints will be used onwards"); per-endpoint HMAC secrets (rejected: Grafana and the request both name basic auth). Serves Q13, Q14, Q17. Approvals A1, A7, A11.

### D4: Normalised event per endpoint type and ignore rules

`normalize(endpoint_type, headers, payload) -> NormalizedEvent{type, source, kind mr|issue|comment|alert, action, repo, number, title, body, comment_body, url, author, actor, labels, delivery_id, dedup_key, priority}`; alert priority 0, everything else 1. Type to events: `github-pr` pull_request, pull_request_review_comment, pull_request_review, issue_comment on a PR; `github-issue` issues, issue_comment on an issue; `gitlab-mr` Merge Request Hook, Note Hook on an MR; `gitlab-issue` Issue Hook, Note Hook on an issue; `grafana-alert` the alert webhook body. A valid provider event of another type is stored `ignored`, `type_mismatch` (my call: visible in the UI, so a misconfigured hook is diagnosable); anything else `unsupported_event`. Other reasons, stored and listed: `self_event` (actor in `WEBHOOK_BOT_LOGINS`), `author_not_allowed` (issue and comment events when `WEBHOOK_ALLOWED_AUTHORS` is set; Q8 kept, it never depended on mappings), `action_ignored` (closed, merged, labeled, unlabeled, a title-only edit, drafts), `resolved` (Grafana not firing), `duplicate`, `queue_full`, `endpoint_removed`. `no_mapping` and `mapping_removed` no longer exist. Handled actions: MR/PR opened, reopened, synchronize/update, ready_for_review; issue opened, reopened, edited (body); comment created. Serves Q4 (changed as Q17), Q8. Approvals A1, A2.

### D5: Dedup semantics

Keys are per endpoint: `(endpoint_id, dedup_key)` (my call: two endpoints on one repo are two assignments with their own agents). Partial unique index on `events(endpoint_id, dedup_key) WHERE status = 'new'`. On a delivery whose key has a `new` row, its payload, title, body and `updated_at` are replaced (latest wins, it keeps its sequence) and the delivery is stored `ignored`, reason `duplicate`, `duplicate_of` it (gate Q1's first half, kept). A provider redelivery (same `X-GitHub-Delivery` or `X-Gitlab-Event-UUID` on the endpoint) is stored `ignored`, `duplicate` (my call: forges retry on timeouts). A key with an `in-progress` row is decided by the worker under D16 instead of the old "update message while in-progress" rule (gate Q1's second half, replaced by Q19 and Q21). A row claimed between read and update is retried at most 3 times. Serves Q18. Approvals A2.

### D6: Limits and FIFO

At most `WEBHOOK_MAX_IN_PROGRESS` (default 3) first-dispatch events in progress and at most `WEBHOOK_MAX_IN_PROGRESS_PER_ENDPOINT` (default 1, was 1 per mapping) per endpoint; the worker claims the oldest eligible `new` row by `(priority, seq)` with `FOR UPDATE SKIP LOCKED`. Deliveries to a running agent bypass the caps (their cluster already runs). More than `WEBHOOK_MAX_QUEUE` (default 500) `new` rows: the delivery is stored `ignored`, `queue_full`. A run in progress longer than `WEBHOOK_RUN_TIMEOUT_SECONDS` (default 3600) becomes `failed`, `timeout`. No rate limit on successful deliveries; the failed-auth limit is D18. Serves Q23. Approvals A2.

### D7: Endpoints replace mappings

`endpoints{id, suffix unique, type, preset_id, prompt_template (nullable), username, password_hash, created_at, credentials_rotated_at}`, written only by the api. The suffix is `secrets.token_urlsafe(24)` (32 URL-safe chars) by default, or a user string matching `^[A-Za-z0-9._~-]{1,128}$` that no other endpoint has (409 `suffix_taken`). The URL is `WEBHOOK_PUBLIC_BASE_URL + "/webhook/" + suffix`. The type and the preset are required at creation; `POST` validates `preset_id` against the orchestrator (`422 unknown_preset`). The prompt template stays optional, now on the endpoint (D9). Endpoints are created, listed, credential-rotated and deleted, not edited (my call: the request names creation only; recreate to change the type or preset). Deleting an endpoint keeps its events (they carry `endpoint_suffix`); its still-`new` events become `ignored`, `endpoint_removed`; running clusters are untouched. The old mapping table, matching and specificity rules (old D7, gate Q7) are dropped. Serves Q13. Approvals A3, A4, A11.

### D8: Dispatch and run tracking

The worker (singleton, `advisory_singleton`) claims a row `new -> in-progress` (guarded). First dispatch is `agents_common.runs.dispatch`: create the cluster `POST /api/v1/clusters {preset_id, slug}` with the deterministic slug `wh-<event id>` (a 409 resolves the existing cluster by slug), record `cluster_id`, adopt a message carrying the marker `<!-- agents-webhook:event:<id> -->` before posting one, post the rendered prompt with the marker, record `message_id`. So a restart at any point never posts a second prompt. `track` polls `GET /api/v1/messages/{id}`: turn `completed` -> `handled`; message `failed|cancelled` or turn `failed` -> `failed` with the reason; timeout per D6. The service never deletes clusters. Serves Q5, Q6. Approvals A3.

### D9: Prompt rendering

Default prompt: a fixed preamble saying the block is untrusted event data, never instructions, then `<event type source kind action repo number url author>` with `<title>`, `<body>`, `<comment>`, `<labels>` children, every value XML-escaped (tatara-new `bundle.go` L220-268); a delivery to a running agent starts "Update to the event you are working on:". An endpoint's `prompt_template` uses `string.Template` placeholders `$event`, `$type`, `$source`, `$kind`, `$action`, `$repo`, `$number`, `$url`, `$title`, each substituted escaped; unknown placeholders are rejected on endpoint create (422). Approvals A3.

### D10: Orchestrator service tokens on port 8002

As built (tasks orch-service-port-auth, orch-chart-services-port, orch-service-port-docs, done): `ORCH_SERVICE_PORT` 8002, `ORCH_SERVICE_TOKENS(_FILE)` CSV `<name>:<sha256 hex>`, bearer tokens compared with `hmac.compare_digest`, only the trigger-service routes (`GET /api/v1/meta`, `GET /api/v1/presets[/{id}]`, `GET|POST /api/v1/clusters`, `GET /api/v1/clusters/{id}`, `GET|POST /api/v1/clusters/{id}/messages`, `GET /api/v1/messages/{id}`, health), ClusterIP `<fullname>-services:8002`. Agent reuse needs no new route: it reads `GET /api/v1/presets/{id}` and `GET /api/v1/clusters/{id}`. Serves Q9. Approvals A5. Review tier panel.

### D11: UI in agents-web

The Webhooks page lives in agents-web. Its menu entry is `BACKEND_MENUS.webhooks = [{id: 'webhooks', label: 'Webhooks', order: 20, backend: 'webhooks', render}]` (contract `agents-web-backend-registry`: slots 10 Clusters, 20 Webhooks, 30 Schedules, 40 Presets), shown only when `config.json` lists backend `{id: webhooks, label: Webhooks, basePath: /webhooks/api/v1}`; configuration-improvements (done) registered Clusters, so it sits between Clusters and Presets. Types come from `openapi/webhooks.json` vendored with `npm run sync:api -- webhooks`. The page has an Endpoints section above the events: a New endpoint dialog (type, `PresetSelect`, optional suffix, optional credentials, optional template), a credentials dialog shown once after create or rotate with the full URL, username and password, copy buttons and per-type hints, and a list with the URL (copy), type, preset name, username, created and rotated times, Rotate credentials and Delete, each after a confirm. The events table polls every 5 s with status and endpoint filters and shows endpoint, kind, repo and number, title, status chip, reason, cluster slug and update or duplicate links. The preset form gains a Reuse running agent switch (D17). The trigger UI kit (contract `trigger-ui-page-pattern`, done) is reused. Serves Q26. Approvals A4, A10.

### D12: URL layout

One host, `lab.szymonrichert.pl`. UI API at `/webhooks/api/v1` (served natively, no rewrite) behind SSO; public ingest at the `/webhook` Prefix (the request's URL form `https://<base>/webhook/<random string>`), which Kubernetes Prefix matching keeps apart from `/webhooks/...`. agents-webhook thus owns two prefixes, `/webhooks/` and `/webhook/`, a recorded exception to the one-prefix rule of contract `agents-web-url-layout` (my call, from the user's URL form). Two Ingress objects in the chart; neither carries the cert-manager annotation, both use TLS secret `agent-orchestrator-tls`; the api Ingress keeps the node-IP `denySourceRanges`, the ingest Ingress is public. Serves Q25. Approvals A4, A7.

### D13: Deploy

agents-helmfile gets the release pair `agents-webhook-db` (`cnpg/cluster` 0.9.0) and `agents-webhook` (`oci://harbor.szymonrichert.pl/charts/agents-webhook`, pinned `0.1.0-main.<sha7>`, needs the db and the orchestrator), values under `values/agents-webhook{,-db}/`, the DB URL from Secret `agents-webhook-db-cluster-app` key `uri`, `publicBaseUrl` and `trustedProxies` set; the service token from done task helmfile-service-token, the unused source secrets removed (helmfile-drop-source-secrets); the orchestrator pin moves to the build with the service port and the reuse field; agents-web gets the webhooks backend entry; the smoke creates and deletes a temporary endpoint and checks basic auth, the events API and the service port; the orchestrator runs `mise run apply` in its main session, then `mise run diff` and `mise run smoke` prove it. Approvals A8.

### D14: Headless parity

Every capability has a documented route (README `## API`, committed `openapi.json`, drift test) and an API-only e2e (`tests/e2e/test_e2e_api.py` in agents-webhook: real Postgres, the three processes, `agents_common.fake_orchestrator`), covering each endpoint type, every auth path, dedup, each ignore reason, the caps, the queue cap, agent reuse on and off with a discarded cluster, endpoint create, rotate and delete, handled and failed. The orchestrator's reuse field has an API-only test; the service port has a kind e2e check. Approvals A9.

### D15: Repo creation and visibility

The repos were created by the meta epic agents-webhook-component (done). The scaffold tasks add what the scaffold lacks (pyproject, Dockerfile, CI, chart). Harbor `containers/agents-webhook` and `charts/agents-webhook` use the same robot secrets as agent-orchestrator, set with `gh secret set` on the new repo. Approvals A6.

### D16: Agent reuse: route new events to the running agent

User requirement (2026-10-25), verbatim: "Another requirement- as long as an agent handling specific event is running, it will receive any new webhooks/events instead of creating new one." Clarification, verbatim: "(agent reuse is an optional feature, it can be set during preset creation)".

When the endpoint's preset has `reuse_running_agent: true` (D17), a claimed event whose `(endpoint, dedup_key)` has an earlier run with a cluster (platform/repo/mr-id, platform/repo/issue-id, alert labels) is delivered to that cluster as an update message when the cluster is running: `GET /api/v1/clusters/{id}` answers and `desired` is `active`, whether or not the first turn completed (the orchestrator's cluster state is the source of truth; autoclose flips it to `deleting` and so ends reuse). The event is recorded `handled` once its message reaches `sent`, with `update_of` linking the parent run, and bypasses the caps. Only when no running cluster exists for the key does a new cluster start. With the field off or unset, every claimed event starts its own cluster; an event for a key already in progress waits until that run's first turn ends (Q21).

Order and busy agents: rows of one key are claimed one at a time in arrival order (no same-key row may be in progress without a cluster, and no same-key delivery in flight); a delivery while the agent's turn is busy waits in the orchestrator's per-cluster message queue and is never merged with another delivery (my call: each comment carries its own information; only not-yet-claimed `new` rows coalesce, D5).

Discard mid-delivery: when the cluster is gone at check time, the post answers 404 or 409, or the message ends `cancelled` or `failed` before `sent` (the cluster was discarded), the event falls back once to a first dispatch as a new cluster `wh-<id>`, or back to `new` keeping its FIFO place while the caps are full; no event is lost.

Alternative, not recommended: "any event on the same webhook endpoint goes to its running agent" (the endpoint, not the item, is the unit). Rejected as the default because one endpoint usually serves a whole repo or org, so unrelated PRs would pile onto one agent. Serves Q19, Q21, Q22. Approvals A12.

### D17: The reuse_running_agent preset field

`ClusterSpec.reuse_running_agent: bool | None = None` in agent-orchestrator, sparse like `autoclose_after_seconds` (default false: absent from a preset unless set). The orchestrator stores and returns it and never acts on it, so it applies only to trigger-service runs; clusters a user creates ignore it. The webhook worker reads it from the endpoint's preset (`GET /api/v1/presets/{id}`) once per tick when it claims, so a change takes effect for later events (my call). agents-web's preset form gets a Reuse running agent switch (off by default). Alternative: a preset column outside the spec (rejected: a migration and a second body shape for one boolean; presets are sparse specs). Serves Q20. Approvals A12.

### D18: Credential storage, constant-time checks, brute-force and enumeration

Default credentials: username `wh-` + 8 hex, password `secrets.token_urlsafe(32)`; the user may override both, the password with at least `WEBHOOK_MIN_PASSWORD_LENGTH` (16) characters. Only a salted scrypt hash (`hashlib.scrypt`, n=2**14, r=8, p=1, 16-byte salt) is stored; the password appears only in the create and rotate responses (`Cache-Control: no-store`) and the one-time UI dialog, never in a list, a log or a later reveal (my call: a hash cannot be revealed, and a reveal would need a recoverable secret). Rotate issues new credentials and invalidates the old password. Checks: the username with `hmac.compare_digest`, the password through scrypt then `compare_digest`; an unknown suffix or malformed header still runs scrypt against a fixed dummy hash, and every failure (unknown or deleted suffix, missing or malformed header, wrong username or password) answers the same 401 body with `WWW-Authenticate: Basic realm="agents-webhook"`, so suffixes cannot be enumerated by status or timing. Brute force: more than `WEBHOOK_AUTH_FAILURES_PER_MINUTE` (10) failures from one client in a sliding minute answer 429 with `Retry-After` before any DB or hash work; the client is the peer address, or the right-most untrusted `X-Forwarded-For` hop when the peer is in `WEBHOOK_TRUSTED_PROXIES` (the ingress controller's CIDR); the counter is in memory per ingest replica (my call: two replicas double the budget to 20 a minute, still far below a guessable rate for 43-char random passwords). Logs never carry a failed request's suffix, the Authorization header or a password. Serves Q14, Q15, Q16. Approvals A11.

### D19: agents-common v0.2.0

The reuse support is shared, so it ships in agents-common as additive v0.2.0 (tasks common-reuse-running, common-release-v0-2-0): `Preset.spec`, `Preset.reuse_running_agent`, `Cluster.status`, `runs.running_cluster`, `runs.deliver` (post without failing the run when the cluster is gone), `runs.track_delivery` (handled on `sent`, "gone" on cancel), and fake orchestrator helpers (`add_preset(spec=)`, `mark_sent`, `discard_cluster`, `remove_cluster`). v0.1.0 stays as tagged; webhook-scaffold pins v0.1.0 and webhook-reuse-routing moves the pin to v0.2.0, so the service work starts before the new tag. Alternative: the reuse code inside agents-webhook (rejected: agents-schedule would copy it, an anti-goal). Serves Q24. Approvals A10, A12.

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| start-discovery (code, tatara-new, deploy) | ran, `discovery.md` 2026-10-25 | drop-or-forward dedup (`TN/internal/queue/enqueue.go:dedupExists`, `TN/internal/controller/task_events.go`); capacity with FIFO by (priority, seq) (`TN/internal/controller/queue_controller.go:admit`); Grafana firing-only dedup on labels (`TN/internal/webhook/grafana.go:incidentDedupKey`); bot-actor drop (`TN/internal/webhook/server.go:isBotActor`) | CRD queue and per-project routing (`TN/api/v1alpha1/queuedevent_types.go`); agent-side outcome API with forge comments (`TN/internal/restapi/outcome.go`); per-source signature secrets (re-plan 2026-10-25, user requirement) |
| research-code-internal | ran as discovery lane 4, plus the re-plan probes: `ClusterSpec` sparse fields (`code/agent-orchestrator/src/agent_orchestrator/spec.py` L356-378), cluster `desired` values (`db/migrations/0001_init.sql` L7), agents-common `Preset`/`Cluster` models dropping `spec`/`status` (`src/agents_common/orchestrator.py` L36-46), the preset form's sparse pattern (`code/agents-web/src/clusters/clusterSpecForm.ts` L150, L321) | the reuse map below | a preset column outside the spec |
| research-code-external | skipped: tatara-new is the parity target and was read directly | - | - |
| research-papers | skipped: CRUD, queue and HTTP plumbing, no algorithmic core | - | - |
| research-docs | skipped: basic auth and scrypt are standard-library (`hashlib.scrypt`, `hmac.compare_digest`); forge basic-auth support is confirmed by the live smoke and docs task | - | - |
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
| discovery reuse | `scripts/bootstrap-secrets.sh` | helmfile-service-token, helmfile-drop-source-secrets |
| re-plan probe | `ClusterSpec.autoclose_after_seconds` sparse field | orch-preset-reuse-field |
| re-plan probe | `clusterSpecForm.ts` sparse `SetKey` pattern | web-preset-reuse-row |
| re-plan probe | `runs.post_update` fails the run when the cluster is gone | common-reuse-running (`deliver`) |
| re-plan probe | `FakeOrchestrator.complete_turn` sets `sent`; no discard helper | common-reuse-running |
| re-plan probe | `test_secrets.py:_decrypt` in-process decrypt | helmfile-drop-source-secrets |
| discovery do-not-build | SQLAlchemy / alembic | rejected: not built; psycopg 3 and the forward-only migrator (common-db-helpers) |
| discovery do-not-build | prompt field on presets | rejected: not built; prompt sent as a message (common-run-tracker) |
| discovery do-not-build | turn-completion callback in the orchestrator | rejected: not built; polling (common-run-tracker) |
| discovery do-not-build | writes into orchestrator tables | rejected: not built; HTTP only (common-orchestrator-client) |
| discovery do-not-build | skip-auth route in the SSO sidecar | rejected: not built; separate ingest Deployment (webhook-chart-workloads) |
| discovery do-not-build | in-chart CNPG | rejected: not built; helmfile cnpg release (helmfile-webhook-releases) |
| discovery fix-as-ac | non-idempotent create+message | common-run-tracker, webhook-dispatch-worker, webhook-reuse-routing |
| discovery fix-as-ac | credential compare in constant time | webhook-endpoints-repo, webhook-ingest-http |
| discovery fix-as-ac | 413 before parsing | webhook-ingest-http |
| discovery fix-as-ac | 202 for accepted and ignored, 5xx only on DB failure | webhook-ingest-http |
| discovery fix-as-ac | untrusted event text framed as data | webhook-prompt-render |
| discovery fix-as-ac | status-guarded updates, SKIP LOCKED claims | webhook-event-store |
| discovery fix-as-ac | public ingest without SSO annotations | webhook-chart-workloads |
| discovery fix-as-ac | orchestrator API additive-only, openapi and README regenerated | orch-service-port-docs, orch-preset-reuse-field |
| discovery ideas | adopted: drop-or-forward dedup | webhook-event-store, webhook-reuse-routing |
| discovery ideas | adopted: capacity with FIFO by (priority, seq) | webhook-event-store, webhook-dispatch-worker |
| discovery ideas | adopted: Grafana dedup on labels, firing only | webhook-normalize |
| discovery ideas | adopted: bot-actor self-event drop | webhook-normalize |
| discovery ideas | rejected: CRD queue and per-project routing | rejected: service-owned DB; per-webhook endpoints are the routing (D7) |
| discovery ideas | rejected: outcome API posting forge comments | rejected: out of scope (Non-goals) |
| discovery ideas | open Q9: Keycloak client-credentials vs service tokens | orch-service-port-auth (D10) |
| frontend-decoupling brief | runtime `config.json` backend entry | web-webhook-menu-entry, helmfile-web-webhooks-entry |
| frontend-decoupling brief | vendored openapi per backend | web-webhook-api-client, web-preset-reuse-row |
| frontend-decoupling brief | one host, path routing, single cert-manager annotation (A4) | webhook-chart-network |
| retro history | no proposal bearing on this re-plan beyond the live-apply rule already in Constraints | apply-smoke-webhook |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 New components agents-common and agents-webhook | common-scaffold, common-db-helpers, common-settings-runtime, common-orchestrator-client, common-run-tracker, common-release-v0-1-0, webhook-scaffold |
| D2 One image, three Deployments | webhook-cli-entrypoints, webhook-chart-workloads |
| D3 Per-webhook endpoints with basic auth | webhook-endpoints-repo, webhook-ingest-http, webhook-schema-settings, helmfile-drop-source-secrets |
| D4 Normalised event per type and ignore rules | webhook-normalize, webhook-ingest-http |
| D5 Dedup semantics | webhook-schema-settings, webhook-event-store |
| D6 Limits and FIFO | webhook-event-store, webhook-dispatch-worker |
| D7 Endpoints replace mappings | webhook-schema-settings, webhook-endpoints-repo, webhook-ui-api, web-webhook-endpoints |
| D8 Dispatch and run tracking | common-run-tracker, webhook-dispatch-worker |
| D9 Prompt rendering | webhook-prompt-render |
| D10 Orchestrator service tokens on port 8002 | orch-service-port-auth, orch-chart-services-port, orch-service-port-e2e, orch-service-port-docs |
| D11 UI in agents-web | web-trigger-ui-kit, web-webhook-api-client, web-webhook-events-page, web-webhook-endpoints, web-webhook-menu-entry |
| D12 URL layout | webhook-chart-network, webhook-ui-api, webhook-ingest-http |
| D13 Deploy | helmfile-service-token, helmfile-drop-source-secrets, deploy-pin-orch-service-port, helmfile-webhook-releases, helmfile-web-webhooks-entry, smoke-webhook-check, apply-smoke-webhook, webhook-ci-images |
| D14 Headless parity | webhook-openapi-readme, webhook-api-e2e, orch-service-port-e2e, orch-preset-reuse-field, webhook-docs-memory |
| D15 Repo creation and visibility | common-scaffold, webhook-scaffold, webhook-ci-images |
| D16 Agent reuse | webhook-event-store, webhook-reuse-routing, webhook-prompt-render, webhook-api-e2e |
| D17 The reuse_running_agent preset field | orch-preset-reuse-field, web-preset-reuse-row, deploy-pin-orch-service-port |
| D18 Credentials, constant time, brute force, enumeration | webhook-endpoints-repo, webhook-ingest-http, webhook-ui-api, web-webhook-endpoints |
| D19 agents-common v0.2.0 | common-reuse-running, common-release-v0-2-0, webhook-reuse-routing |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `agents-common-db` | common-db-helpers | webhook-schema-settings, webhook-endpoints-repo, webhook-event-store | `code/agents-common/src/agents_common/db/__init__.py` |
| `agents-common-settings-runtime` | common-settings-runtime | webhook-schema-settings, webhook-dispatch-worker, webhook-cli-entrypoints | `code/agents-common/src/agents_common/settings.py` |
| `agents-common-orchestrator-client` | common-orchestrator-client | common-run-tracker, webhook-ui-api, webhook-dispatch-worker | `code/agents-common/src/agents_common/orchestrator.py` |
| `agents-common-fake-orchestrator` | common-orchestrator-client, common-reuse-running | webhook-ui-api, webhook-dispatch-worker, webhook-reuse-routing, webhook-api-e2e | `code/agents-common/src/agents_common/fake_orchestrator.py` |
| `agents-common-run-tracker` | common-run-tracker | webhook-event-store, webhook-dispatch-worker | `code/agents-common/src/agents_common/runs.py` |
| `agents-common-reuse` | common-reuse-running | webhook-reuse-routing; agents-schedule-microservice | `code/agents-common/src/agents_common/runs.py` |
| `agents-common-lib` | common-release-v0-1-0, common-release-v0-2-0 | webhook-scaffold, webhook-reuse-routing | `code/agents-common/pyproject.toml` |
| `orch-service-tokens` | orch-service-port-auth | orch-chart-services-port, orch-service-port-e2e, orch-service-port-docs, helmfile-service-token, smoke-webhook-check | `code/agent-orchestrator/README.md` |
| `orch-services-service` | orch-chart-services-port | orch-service-port-e2e, deploy-pin-orch-service-port, helmfile-webhook-releases | `code/agent-orchestrator/chart/agent-orchestrator/templates/service-services.yaml` |
| `preset-reuse-running-agent` | orch-preset-reuse-field | web-preset-reuse-row, webhook-reuse-routing; agents-schedule-microservice | `code/agent-orchestrator/src/agent_orchestrator/spec.py` |
| `webhook-events-schema` | webhook-schema-settings | webhook-endpoints-repo, webhook-event-store, webhook-ui-api | `code/agents-webhook/src/agents_webhook/migrations/0001_init.sql` |
| `webhook-settings-env` | webhook-schema-settings | webhook-ingest-http, webhook-dispatch-worker, webhook-chart-workloads | `code/agents-webhook/src/agents_webhook/settings.py` |
| `webhook-normalized-event` | webhook-normalize | webhook-event-store, webhook-ingest-http, webhook-prompt-render | `code/agents-webhook/src/agents_webhook/normalize.py` |
| `webhook-endpoints` | webhook-endpoints-repo | webhook-event-store, webhook-ingest-http, webhook-ui-api, webhook-dispatch-worker | `code/agents-webhook/src/agents_webhook/db/endpoints.py` |
| `webhook-event-queue` | webhook-event-store | webhook-ingest-http, webhook-dispatch-worker, webhook-reuse-routing, webhook-ui-api | `code/agents-webhook/src/agents_webhook/db/events.py` |
| `webhook-prompt` | webhook-prompt-render | webhook-dispatch-worker, webhook-reuse-routing, webhook-ui-api | `code/agents-webhook/src/agents_webhook/prompt.py` |
| `webhook-ingest-url` | webhook-ingest-http | webhook-chart-network, webhook-api-e2e, smoke-webhook-check; agents-helmfile | `code/agents-webhook/README.md` |
| `webhook-api` | webhook-ui-api | webhook-openapi-readme, webhook-api-e2e, web-webhook-api-client, smoke-webhook-check | `code/agents-webhook/README.md` |
| `webhook-cli` | webhook-cli-entrypoints | webhook-chart-workloads, webhook-api-e2e | `code/agents-webhook/src/agents_webhook/cli.py` |
| `agents-webhook-chart` | webhook-chart-workloads | webhook-chart-network, webhook-ci-images, helmfile-webhook-releases | `code/agents-webhook/chart/agents-webhook/values.yaml` |
| `agents-webhook-image` | webhook-ci-images | helmfile-webhook-releases | `code/agents-webhook/.github/workflows/ci.yaml` |
| `trigger-ui-page-pattern` | web-trigger-ui-kit | web-webhook-events-page, web-webhook-endpoints | `code/agents-web/src/triggers/index.ts` |
| `web-webhook-client` | web-webhook-api-client | web-webhook-events-page, web-webhook-endpoints, web-webhook-menu-entry | `code/agents-web/src/webhooks/api.ts` |

Cross-epic (in `docs/plans/contracts.json`): the agents-common parts, `orch-service-tokens`, `orch-services-service`, `trigger-ui-page-pattern`, `agents-common-reuse` and `preset-reuse-running-agent` list agents-schedule-microservice as consumer; `webhook-api`, `webhook-ingest-url`, `agents-webhook-chart` and `agents-webhook-image` list agents-web and agents-helmfile. Consumed from other epics: `agents-web-url-layout` (with the recorded `/webhook/` exception, D12), `agents-web-backends-config`, `agents-web-backend-registry`, `agents-web-openapi-vendor` (owner frontend-decoupling), `orch-presets-api` and `orch-cluster-create-api` (owner cluster-presets), `orch-cluster-autoclose` (owner configuration-improvements; it ends reuse, D16).

## Cross-epic impact: agents-schedule-microservice

Not re-planned here; what its plan must change when it runs:

- Consumed contracts unchanged in shape: `agents-common-lib` v0.1.0, `preset-mapping-model`, `trigger-ui-page-pattern`, `orch-service-tokens`, `orch-services-service`. No contract it consumes was dropped (the webhook mapping table was internal, never a contract).
- New, recommended (Q20): a scheduled run honours `reuse_running_agent` by the same rule keyed by the schedule: if the schedule's latest run has a cluster that `runs.running_cluster` reports running and the preset opts in, the fire posts the prompt there (`runs.deliver`, `runs.track_delivery`) instead of creating a cluster. Tasks to change: scaffold-project-and-cli (pin `agents-common@v0.2.0`), run-dispatcher (the reuse branch and the fallback), run-outcome-tracker (`track_delivery` for reused runs), runs-repository (latest run per schedule, per-schedule order), kind-e2e-api (reuse on and off), api-docs-and-openapi and its README (the rule). New consumed contracts: `agents-common-reuse`, `preset-reuse-running-agent`.
- Wording only: its README and design say "similar to agents-webhooks (maps cronjob to preset)"; agents-webhook now maps a URL to a preset, so no shared mapping model exists to mirror.
- Menu order unchanged: Clusters 10, Webhooks 20, Schedules 30, Presets 40.

## Review focus

- webhook-endpoints-repo and webhook-ingest-http (full): one failure path for every auth failure, the dummy hash, auth before the body read, 429 before any DB or hash work, `X-Forwarded-For` honoured only from trusted proxies, no suffix, header or password in logs.
- webhook-event-store: dedup under concurrent deliveries (two ingest replicas), guarded transitions, the partial unique index, FIFO, caps and per-key order in one claim query.
- webhook-reuse-routing and common-reuse-running: the running check, order per key, no lost event when the cluster goes away between the check, the post and `sent`; crash points never post twice.
- webhook-ui-api and web-webhook-endpoints: the password only in create and rotate responses and the one-time dialog, `Cache-Control: no-store`.
- webhook-prompt-render: every event field escaped; a template cannot pull unescaped text.
- webhook-chart-workloads: the ingest Deployment has no oauth2-proxy annotations and no orchestrator token; the api has the annotations.
- orch-preset-reuse-field: additive only; the orchestrator never acts on the field.

## Left to the builder

- Internal module layout inside each package beyond the files named in tasks, as long as the contract files stay where the Contracts table says.
- Pool sizes, poll intervals below 5 s, log formats, the limiter's data structure.
- How claim_next expresses the per-key rule in SQL, within the AC.
- agents-web component structure inside `src/webhooks/`, within frontend-decoupling's conventions.

## Assumptions and unknown facts

- GitHub and GitLab send HTTP basic auth from `user:password@` in the hook URL, and Grafana's webhook contact point sends its basic-auth fields. Confirmed by the live check of smoke-webhook-check (Grafana path) and by the user wiring a forge after apply; webhook-docs-memory documents it from the providers' docs.
- The ingress controller's source CIDR for `WEBHOOK_TRUSTED_PROXIES` is probed read-only in helmfile-webhook-releases (node pod CIDRs); until set, the limiter keys on the controller address, which is safe but coarse.
- A discarded cluster's row is removed, so `GET /api/v1/clusters/{id}` answers 404 (`code/agent-orchestrator/src/agent_orchestrator/db/clusters.py`); common-reuse-running treats both 404 and `deleting` as not running.
- The CI robot secrets for Harbor are the same as agent-orchestrator's; the user sets them on the new repo if the agent cannot (webhook-ci-images ends `blocked`, whoCanClear user).
- Local testcontainers Postgres failed in the frontend-decoupling baseline (Docker readiness); implementers rely on a working Docker or CI.

## Open questions

- Q1: Dedup: while the earlier event with the same key is new, does the newer payload replace it (keeping its FIFO place), and while it is in-progress, is the newer one sent as an update message to the same cluster and recorded handled? [answer: first half kept; second half superseded by Q19 and Q21 (re-plan 2026-10-25)]
- Q2: Do limits mean concurrency caps (3 in progress, 1 per mapping, FIFO with alerts first), a 5 MiB body cap and a 500-event queue cap, with no per-minute rate limit? [answer: superseded by Q23 (per endpoint instead of per mapping)]
- Q3: Is incoming auth tatara-new parity (GitHub HMAC, GitLab token, Grafana bearer), one SOPS secret per source, with public ingest at https://lab.szymonrichert.pl/webhooks/<source> in its own Deployment without SSO? [answer: own public Deployment without SSO kept; auth and paths superseded by Q13-Q17 and Q25]
- Q4: Are events ignored (still listed with the reason) when no mapping matches, the actor is a bot login, the action is closed/merged/labeled/title-only edit, the alert is resolved, a duplicate, or the queue is full? [answer: superseded by Q17 (type_mismatch replaces no_mapping)]
- Q5: Add a fifth status failed (create, message or turn failed, or a 1 h timeout) with a reason? [answer: yes (working answer, kept)]
- Q6: Is an event handled when its first turn completes, with the service never deleting clusters (cleanup via configuration-improvements autoclose)? [answer: yes (working answer, kept); a delivery to a running agent is handled when sent (Q22)]
- Q7: Is a mapping (source, kind, repo or any, Grafana label subset) to a preset plus optional prompt template, most specific wins, created from an event row and removable, not re-queuing past events? [answer: superseded by Q13 (endpoints replace mappings)]
- Q8: Add an optional global author allowlist that ignores issue and comment events from other authors when set (off by default)? [answer: yes (working answer, kept; independent of mappings)]
- Q9: Use bearer service tokens on a dedicated orchestrator port 8002 (sha256 hashes in ORCH_SERVICE_TOKENS) serving only the routes a trigger service needs? [answer: yes (built)]
- Q10: Put shared code in a new library component agents-common pinned by git tag v0.1.0? [answer: yes (built and tagged)]
- Q11: Create szymonrychu/agents-common and szymonrychu/agents-webhook as public repos with workbench:component-add in the meta epic agents-webhook-component? [answer: yes (done)]
- Q12: Use Harbor containers/agents-webhook and charts/agents-webhook with the same HARBOR_USERNAME/HARBOR_PASSWORD CI secrets as agent-orchestrator? [answer: yes (working answer, kept)]
- Q13: Is an endpoint https://lab.szymonrichert.pl/webhook/<suffix> with a 32-char random URL-safe suffix by default or a unique user suffix matching [A-Za-z0-9._~-]{1,128}, exactly one of the five types, one required preset and an optional prompt template, created, listed, credential-rotated and deleted but never edited (recreate to change type or preset)? [recommended: yes (D7)]
- Q14: Are credentials a random username wh-<8 hex> and a 43-char random password by default, both overridable (password at least 16 chars), stored only as a salted scrypt hash, with the password shown once at create or rotate and never revealable later? [recommended: yes (D18)]
- Q15: Do an unknown or deleted suffix, a missing or malformed header and a wrong username or password all get the identical 401 with WWW-Authenticate Basic, with a dummy scrypt for unknown suffixes and auth checked before the body is read, so suffixes cannot be enumerated? [recommended: yes (D18)]
- Q16: Against brute force, do more than 10 failed authentications a minute from one client get 429 with Retry-After (in memory per ingest replica, client from X-Forwarded-For only behind WEBHOOK_TRUSTED_PROXIES), with still no limit on successful deliveries? [recommended: yes (D18)]
- Q17: Are the per-source HMAC/token checks and their three already-bootstrapped (never applied) SOPS secrets dropped, an event of another type at an endpoint stored ignored type_mismatch, and endpoint_removed replacing no_mapping/mapping_removed? [recommended: yes (D3, D4)]
- Q18: Are dedup keys scoped per endpoint, with latest-wins while new kept and exact provider redeliveries (X-GitHub-Delivery, X-Gitlab-Event-UUID) ignored as duplicate? [recommended: yes (D5)]
- Q19: With reuse on, is a new event whose dedup key (platform/repo/mr-id, platform/repo/issue-id, alert labels) matches an event whose cluster is still running (GET /clusters/{id} on the service port answers and it is not deleting or discarded, whether or not the first turn completed) delivered to that cluster as an update message and recorded handled with a link to the parent run, a new cluster starting only when none runs for the key, autoclose ending it; rather than the alternative reading that any event on the same endpoint goes to its running agent? [recommended: yes, per item key, not per endpoint (D16)]
- Q20: Is reuse opt-in per preset as the sparse optional spec field reuse_running_agent (default false), ignored by the orchestrator so it applies only to trigger-service runs (user-created clusters ignore it), read from the preset when an event is claimed, and honoured by agents-schedule too with the same rule keyed by the schedule? [recommended: yes (D17; schedule epic note in design)]
- Q21: With reuse off, does an event for a key already in progress wait until that run's first turn ends and then start its own cluster (replacing the old update-message-while-in-progress rule)? [recommended: yes (D16)]
- Q22: Are deliveries for one key sent one at a time in arrival order, queued in the orchestrator while the agent is busy and never merged, handled once the message is sent, and when the cluster is discarded before or during delivery does the event fall back to a new cluster with nothing lost? [recommended: yes (D16)]
- Q23: Are the limits 3 in progress overall and 1 per endpoint (was per mapping), with deliveries to a running agent bypassing the caps, a 500-event queue cap and a 5 MiB body cap? [recommended: yes (D6)]
- Q24: Does the shared reuse support ship as agents-common v0.2.0 (a new irreversible tag; v0.1.0 untouched), with agents-webhook moving its pin to v0.2.0? [recommended: yes (D19)]
- Q25: Is the public ingest at the singular /webhook/ prefix from your URL form, as a second agents-webhook prefix beside the SSO-protected /webhooks/api/v1, in its own Deployment without SSO? [recommended: yes (D12)]
- Q26: Does the Webhooks page show an Endpoints section (create dialog with type, preset, optional suffix, optional credentials, optional template; a one-time credentials dialog with the full URL, copy buttons and per-type hints; a list with URL, type, preset, username, rotate and delete behind a confirm) above the recent events list with status and endpoint filters, plus a Reuse running agent switch in the preset form? [recommended: yes (D11)]

## Irreversible operations in scope

- Pushing tag `v0.2.0` on agents-common's main merge commit (common-release-v0-2-0); tags are never re-pointed. Approval A12. (`v0.1.0` is already pushed.)
- Publishing images and charts to Harbor from the new repo's main CI (webhook-ci-images). Approval A8.
- `mise run apply` in agents-helmfile, run by the orchestrator in its main session: creates the CNPG cluster `agents-webhook-db`, the agents-webhook release and its public Ingress prefix `/webhook/`, adds the orchestrator service port, and rotates nothing (apply-smoke-webhook). Approvals A7, A8.
- Removing the never-applied source secrets from `values/agents-webhook/default.secrets.yaml` (helmfile-drop-source-secrets); recoverable from git history, no live secret changes. Approval A11.
