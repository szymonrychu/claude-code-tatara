# agents-webhook microservice - discovery brief

Phase 1 of start-development, 2026-10-25. Read-only discovery; nothing designed or planned
here. Shared facts for the sibling epic agents-schedule-microservice live in this file; its
own brief (`../agents-schedule-microservice/discovery.md`) references it.

Path prefixes: `TN/` = `/Users/szymonri/Documents/tatara-new/code/tatara-operator/`,
`AO/` = `code/agent-orchestrator/`, `AH/` = `code/agents-helmfile/`.

## Facts with evidence

### F1. tatara-new: how webhooks are received (parity target)

- There is no separate webhook service and no "scheduler API" in tatara-new. Webhooks, the
  queue and cron all live in the Kubernetes operator, with state in CRDs, not a database.
  The chain is webhook, then Minter, then the QueuedEvent CRD, then DispatcherReconciler,
  then a Task, then an agent pod. A search for `scheduler api|schedulerapi` over Go, md and
  yaml found nothing.
- **Routes** (`TN/internal/webhook/server.go:Mount` L125-128):
  - `POST /operator/webhooks/{project}` serves GitHub and GitLab.
  - `POST /operator/webhooks/{project}/grafana` serves Grafana.
- **Provider detection** is by header (`TN/internal/scm/registry.go:Select` L12-21):
  - `X-GitHub-Event` means GitHub.
  - `X-Gitlab-Event` means GitLab.
  - Anything else gets 400.
- **Request checks** (`server.go:handle` L138-207):
  - The body is capped at 5 MiB; a larger one gets 413 (`readBody`/`maxBodyBytes` L1640-1658).
  - A bad signature gets 401.
  - An event that is accepted or ignored gets 202 (`accept` L1624).
  - A failure the forge should retry gets 500.
- **Signatures**:
  - GitHub uses HMAC-SHA256 over the raw body against `X-Hub-Signature-256` (`sha256=`
    prefix), compared with `hmac.Equal`, and an empty secret is refused
    (`TN/internal/scm/github.go:verifyGitHubSig` L281-299).
  - GitLab compares `X-Gitlab-Token` in constant time (`TN/internal/scm/gitlab.go:DetectAndVerify`
    L101-111).
  - Grafana compares `Authorization: Bearer <secret>` in constant time and returns 404 unless
    Grafana is enabled (`server.go:handleGrafanaAlert` L1233-1246).
  - The secrets are the `webhookSecret` key of a Kubernetes Secret (`server.go:webhookSecret`
    L1600-1613).
- **Accepted events**:
  - GitHub: `pull_request`, `issues`, `issue_comment` (an MR comment when `issue.pull_request`
    is set), `pull_request_review_comment` (only `created`) and `pull_request_review`
    (`github.go:DetectAndVerify` L109-163).
  - GitLab: Merge Request, Issue and Note hooks (`gitlab.go` L116-129, `glActionAndLabel` L270-300).
  - Actions are normalised to opened, reopened, labeled, unlabeled, closed, synchronize,
    submitted, created, edited and other (`ghNormalizeAction` L271). GitLab `update` becomes
    synchronize.
- **Dropped or ignored events**:
  - The actor is the bot itself (`server.go:isBotActor` L1181).
  - The author is not in the reporter allowlist (`TN/api/v1alpha1/logins.go:IsAllowedReporter` L39).
  - The repo is unknown (`matchRepo` L259).
  - A Grafana alert whose status is not `firing`, so `resolved` is ignored (`server.go` L1252).
  - `pull_request.edited`, `ready_for_review`, review dismissals and GitLab `unapproved`
    (`server.go` L335-341).
  - Drafts are not handled at all.
- **Normalised event**: `scm.WebhookEvent` in `TN/internal/scm/scm.go` L17-71:
  - kind: push, issue, mr, ci or other
  - Repo, Number, IsPR, Action
  - Title, Body, CommentBody, CommentID, IsComment
  - IssueRef, URL
  - AuthorLogin, ActorLogin
  - Labels, HeadSHA, HeadBranch
- **Grafana payload**: `GrafanaAlert{Status, GroupKey, CommonLabels, CommonAnnotations,
  ExternalURL, Alerts[]{Labels, Annotations, StartsAt, Fingerprint}}`
  (`TN/internal/webhook/grafana.go` L14-31).

### F2. tatara-new: dedup, limits and FIFO

- **Queue row**: the `QueuedEvent` CRD (`TN/api/v1alpha1/queuedevent_types.go` L200-253).
  - Its spec has `Seq`, `Class` (normal or alert), `DedupKey`, `Priority` and `Payload`.
  - Priority 0 is an incident, 1 a webhook and 2 cron or sweep.
- **Dedup is "drop while in flight"**: the first event wins, later ones are dropped. There
  is no time window and no latest-wins (`TN/internal/queue/enqueue.go:dedupExists` L183-215).
  - An event is suppressed while an unfinished queued event or a live Task carries the same
    key.
  - The row name is deterministic, `qe-`+sha256(project|key)[:16] (`QueuedEventName` L278),
    so a concurrent duplicate fails on AlreadyExists.
- **Events for a live Task are not lost**: they are appended to that Task as pending events,
  capped at 20 with the oldest dropped (`TN/internal/controller/task_events.go` L21, L175).
  The running agent then sees them in its next prompt.
- **Grafana dedup key**: sha256(project + alertname, plus `category` when every alert
  agrees)[:16] (`grafana.go:incidentDedupKey` L128-136).
  - A suppressed refire increments a counter and posts at most one comment per 30 min
    (`server.go:enqueueRefireComment` L1342).
- **Limits are concurrency caps, not request rate limits**
  (`TN/internal/controller/queue_controller.go:admit` L350ff, L711-714):
  - The alert pool's capacity defaults to 1.
  - The normal pool's capacity is `spec.queue.capacity`, else `maxConcurrentAgents`, else 3
    (`TN/api/v1alpha1/project_types.go` L1491-1506).
  - Admission order is (priority, seq) ascending, so FIFO within a priority (`queueOrderBefore`
    L136).
  - Starvation guard: one slot is reserved for priority 2 after it has waited 1h
    (`starvationBudget` L123).
  - Capacity 0 pauses the project.
- **What triggers what**: matching is by repo, author and event. There are no presets.
  - An issue opened, an orphan comment or a trigger label mints an `implement` Task
    (`TN/internal/controller/sweep.go:MintStage` L567).
  - A human PR mints a `review` Task (`ClassifyPR` L1126).
  - A firing alert mints an `incident` Task.
- **Prompt**: a Go text/template XML bundle with `<events>`, `<issue>`, `<merge_request>` and
  `<comments>`. The content is XML-escaped and framed as data, not instructions
  (`TN/internal/prompt/bundle.go` L220-268).
- **Reporting back**: the agent calls `POST /tasks/{t}/outcome` (`TN/internal/restapi/outcome.go`).
  The operator posts comments with a `<!-- requestId -->` idempotency marker
  (`TN/internal/controller/reviewpost.go` L73, L633).
- **Status visibility**: the Task states are new, refined, under-implementation and so on
  (`TN/api/v1alpha1/task_types.go` L231-238). The webhook result labels
  `accepted|ignored|duplicate|created|error|bad_signature` exist only as a metric.
- **No UI**: there is no events or mappings UI. The only view is Grafana dashboards
  (`tatara-observability/dashboards/operator.json`).

### F3. agent-orchestrator: the API a trigger service calls

- **Presets**:
  - Routes: `GET|POST /api/v1/presets` and `GET|PUT|DELETE /api/v1/presets/{id}`
    (`AO/src/agent_orchestrator/api/presets.py` L76-134).
  - Schema: `PresetView{id, name, is_default, spec, created_at, updated_at}`
    (`AO/src/agent_orchestrator/api/schemas.py` L22-42).
  - `ClusterSpec` (`AO/src/agent_orchestrator/spec.py:ClusterSpec` L124-141) has **no prompt,
    initial-message or template field** and uses `extra="forbid"`.
- **Start from a preset**: `POST /api/v1/clusters {"preset_id", "slug"?}` returns 201
  `ClusterView` with its `id` (`AO/src/agent_orchestrator/api/clusters.py:create_cluster` L148,
  `_create_from_preset` L189-212).
  - A slug that is already taken gets 409 `conflict` (L186).
  - A slug is a DNS-1123 label of at most 40 characters (`spec.py:validate_slug` L74).
  - The spec is snapshotted into the cluster at create time; nothing can override it there.
- **Prompt**: a separate call, `POST /api/v1/clusters/{id}/messages {text}`, returns 202
  `{message_id, status: queued}` (`AO/src/agent_orchestrator/api/messages.py:post_message` L61).
  - It can be sent right after create: the dispatcher holds it until an agent is idle
    (`AO/src/agent_orchestrator/db/queue.py` `_PICK` L196-209).
  - It has no idempotency key.
- **Outcome**: `GET /api/v1/messages/{id}` returns a MessageView (`messages.py` L99, `schemas.py` L129-166).
  - The message `status` is queued, dispatching, verifying, sent, failed or cancelled.
  - Its `turn` carries `{status running|completed|failed, completed_at, final_text}`.
  - Reference poller: `AO/bench/runner.py:_finished` L187 and `_await_message` L193, with SSE
    as a wake-up in `_follow_stream` L210.
  - `ClusterView.summary.state` is working, waiting, booting, error or deleting
    (`AO/src/agent_orchestrator/db/views.py:summarize` L53-76).
- **There is no callback on turn completion**. The only outbound callback is the discard
  hook (`AO/src/agent_orchestrator/reconciler/discard_hook.py:_post_webhook` L108), and it
  fires only when a cluster is deleted.
- **A cluster never ends on its own**:
  - No TTL or auto-delete exists, and the wrapper renders `idle_timeout_seconds: 0`
    (`AO/src/agent_orchestrator/k8s/render.py` L120).
  - The caller must call `DELETE /api/v1/clusters/{id}`, which returns 202.
  - "Autoclose after time" is requested in the configuration-improvements epic.
- **The API has no authentication**:
  - `SourceAllowlist` checks only the socket peer against `ORCH_ALLOWED_CIDRS`
    (`AO/src/agent_orchestrator/api/allowlist.py` L59-94; default `192.168.1.0/24` at
    `AO/src/agent_orchestrator/settings.py` L127). It never reads X-Forwarded-For.
  - The deployed value is `127.0.0.1/32`, because only the oauth2-proxy sidecar may reach
    the api (`AH/values/agent-orchestrator/common.yaml`, `AH/MEMORY.md` 2026-10-24).
  - The README says pod CIDRs are kept out deliberately, so agent pods cannot reach the API.
  - **So a new in-cluster service gets 403 today.** The only existing service auth is the
    agents' HMAC token on port 8001 (`AO/src/agent_orchestrator/api/agent.py:require_agent` L57).
- **The SSO sidecar** (`/Users/szymonri/Documents/infrastructure/code/containers/apps/oauth2proxy-injector/webhook.go`
  L404-450) is injected per pod by annotation.
  - It sets `OAUTH2_PROXY_SKIP_JWT_BEARER_TOKENS=true`, so a Keycloak JWT bearer token may
    pass it.
  - It has a shared `COOKIE_DOMAIN`.
  - It has **no skip-auth-routes annotation**. A public webhook endpoint therefore cannot sit
    in an SSO-annotated pod.
  - The orchestrator Service targets port name `http`, which the injector hands to the
    sidecar (`AO/chart/agent-orchestrator/templates/service.yaml` L9-11).
- **Write rules**:
  - `/api/v1` is additive-only (`AO/MEMORY.md` L17).
  - Each table has one writer; the queue tables are the only multi-writer exception, and
    other services go through HTTP (`AO/MEMORY.md` L19).

### F4. agent-orchestrator: patterns a new Python service copies

- **DB access**:
  - psycopg 3 async with psycopg_pool (`AO/pyproject.toml` L10); no SQLAlchemy or alembic.
  - Pool, NOTIFY and a reconnecting LISTEN are in `AO/src/agent_orchestrator/db/pool.py`
    (`open_pool` L18, `notify` L24, `listen` L28).
- **Migrations**: forward-only SQL files `db/migrations/000N_*.sql`, run under an advisory
  lock by `AO/src/agent_orchestrator/db/migrate.py:run_migrations` L24, as the `orch migrate`
  initContainer.
- **Queue tables**: every change is a status-guarded `UPDATE ... WHERE status=<expected>`
  (`AO/src/agent_orchestrator/db/queue.py:_transition` L114, header L1-9). Claims use
  `FOR UPDATE SKIP LOCKED` (L208, L228).
- **Singleton workers**: an advisory lock with a heartbeat
  (`AO/src/agent_orchestrator/runtime/singleton.py:advisory_singleton` L90), run by
  `AO/src/agent_orchestrator/runtime/run.py:run_service` L83.
- **Settings**: pydantic-settings with `env_prefix="ORCH_"` and a `SettingsError` that names
  each bad variable (`AO/src/agent_orchestrator/settings.py` L25, L81-82, L155-172).
- **Tests**: testcontainers Postgres with a migrated template DB (`AO/tests/conftest.py` L27-56).
- **openapi.json** is generated and committed:
  - A drift test fails when it changes (`AO/tests/test_readme_api.py` L65).
  - Every route must be documented in the README (L53).
  - The TypeScript types come from openapi-typescript (`AO/frontend/package.json`
    `gen:api`/`check:api`).

### F5. Frontend today

- **No router**: `App.tsx` switches on `useState<'cluster' | 'presets'>`
  (`AO/frontend/src/App.tsx` L22).
- **Menu**: the hamburger (`AO/frontend/src/layout/TopBar.tsx` MenuIcon L46) opens the
  `AO/frontend/src/layout/SessionsMenu.tsx` drawer.
  - The drawer has a Sessions list and a pinned Settings section built from
    `settingsCategories` (L46-60). Contract `orch-settings-menu` is in `docs/plans/contracts.json`.
  - The only entry today is Presets (`App.tsx` L39). **There is no "Clusters" entry.** The
    configuration-improvements epic adds one "above presets".
- **Serving**: the API base is a fixed `'/api/v1'` (`AO/frontend/src/api/client.ts` L37).
  - The built `dist` is served by the orchestrator process (`AO/src/agent_orchestrator/api/app.py`
    L79-80, `api/spa.py`).
  - Everything is same-origin; there is no CORS.
  - The frontend-decoupling epic (no design yet) is what lets other services own pages.

### F6. Scaffold and deploy

- **`mise run component:add`** (`plugins/workbench/skills/component-add/SKILL.md`,
  `scripts/init_engine/scaffold.py:write`):
  - It writes AGENTS, CLAUDE, MEMORY, ROADMAP, README, `.mise.toml` (python 3.14.6, uv, ruff,
    pytest), `.gitignore` and a smoke test.
  - It writes **no Dockerfile, CI, chart or pyproject**; these must be modelled on agent-orchestrator.
  - A github origin needs an explicit forge confirmation (`--confirm-forge`).
  - The existing origins are `github.com/szymonrychu/*` (`.gitmodules`).
- **agent-orchestrator scaffold to model on**:
  - `mise.toml` tasks: test, lint, fmt, test:integration, test:e2e, test:chart, lint:chart.
  - Dockerfile: a node stage, then python:3.12-slim, uv, USER 1000.
  - `.github/workflows/ci.yaml` jobs: lint, test, frontend, images, chart, e2e, chart-publish.
    Images go to `harbor.szymonrichert.pl/containers/<name>:<sha7>` using secrets
    `HARBOR_USERNAME`/`HARBOR_PASSWORD`; charts go to `oci://harbor.szymonrichert.pl/charts/<name>`.
  - The chart has one Deployment per `components` entry (`AO/chart/agent-orchestrator/templates/deployment.yaml`)
    and a Postgres source of cnpg, existingSecret, url or parts (`_config.tpl` L4-58).
- **agents-helmfile** (`AH/helmfile.yaml.gotmpl`): all releases are in namespace `agents`.
  - The pattern is a pair of releases: `<name>-db` (chart `cnpg/cluster` 0.9.0) and `<name>`
    (OCI chart, pinned version, `needs: agents/<name>-db`).
  - Values are layered from `values/common.yaml` and `values/<release>/{common,default}.yaml`,
    with SOPS-encrypted `default.secrets.yaml`.
  - The app reads the CNPG Secret `<name>-db-cluster-app`, key `uri`
    (`AH/values/agent-orchestrator/common.yaml`, `AH/values/agent-orchestrator-db/common.yaml`
    initdb).
  - Secrets are bootstrapped by `AH/scripts/bootstrap-secrets.sh`; rendering is tested by
    `AH/tests/test_*_release.py`.
  - mise tasks: lint, test, diff, apply (guarded by lint and test, and the kube-context check),
    smoke.
  - The public host is `lab.szymonrichert.pl` behind Cloudflare (`AH/MEMORY.md` 2026-10-25).

## Known / assumed / unknown

**Known**
- Every fact in F1-F6.
- The orchestrator has every route needed to start a run (create from preset, then post a
  message) and to see it finish (poll the message or its turn).
- Calling it from another pod is blocked by the CIDR allowlist and the SSO sidecar.
- The public webhook endpoint and the SSO-protected UI/API must be in different pods.

**Assumed**
- "Scheduler API" in the request means the orchestrator's `/api/v1`, since nothing else in
  either system has that name.
- One deployment serves one GitHub org, one GitLab instance and one Grafana. tatara-new's
  per-project routing is not needed.

**Unknown**
- Whether a Keycloak client-credentials JWT passes the injected oauth2-proxy (audience and
  issuer checks).
- Whether GitLab is reachable and used at all from this lab.
- Which Python cron library to use (the schedule epic; a research-docs lens).
- The frontend-decoupling design, which decides where the webhook and schedule pages live.

## Questions for the user (preference; recommended answer first)

1. **Dedup semantics.** When an event's key (platform/repo/mr-id, platform/repo/issue-id, or
   the alert labels) matches an earlier one:
   - **Recommended:** while the earlier one is still `new`, the newer payload replaces it and
     keeps its FIFO position (latest wins). While it is `in-progress`, the newer one is
     forwarded as a follow-up message to that same cluster and recorded as `handled`, linked
     to it. This mirrors tatara-new, which appends the event to the live Task.
   - Alternative: pure tatara-new behaviour, where duplicates are `ignored` while in flight.
2. **What "limits" means.**
   - **Recommended:** concurrency caps as in tatara-new: at most N events in-progress at once
     (default 3) and at most 1 per mapping, with the rest waiting FIFO. Also a 5 MiB body
     cap, and a queue-length cap (default 500) beyond which new events are recorded `ignored`
     (reason `queue_full`).
   - No per-minute rate limiting.
3. **Auth of incoming webhooks.**
   - **Recommended:** tatara-new parity: GitHub HMAC `X-Hub-Signature-256`, GitLab
     `X-Gitlab-Token`, Grafana `Authorization: Bearer`. One secret per source, from a SOPS
     Secret in agents-helmfile rather than the UI.
   - The ingest endpoint is public on `lab.szymonrichert.pl/webhooks/<source>`, in its own
     pod without SSO.
4. **Which events are "ignored".**
   - **Recommended:** ignored when no mapping matches, the actor is a configured bot login
     (self-events), the action is closed, merged, edited-title-only or labeled, the Grafana
     status is resolved, it is a duplicate under Q1, or the queue is full.
   - Every ignored event is still listed, with its reason.
5. **Failed runs.** The request names new/in-progress/handled/ignored.
   - **Recommended:** add a fifth status `failed` (create or message failed, or the turn
     failed) with a reason, rather than folding it into handled.
6. **When an event is handled, and cluster cleanup.**
   - **Recommended:** `handled` when the first turn completes. The webhook service never
     deletes clusters; cleanup comes from the preset's autoclose-after-time
     (configuration-improvements epic).
   - Alternative: the service deletes the cluster once the turn completes.
7. **What a mapping matches and what it sends.**
   - **Recommended:** a mapping is (source, kind mr|issue|comment|alert, repo or any, for
     Grafana a label subset) to a preset, plus an optional prompt template.
   - The default template wraps the event as escaped data, as tatara-new's bundle does.
   - The most specific mapping wins, so one event starts one cluster.
   - A mapping can be created from an event row in the recent list.
8. **Author allowlist (prompt-injection guard on public repos).**
   - **Recommended:** an optional global allowlist of author logins. When it is set, issue
     and comment events from others are `ignored`.
9. **Service-to-service auth to the orchestrator.**
   - **Recommended:** add bearer service tokens to the orchestrator: `ORCH_SERVICE_TOKENS`,
     a hash-compared list from a Secret, that bypasses the CIDR allowlist on a dedicated
     internal port, as the agent port does.
   - The alternative, Keycloak client-credentials through the sidecar, depends on an unknown.
10. **Where shared code lives** (also needed by agents-schedule).
    - **Recommended:** a new small library component `agents-common`, pinned by git tag as
      any-mcp is. It holds settings, pool, migrate, guarded-transition helpers, the
      orchestrator client and the trigger/run tracker.
    - Alternatives: agents-schedule depends on the agents-webhook package, or each service
      copies the code.

## Proposed epic dependency order

1. **frontend-decoupling.** It defines how the UI reaches more than one backend: path-routed
   ingress on one host (`/api/v1` to the orchestrator, `/webhooks/api/v1`, `/schedules/api/v1`),
   SSO cookie shared through the sidecar's cookie domain, and how a service adds a menu entry.
2. **configuration-improvements**, a soft dependency.
   - It adds the Clusters menu entry. The webhook entry sits between Clusters and Presets;
     until then it goes just above Presets.
   - It adds autoclose-after-time (Q6).
3. **agents-webhook-microservice.** It owns the shared library (Q10), the orchestrator
   service-token change (Q9) and the helmfile releases.
   - Its backend and helmfile tasks need not wait for 1 or 2. Only its UI tasks depend on
     the frontend-decoupling contract.
4. **agents-schedule-microservice.** It reuses the library, orchestrator client, run tracker
   and UI patterns from 3.

## Plan inputs

### reuse
- orchestrator create-from-preset - `code/agent-orchestrator/src/agent_orchestrator/api/clusters.py:_create_from_preset` - orchestrator client (create cluster with deterministic slug, 409 conflict = already created)
- orchestrator post message - `code/agent-orchestrator/src/agent_orchestrator/api/messages.py:post_message` - dispatch task (send rendered prompt; follow-up message on in-progress dedup)
- message outcome polling - `code/agent-orchestrator/bench/runner.py:_finished` - run tracker (in-progress to handled/failed)
- SSE wake-up - `code/agent-orchestrator/bench/runner.py:_follow_stream` - run tracker (optional wake-up instead of tight poll)
- source allowlist - `code/agent-orchestrator/src/agent_orchestrator/api/allowlist.py:SourceAllowlist` - orchestrator service-token task (bypass point)
- agent token / port gate pattern - `code/agent-orchestrator/src/agent_orchestrator/api/allowlist.py:PortGate` - orchestrator service-token task (dedicated internal port)
- guarded transition - `code/agent-orchestrator/src/agent_orchestrator/db/queue.py:_transition` - events queue table, shared library
- forward-only migrator - `code/agent-orchestrator/src/agent_orchestrator/db/migrate.py:run_migrations` - shared library, both services' migrate initContainer
- pool / notify / listen - `code/agent-orchestrator/src/agent_orchestrator/db/pool.py:open_pool` - shared library
- singleton worker - `code/agent-orchestrator/src/agent_orchestrator/runtime/singleton.py:advisory_singleton` - dispatcher worker of both services
- service runner - `code/agent-orchestrator/src/agent_orchestrator/runtime/run.py:run_service` - worker entrypoints
- settings structure - `code/agent-orchestrator/src/agent_orchestrator/settings.py:Settings` - both services' settings (own env prefix)
- template-DB test fixture - `code/agent-orchestrator/tests/conftest.py` - both services' DB tests
- openapi drift test - `code/agent-orchestrator/tests/test_readme_api.py` - both services' API contract tests
- chart components loop - `code/agent-orchestrator/chart/agent-orchestrator/templates/deployment.yaml` - both charts (ingest/api/worker components)
- chart postgres source - `code/agent-orchestrator/chart/agent-orchestrator/templates/_config.tpl` - both charts
- CI workflow - `code/agent-orchestrator/.github/workflows/ci.yaml` - both new repos' CI (images, chart publish)
- settings menu - `code/agent-orchestrator/frontend/src/layout/SessionsMenu.tsx:SessionsMenu` - menu entries (via frontend-decoupling contract)
- component scaffold - `scripts/init_engine/scaffold.py:write` - repo creation via `mise run component:add`
- db + app release pair - `code/agents-helmfile/helmfile.yaml.gotmpl` - helmfile releases agents-webhook-db and agents-webhook
- secrets bootstrap - `code/agents-helmfile/scripts/bootstrap-secrets.sh` - per-source webhook secrets, service token

### do-not-build
- SQLAlchemy / alembic layer - psycopg 3 + forward-only SQL migrator already used - `code/agent-orchestrator/src/agent_orchestrator/db/migrate.py:run_migrations`
- prompt field on presets / ClusterSpec - the prompt is a separate message call - `code/agent-orchestrator/src/agent_orchestrator/api/messages.py:post_message`
- turn-completion callback in the orchestrator - polling GET /api/v1/messages/{id} already gives the outcome - `code/agent-orchestrator/src/agent_orchestrator/api/messages.py` L99
- writes into orchestrator tables - one writer per table; go through /api/v1 - `code/agent-orchestrator/MEMORY.md` L19
- skip-auth route in the SSO sidecar - not supported by the injector; split the public ingest into its own pod - `infrastructure/code/containers/apps/oauth2proxy-injector/webhook.go`
- in-chart CNPG for the new services - agents-helmfile deploys a separate cnpg/cluster release - `code/agents-helmfile/helmfile.yaml.gotmpl`

### fix-as-ac
- non-idempotent create+message - dispatch task - cluster slug is deterministic per event; a 409 conflict resolves the existing cluster; the message id is recorded before the event leaves `new`, and a restart never posts a second prompt
- signature compare - ingest handlers - HMAC/token/bearer compared in constant time (`hmac.compare_digest`) over the raw body; empty secret refuses all requests
- unbounded body - ingest handlers - body over 5 MiB returns 413 before parsing
- forge retries on transient errors - ingest handlers - accepted and ignored events return 202; only a failed DB write returns 5xx
- untrusted event text in prompts - prompt rendering - event fields are escaped and framed as data, never as instructions (as `TN/internal/prompt/bundle.go`)
- multi-writer queue rows - events table - every status change is a status-guarded UPDATE; claims use FOR UPDATE SKIP LOCKED
- ingest behind SSO - chart - the public ingest Deployment carries no oauth2-proxy annotations; the UI/API Deployment does
- orchestrator API additive-only - service-token task - no existing /api/v1 route changes shape; openapi.json and README regenerated and drift test green

### ideas
- adopted: drop-or-forward dedup keyed on platform/repo/number, with in-flight events forwarded to the live run - TN/internal/queue/enqueue.go:dedupExists, TN/internal/controller/task_events.go
- adopted: concurrency capacity with FIFO by (priority, seq) - TN/internal/controller/queue_controller.go:admit
- adopted: Grafana dedup on alert labels, firing only - TN/internal/webhook/grafana.go:incidentDedupKey
- adopted: bot-actor self-event drop - TN/internal/webhook/server.go:isBotActor
- rejected: CRD-backed queue and per-project routing - the hard rules require a service-owned DB, and there is one project per deployment here - TN/api/v1alpha1/queuedevent_types.go
- rejected: agent-side outcome API posting forge comments - out of the requested scope; status lives in the webhook UI - TN/internal/restapi/outcome.go
- open (Q9): Keycloak client-credentials JWT through the sidecar vs orchestrator service tokens - infrastructure oauth2proxy-injector/webhook.go L442
