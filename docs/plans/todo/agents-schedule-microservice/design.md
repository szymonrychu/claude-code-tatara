# agents-schedule microservice design

## Summary

A new Python component `agents-schedule` with its own Postgres database maps user-defined 5-field cron
schedules (with an IANA timezone) to orchestrator presets plus a prompt. A singleton worker fires due
schedules exactly once per fire time, starts a cluster from the preset through the orchestrator's
service-token port and sends the prompt, then tracks the first turn to `handled` or `failed`. A
Schedules page in agents-web, reached from the hamburger menu between Webhooks and Presets, manages
schedules and shows run history. Headline decisions: everything shared (DB helpers, settings and
runtime, orchestrator client, dispatch and run tracking, fake orchestrator, trigger UI kit, service
tokens) is consumed from agents-webhook-microservice, nothing is rebuilt (D2); the last-fired stamp
is derived from the runs table so each table keeps one writer (D3); tatara-new due-check parity with
one catch-up run after downtime (D5); overlaps are recorded `ignored` (D6).

## Intent and why

The user wants more of tatara-new in this system (README Description). tatara-new runs scheduled work
from fixed per-activity cron fields on its Project CRD; here the request is a separate microservice
where any cron schedule maps to any preset, "similar to agents-webhooks", living in the web UI's
hamburger menu. It is the second trigger service after agents-webhook and reuses its shared parts.

## Goals

- G1: `code/agents-schedule` exists (public GitHub repo, created by epic agents-schedule-component) with a Python service, its image, chart and CI.
- G2: schedules (name, cron, timezone, preset, prompt, enabled) are created, listed, edited, previewed, enabled, disabled and deleted through `/schedules/api/v1`, with 422 reasons for invalid cron, timezone or preset.
- G3: an enabled schedule fires once per fire time, starts one cluster from its preset and sends its prompt; a restart or a second worker never fires or posts twice.
- G4: after downtime a schedule fires one catch-up run; a fire while the previous run is in flight is recorded `ignored` with reason `previous_running`.
- G5: each run ends `handled` (first turn completed) or `failed` with a reason; history per schedule and globally is listed by the API.
- G6: the Schedules page in agents-web manages schedules and shows runs with a cluster link; its menu entry sits between Webhooks and Presets and appears only when the backend is configured.
- G7: the API is documented (README, committed `openapi.json`, drift test) and a kind e2e exercises every route.
- G8: v0.1.0 is released, deployed with its CNPG database to the agents namespace, and the live smoke covers it.

## Non-goals

- No Kubernetes CronJob per schedule (AGENTS.md decouples services from Kubernetes APIs).
- No prompt field on presets and no change to the orchestrator API.
- No cluster deletion by this service; cleanup is the preset autoclose of configuration-improvements.
- No per-schedule jitter (tatara-new `scanOffset`), seconds field or cron macros.
- No new shared library code, orchestrator client, dispatch algorithm, fake orchestrator or UI kit: agents-webhook-microservice owns them.

## Anti-goals

- A second copy of the DB, settings, client or dispatch code next to agents-common.
- A double fire or a second prompt after a restart or with two worker replicas.
- A missed-run storm after downtime.
- The schedule API reachable without SSO, or the service reaching the orchestrator through the SSO port.

## Constraints

- Python only for the service; TypeScript only in agents-web (AGENTS.md hard rules).
- Services talk only through HTTP; each table has one writer except queue tables, which change rows only through status-guarded updates.
- The orchestrator `/api/v1` is additive-only; this epic adds nothing to it.
- Plan-execute needs every task repo under `code/` when the run starts (`ticket.py:_integration_plan`), and an epic cannot mix superrepo and component tasks: the repo creation is its own meta epic, agents-schedule-component, a blocker of this one.
- Orchestrator ruling: runs after agents-webhook-microservice and frontend-decoupling (README blockers), consuming their contracts. agent-init-scripts and cluster-scaling are blockers too because this epic edits the same agents-helmfile files after them, and configuration-improvements because the menu order rule `web-settings-menu-order` requires it.

## Decisions

### D1: New component agents-schedule

A Python service repo `szymonrychu/agents-schedule` (public, like every component), created by `mise run component:add` in epic agents-schedule-component (task create-agents-schedule-repo, the agents-web-component pattern). This epic adds pyproject, package `agents_schedule`, console script `sched` with `migrate`, `api`, `worker`. Alternative: the schedule code inside agents-webhook (rejected: couples two services' releases, against the "separate microservice" request). Approvals A1, A7.

### D2: Consume the shared parts, build none

agents-common v0.1.0 (contracts `agents-common-lib`: settings, db, runtime, OrchestratorClient, FakeOrchestrator, testing plugin; `preset-mapping-model`: PresetBinding, RunStore, marker, dispatch, track), the orchestrator service-token port (`orch-service-tokens`, `orch-services-service`) and the agents-web trigger UI kit (`trigger-ui-page-pattern`) come from agents-webhook-microservice; the runtime backends config, backend menu registry, URL layout, OpenAPI vendoring, chart and image (`agents-web-backends-config`, `agents-web-backend-registry`, `agents-web-url-layout`, `agents-web-openapi-vendor`, `agents-web-chart`, `agents-web-image`) from frontend-decoupling, registered in `docs/plans/contracts.json`; the menu order rule `web-settings-menu-order` from configuration-improvements. All are registered in `docs/plans/contracts.json` and list this epic as consumer. Approval A8.

### D3: Two tables, one writer each

`schedules` (writer: the api) and `runs` (queue table: the api inserts manual runs, the worker inserts scheduled runs and moves statuses with guarded updates). The last-fired stamp is not a column: it is the latest scheduled `runs.fire_time`, else `schedules.armed_at` (set on create, on enable and on a cron or timezone change). Alternative: a `last_fired_at` column on `schedules` (rejected: two writers on one table). Run statuses: new, in-progress, handled, failed, ignored (the webhook set). Approvals A1, A2, A3.

### D4: Cron syntax, timezone and library

Exactly 5 fields (tatara-new's CRD pattern), no macros or seconds; each schedule has an IANA timezone, default `Europe/Warsaw`; the API and the form preview the next 3 fire times. Library croniter 6.2.4 (maintained, released 2026-07-10, probed on PyPI 2026-10-25) with `tzdata` from PyPI so zoneinfo works in a slim image (my call; cronsim 2.7 was the alternative). Gate Q1. Approval A2.

### D5: Due check and missed runs

tatara-new parity (`projectscan.go:activityDue`): due when `next(stamp) <= now`; the run is for the latest fire time in `(stamp, now]`, and earlier fire times in that interval are not run and are logged with their count. So downtime yields one catch-up run. Gate Q2. Approval A3.

### D6: Overlap

A fire while the schedule already has `SCHED_MAX_PER_SCHEDULE` (default 1) runs new or in-progress is inserted as `ignored`, reason `previous_running`; the stamp still advances (tatara-new `inflightRefineTask`). Run-now follows the same rule. Gate Q3. Approval A3.

### D7: Prompt

Each schedule carries a required prompt (1..16384 chars) with placeholders `{schedule_name}` and `{fired_at}`, replaced literally; other braces stay as written. The prompt is sent as the first message after create; presets stay prompt-less. Gate Q4. Approvals A2, A3.

### D8: Limits

At most `SCHED_MAX_IN_PROGRESS` (default 3) runs in progress overall and 1 per schedule; further `new` runs wait FIFO by fire time. A run in progress longer than `SCHED_RUN_TIMEOUT_SECONDS` (default 3600) fails with reason `timeout` (the webhook D6 rule). Separate from the webhook's caps, since each service has its own DB. Gate Q5. Approval A3.

### D9: Exactly-once fire and idempotent dispatch

The worker runs under the agents-common advisory singleton, and scheduled runs are inserted with `ON CONFLICT (schedule_id, fire_time) DO NOTHING`, so a restart or a second worker never creates a second run. Dispatch is agents-common `runs.dispatch`: claim `new -> in-progress`, deterministic slug `<name slug>-<8 hex of run id>` (409 resolves the existing cluster), marker `marker("schedule", run_id)` = `<!-- agents-schedule:<id> -->` checked before posting, ids recorded with guarded updates. Approval A3.

### D10: Run outcome and cleanup

agents-common `runs.track` polls the message: first turn completed is `handled`; message failed or cancelled, turn failed, message gone or timeout is `failed` with that reason. The service never deletes clusters; cleanup is the preset's autoclose (configuration-improvements, contract `orch-cluster-autoclose`). Gate Q8. Approval A3.

### D11: API surface and headless parity

All routes under `/schedules/api/v1` (the reserved prefix of `agents-web-url-layout`; gate Q9): schedules CRUD, `POST /schedules/preview`, `POST /schedules/{id}/run` (allowed on a disabled schedule, my call), `GET /schedules/{id}/runs`, `GET /runs`, `GET /runs/{id}`; `/healthz` and `/readyz` at the root. Errors `{error: {code, message}}`. A source allowlist on the socket peer (`SCHED_ALLOWED_CIDRS`, default `127.0.0.1/32`) admits only the oauth2-proxy sidecar. README `## API`, committed `openapi.json` with a drift test, and an API-only kind e2e that hits every route against the agents-common fake orchestrator. Approval A5.

### D12: UI in agents-web

`src/schedules/`: API client typed from the vendored `openapi/schedules.json`, `ScheduleForm` (cron, timezone, `PresetSelect`, prompt, live preview), `ScheduleRuns` (`RunStatusChip`, cluster link, `usePoll`), `SchedulesPage` (enable/disable, run now, edit, delete with confirm, expandable runs). The menu entry is registered in `src/backends/registry.ts` (`agents-web-backend-registry`) at its reserved order 30, giving Clusters 10, Webhooks 20, Schedules 30, Presets 40 (gate Q7, `web-settings-menu-order`), shown only when `config.json` lists the `schedules` backend. Gates Q6, Q7. Approvals A2, A4.

### D13: Chart and image

Image `harbor.szymonrichert.pl/containers/agents-schedule:<sha7>` (python slim, uv, USER 1000); chart `oci://harbor.szymonrichert.pl/charts/agents-schedule` with an api Deployment (SSO annotations from values, Service port name `http`) and a worker Deployment, both with a `sched migrate` initContainer; DB URL from a Secret and the orchestrator token as a value rendered into the chart's own Secret or from `orchestrator.tokenSecret` (the agents-webhook chart shape); Ingress on `/schedules` without its own cert-manager annotation. CI jobs lint, test, images, chart, e2e, chart-publish, chart-publish-tag, as agent-orchestrator. Approvals A1, A6.

### D14: Release and deploy

Tag v0.1.0 on the merged main commit (chart 0.1.0). agents-helmfile: release `agents-schedule-db` (cnpg/cluster 0.9.0) and `agents-schedule` (needs the db; DB URL from `agents-schedule-db-cluster-app` key `uri`; orchestrator `http://agent-orchestrator-services:8002` (`orch-services-service`) with `orchestrator.token` from SOPS `values/agents-schedule/default.secrets.yaml`; host `lab.szymonrichert.pl` path `/schedules`); `bootstrap-secrets.sh` writes the token (raw into `values/agents-schedule/default.secrets.yaml`, its sha256 as `serviceApi.tokenHashes.agents-schedule` into `values/agent-orchestrator/service-token-agents-schedule.secrets.yaml`, as agents-webhook task helmfile-service-token); the agents-web values gain the `schedules` backend and the agents-web pin moves to the build with the Schedules page; the smoke gains a schedule step; then `mise run apply` and `mise run smoke`. Gate Q10. Approval A6.

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| start-discovery (brief `discovery.md`) | ran 2026-10-25 | Next(stamp) due check with collapse (`TN/internal/controller/projectscan.go:activityDue`); skip while in flight (`projectscan.go:inflightRefineTask`) | fixed per-activity CRD cron fields (`TN/api/v1alpha1/project_types.go:ScmCron`); process-local timezone (`projectscan.go`, no TZ handling) |
| research-code-internal | ran inside discovery (shared with the agents-webhook brief F3-F6) | reuse list below | second DB layer or client |
| research-docs (cron library) | replaced by a probe: PyPI JSON for croniter, cronsim, APScheduler on 2026-10-25 | croniter 6.2.4 (released 2026-07-10) | APScheduler (a scheduler framework, not needed under the advisory singleton) |
| research-code-external | skipped: tatara-new is the only prior art requested, read in discovery | none | none |
| research-papers | skipped: no research question | none | none |
| sibling plans | read 2026-10-25: `../agents-webhook-microservice/design.md`, `../frontend-decoupling/tasks/*.md` | contract names, `runs.dispatch` marker pattern, run timeout, URL layout `/<prefix>/api/v1`, backend registry order slot 30 for Schedules | none |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| discovery reuse | shared library (settings, pool, migrate, guarded transitions, orchestrator client, run tracker) | scaffold-project-and-cli, schedule-settings-model, schema-migrations, runs-repository, run-dispatcher, run-outcome-tracker, service-entrypoints |
| discovery reuse | `clusters.py:_create_from_preset` | run-dispatcher (through agents-common `runs.dispatch`) |
| discovery reuse | `messages.py:post_message` | run-dispatcher |
| discovery reuse | `bench/runner.py:_finished` | run-outcome-tracker |
| discovery reuse | `runtime/singleton.py:advisory_singleton` | service-entrypoints |
| discovery reuse | `db/queue.py:_transition` | runs-repository |
| discovery reuse | `db/migrate.py:run_migrations` | schema-migrations |
| discovery reuse | chart components loop and postgres source | helm-chart |
| discovery reuse | CI workflow | dockerfile-and-ci |
| discovery reuse | `scripts/init_engine/scaffold.py:write` | agents-schedule-component/create-agents-schedule-repo |
| discovery reuse | db + app release pair | helmfile-schedule-db-release, helmfile-schedule-release |
| discovery reuse | `SessionsMenu.tsx:SessionsMenu` | web-schedules-menu-entry (now `src/backends/registry.ts`, frontend-decoupling) |
| discovery do-not-build | Kubernetes CronJob per schedule | rejected: non-goal; scheduler-loop under the singleton |
| discovery do-not-build | second orchestrator client / DB layer | run-dispatcher, run-outcome-tracker, schema-migrations use agents-common |
| discovery do-not-build | a cron parser | cron-expressions uses croniter |
| discovery do-not-build | prompt on presets | run-dispatcher sends the schedule's prompt as a message |
| discovery do-not-build | turn-completion callback in the orchestrator | run-outcome-tracker polls |
| discovery fix-as-ac | double fire on restart or two replicas | scheduler-loop AC2, service-entrypoints AC2, kind-e2e-api AC4 |
| discovery fix-as-ac | missed-run storm | cron-expressions AC5, scheduler-loop AC3 |
| discovery fix-as-ac | stamp advances on skip | scheduler-loop AC4 |
| discovery fix-as-ac | non-idempotent create+message | run-dispatcher AC2, AC3 |
| discovery fix-as-ac | invalid cron saved | cron-expressions AC2, AC3; schedules-api-routes AC2 |
| discovery ideas | adopted Next(lastStamp) due check | cron-expressions, scheduler-loop |
| discovery ideas | adopted skip while previous run in flight | scheduler-loop, runs-api-routes |
| discovery ideas | rejected CRD cron fields | rejected: the request is user-defined mappings |
| discovery ideas | rejected process-local timezone | cron-expressions (explicit IANA zone) |
| discovery ideas | open per-repo jitter | rejected: not requested (non-goal) |
| agents-webhook design D6 | run timeout | run-outcome-tracker, schedule-settings-model |
| agents-webhook design D8 | dispatch with marker | run-dispatcher |
| frontend-decoupling web-chart-config-ingress | URL layout `/<prefix>/api/v1`, reserved `schedules` | schedules-api-routes, chart-ingress-and-test-hook, helmfile-schedule-release |
| frontend-decoupling web-backend-menu | registry order slots | web-schedules-menu-entry |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 New component agents-schedule | scaffold-project-and-cli, service-entrypoints |
| D2 Consume the shared parts | scaffold-project-and-cli, run-dispatcher, run-outcome-tracker, kind-e2e-api, web-schedule-form |
| D3 Two tables, one writer each | schema-migrations, schedules-repository, runs-repository |
| D4 Cron syntax, timezone and library | cron-expressions, schedules-api-routes, web-schedule-form |
| D5 Due check and missed runs | cron-expressions, scheduler-loop |
| D6 Overlap | scheduler-loop, runs-api-routes |
| D7 Prompt | run-dispatcher, web-schedule-form |
| D8 Limits | runs-repository, run-dispatcher, schedule-settings-model |
| D9 Exactly-once fire and idempotent dispatch | runs-repository, scheduler-loop, run-dispatcher, service-entrypoints |
| D10 Run outcome and cleanup | run-outcome-tracker |
| D11 API surface and headless parity | schedules-api-routes, runs-api-routes, api-docs-and-openapi, kind-e2e-api, smoke-schedule-check |
| D12 UI in agents-web | web-schedules-api-client, web-schedule-form, web-schedule-runs-list, web-schedules-page, web-schedules-menu-entry, web-config-schedules-backend |
| D13 Chart and image | dockerfile-and-ci, helm-chart, chart-ingress-and-test-hook |
| D14 Release and deploy | release-v0-1-0, helmfile-schedule-db-release, helmfile-schedule-release, schedule-service-token, web-config-schedules-backend, smoke-schedule-check, deploy-schedule |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `sched-cli` | scaffold-project-and-cli | service-entrypoints | `code/agents-schedule/src/agents_schedule/cli.py` |
| `agents-schedule-settings-env` | schedule-settings-model | schema-migrations, helm-chart, helmfile-schedule-release | `code/agents-schedule/README.md` |
| `sched-cron` | cron-expressions | scheduler-loop, schedules-api-routes | `code/agents-schedule/src/agents_schedule/cron.py` |
| `sched-schema` | schema-migrations | schedules-repository, runs-repository | `code/agents-schedule/src/agents_schedule/migrations/0001_schedules.sql` |
| `sched-db-fixture` | schema-migrations | schedules-repository, runs-repository | `code/agents-schedule/tests/conftest.py` |
| `sched-schedules-repo` | schedules-repository | scheduler-loop, run-dispatcher, schedules-api-routes | `code/agents-schedule/src/agents_schedule/db/schedules.py` |
| `sched-runs-repo` | runs-repository | scheduler-loop, run-dispatcher, run-outcome-tracker, schedules-api-routes, runs-api-routes | `code/agents-schedule/src/agents_schedule/db/runs.py` |
| `sched-scheduler` | scheduler-loop | service-entrypoints | `code/agents-schedule/src/agents_schedule/scheduler.py` |
| `sched-dispatch` | run-dispatcher | service-entrypoints | `code/agents-schedule/src/agents_schedule/dispatcher.py` |
| `sched-tracker` | run-outcome-tracker | service-entrypoints | `code/agents-schedule/src/agents_schedule/tracker.py` |
| `sched-api-app` | schedules-api-routes | runs-api-routes, api-docs-and-openapi, service-entrypoints | `code/agents-schedule/src/agents_schedule/api/app.py` |
| `sched-runs-api` | runs-api-routes | api-docs-and-openapi | `code/agents-schedule/src/agents_schedule/api/runs.py` |
| `agents-schedule-api` | api-docs-and-openapi | kind-e2e-api, web-schedules-api-client, smoke-schedule-check | `code/agents-schedule/README.md` |
| `sched-entrypoints` | service-entrypoints | dockerfile-and-ci, helm-chart | `code/agents-schedule/src/agents_schedule/runtime.py` |
| `agents-schedule-image` | dockerfile-and-ci | kind-e2e-api, release-v0-1-0 | `code/agents-schedule/.github/workflows/ci.yaml` |
| `agents-schedule-chart-core` | helm-chart | chart-ingress-and-test-hook | `code/agents-schedule/chart/agents-schedule/values.yaml` |
| `agents-schedule-chart` | chart-ingress-and-test-hook | kind-e2e-api, release-v0-1-0, helmfile-schedule-release | `code/agents-schedule/chart/agents-schedule/values.yaml` |
| `agents-schedule-release` | release-v0-1-0 | deploy-schedule | `code/agents-schedule/README.md` |
| `web-schedules-client` | web-schedules-api-client | web-schedule-form, web-schedule-runs-list, web-schedules-page | `code/agents-web/src/schedules/api.ts` |
| `web-schedule-form` | web-schedule-form | web-schedules-page | `code/agents-web/src/schedules/ScheduleForm.tsx` |
| `web-schedule-runs` | web-schedule-runs-list | web-schedules-page | `code/agents-web/src/schedules/ScheduleRuns.tsx` |
| `web-schedules-page` | web-schedules-page | web-schedules-menu-entry | `code/agents-web/src/schedules/SchedulesPage.tsx` |
| `agents-schedule-db-release` | helmfile-schedule-db-release | helmfile-schedule-release | `code/agents-helmfile/helmfile.yaml.gotmpl` |
| `agents-schedule-release-values` | helmfile-schedule-release | deploy-schedule | `code/agents-helmfile/values/agents-schedule/common.yaml` |
| `agents-web-schedules-config` | web-config-schedules-backend | deploy-schedule | `code/agents-helmfile/values/agents-web/common.yaml` |

Cross-epic, registered in `docs/plans/contracts.json` by this epic: `agents-schedule-api`, `agents-schedule-chart`, `agents-schedule-image`, `agents-schedule-settings-env` (consumers agents-web, agents-helmfile). Consumed, registered by others and listing this epic as consumer: `agents-common-lib`, `preset-mapping-model`, `orch-service-tokens`, `orch-services-service`, `trigger-ui-page-pattern` (agents-webhook-microservice); `agents-web-backends-config`, `agents-web-backend-registry`, `agents-web-url-layout`, `agents-web-openapi-vendor`, `orch-ui-retired` (frontend-decoupling; `agents-web-chart` and `agents-web-image` are consumed by deploy-schedule through agents-helmfile); `web-settings-menu-order`, `orch-cluster-autoclose` (configuration-improvements); `orch-presets-api`, `orch-cluster-create-api` (cluster-presets, done).

## Review focus

- scheduler-loop and run-dispatcher: exactly-once firing and dispatch under restart and two workers (unique key, guarded transitions, marker check); the stamp derived from runs.
- cron-expressions: DST behaviour in Europe/Warsaw and the missed-run collapse.
- schedules-api-routes: the source allowlist reads only the socket peer; validation codes.
- helmfile-schedule-release and schedule-service-token: the api pod behind SSO, the orchestrator reached only on the service port, no secret printed.
- web-schedules-menu-entry: the entry uses the reserved slot 30 and appears only with the backend configured.

## Left to the builder

- Internal module layout beyond the files named in tasks, as long as the contract files stay where the Contracts table says.
- Exact logging format, backoff curve for transient orchestrator errors (bounded by `SCHED_DISPATCH_MAX_ATTEMPTS`).
- UI styling within the trigger UI kit's look.
- Using an agents-common helper (source allowlist, LISTEN wake-up) when the released library has one; otherwise the minimal local version described in the task.

## Assumptions and unknowns

- The agents-common API is as agents-webhook design D1 and D8 describe (`BaseServiceSettings`, `run_migrations`, `transition`, `claim`, `advisory_singleton`, `run_service`, `OrchestratorClient`, `fake_orchestrator`, `runs.dispatch`/`track` with `RunStore` and `PresetBinding`, pytest plugin `agents_common.testing`). Confirmed by reading `code/agents-common` at v0.1.0 before this epic's run; a different signature is followed as released.
- The agents-common fake orchestrator can hold a turn running and fail one; if not, kind-e2e-api covers those two cases in unit tests and reports the gap (task notes).
- agents-web layout is as frontend-decoupling tasks web-runtime-config, web-backend-menu and web-openapi-vendor define (`src/config/backends.ts`, `src/backends/registry.ts`, `openapi/<id>.json`, `scripts/sync-api.mjs`). Confirmed by reading `code/agents-web` before the run.
- The orchestrator service port Service is `agent-orchestrator-services:8002` (agents-webhook D10, release `agent-orchestrator`). Confirmed by `helm template` in helmfile-schedule-release.
- Harbor CI secret values are available to the agent for `gh secret set`; otherwise the meta task blocks on the user (named there).
- No probe could settle the user preferences below; they are in Open questions.

## Open questions

none
- Q1: Cron syntax: exactly 5 fields, each schedule with an IANA timezone defaulting to Europe/Warsaw, and the next 3 fire times shown? [recommended: yes]
- Q2: Missed runs while the service was down collapse into one catch-up run for the latest missed fire time; older ones are skipped and logged? [recommended: yes]
- Q3: A fire while the previous run of the same schedule is still running is skipped and recorded as ignored (reason previous_running), not queued or started anyway? [recommended: yes]
- Q4: Each schedule carries a required prompt with placeholders {schedule_name} and {fired_at}, sent as the first message to the new cluster? [recommended: yes]
- Q5: Limits: at most 3 scheduled runs in progress overall and 1 per schedule, the rest waiting FIFO, and a run stuck over 1 hour marked failed (timeout)? [recommended: yes]

## Irreversible operations in scope

- Creating the public GitHub repo `szymonrychu/agents-schedule` and setting its two CI secrets (epic agents-schedule-component, task create-agents-schedule-repo); approval A7.
- Pushing tag `v0.1.0` on agents-schedule main and publishing chart `0.1.0` (immutable in Harbor) (release-v0-1-0); approval A6.
- Creating the CNPG database `agents-schedule-db` and applying the agents namespace with `mise run apply` (deploy-schedule); additive, no existing release removed; approval A6.
- Writing a new SOPS-managed service token and adding its hash to the orchestrator's service-token Secret (schedule-service-token, deploy-schedule); new values only, nothing rotated; approval A6.
