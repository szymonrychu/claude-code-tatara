# agents-schedule microservice - discovery brief

Phase 1 of start-development, 2026-10-25. Read-only discovery. This brief adds only the
schedule-specific facts. Everything shared with the webhook service lives in
`../agents-webhook-microservice/discovery.md` (W-F1..W-F6 below):
- orchestrator API, auth and the 403 problem (W-F3)
- DB, queue and migration patterns (W-F4)
- frontend menu (W-F5)
- scaffold and helmfile deploy (W-F6)

Path prefixes: `TN/` = `/Users/szymonri/Documents/tatara-new/code/tatara-operator/`,
`AO/` = `code/agent-orchestrator/`, `AH/` = `code/agents-helmfile/`.

## Facts with evidence

### S-F1. tatara-new cron (parity target)

- **No cron service or schedule store.** Cron lives in the operator.
  - Schedules are fixed per-activity fields on the Project CRD:
    `spec.scm.cron.{issueScan, documentation, refine, upgrade}.schedule`
    (`TN/api/v1alpha1/project_types.go:ScmCron` L926-948).
  - There are no user-defined schedule-to-run mappings.
  - The brainstorm cron is retired (`TN/internal/controller/projectscan.go` L56-62).
- **Syntax**:
  - 5-field cron parsed by robfig `ParseStandard`.
  - The CRD pattern `^$|^(\S+\s+){4}\S+$` enforces exactly 5 fields.
  - An empty string disables the activity.
- **Timezone**: no explicit handling. A search for `CRON_TZ`, `TZ=` and `time.Local` found
  nothing, so schedules run in the process's local timezone (inferred).
- **Due check** (`TN/internal/controller/projectscan.go:activityDue` L480, `dueBase` L50):
  - A run is due when now >= `Next(lastStamp)`. Before the first run it is
    `Next(creationTimestamp)`.
  - The stamp is then set to now, so any number of missed runs collapse into one catch-up run.
  - The wake-up uses controller-runtime `RequeueAfter`.
- **Jitter**: issueScan is phase-shifted per repo by an FNV hash (`scanOffset` L100).
- **Concurrency**:
  - refine is skipped while a refine Task is in flight (`inflightRefineTask` L1807).
  - upgrade runs only while open lanes < `maxOpenUpgrades`, default 1 (L1862).
  - The stamp advances even when a run is skipped.
  - Scheduled work enters the same queue at priority 2 (W-F1/W-F2), with dedup keys
    `refine-<proj>` and `upgrade-<proj>-<unix>` (L1195-1290).
- **UI**: none. W-F2 applies.

### S-F2. What a schedule triggers here

- The trigger path is the webhook service's path (W-F3):
  1. `POST /api/v1/clusters {preset_id, slug}`.
  2. `POST /api/v1/clusters/{id}/messages {text}`.
  3. Poll `GET /api/v1/messages/{id}`.
- **A preset has no prompt** (`AO/src/agent_orchestrator/spec.py:ClusterSpec` L124-141). A
  schedule needs its own prompt text, or the cluster boots idle with nothing to do.
- **Clusters never end on their own** (W-F3). Overlapping runs of a frequent schedule pile
  up clusters unless the schedule checks for a run in flight or the preset autocloses
  (configuration-improvements epic).
- **No Python cron dependency exists yet**: there is no cron library in
  `AO/pyproject.toml`.

### S-F3. UI placement

- The request: "lives in webUI in hamburger menu". There is no position constraint, unlike
  the webhook entry, which goes between Clusters and Presets.
- Today the menu holds only Presets (`AO/frontend/src/App.tsx` L39). Its shape is set by the
  frontend-decoupling contract (W-F5).

## Known / assumed / unknown

**Known**
- S-F1 and S-F2.
- Every shared fact in W-F3..W-F6.
- The 403 problem for an in-cluster caller (W-F3) applies to this service too.

**Assumed**
- "Map cronjob to preset" means a DB row (cron expression, preset, prompt, enabled), managed
  in the UI and run by this service.
- It does not mean a Kubernetes CronJob: AGENTS.md decouples services from Kubernetes APIs.
- The service tracks runs with the same run tracker as the webhook service:
  new/in-progress/handled/failed per run.

**Unknown**
- Which Python cron library to use. croniter's maintenance status changed in 2025; cronsim
  and APScheduler are the alternatives. This is a research-docs lens at the installed version.
- Whether the lab cluster's Python images carry tzdata, if a per-schedule timezone is wanted.

## Questions for the user (preference; recommended answer first)

1. **Cron syntax and timezone.**
   - **Recommended:** 5-field cron, matching tatara-new.
   - Each schedule has an IANA timezone, default `Europe/Warsaw`, shown in the UI with the
     next 3 fire times.
2. **Missed runs while the service was down.**
   - **Recommended:** tatara-new parity: collapse into one catch-up run when the service
     comes back, and only if the miss is within one period. Older misses are skipped and
     logged.
3. **Overlap.** The previous run of the same schedule is still in-progress.
   - **Recommended:** skip this firing and record it as `ignored` (reason `previous_running`).
   - Alternatives: queue it, or always start.
4. **What a run sends.**
   - **Recommended:** each schedule carries a required prompt text, with placeholders
     `{schedule_name}` and `{fired_at}`.
5. **Limits.**
   - **Recommended:** share the webhook's concurrency default: at most 3 in-progress runs
     overall and 1 per schedule.
   - Scheduled runs are separate from webhook runs, since each service has its own DB.
6. **Run history and controls in the UI.**
   - **Recommended:** a schedules list with enable/disable, a "run now" button, edit and
     delete.
   - Per-schedule recent runs, with status and a link to the cluster.
7. **Menu position.**
   - **Recommended:** directly below the webhook entry, giving the order Clusters, Webhooks,
     Schedules, Presets.

## Proposed epic dependency order

The order is the one in `../agents-webhook-microservice/discovery.md`:

1. frontend-decoupling
2. configuration-improvements (soft)
3. agents-webhook-microservice
4. agents-schedule-microservice

This epic comes last because it reuses what agents-webhook builds:
- the shared library `agents-common` (webhook Q10)
- the orchestrator service-token auth (webhook Q9)
- the run tracker and the UI page patterns

Its own work is:
- the scheduler loop
- the schedules table and API
- the UI pages
- the chart and its helmfile releases `agents-schedule-db` and `agents-schedule`

## Plan inputs

### reuse
- shared library (settings, pool, migrate, guarded transitions, orchestrator client, run tracker) - owned by agents-webhook-microservice, see `../agents-webhook-microservice/discovery.md` Plan inputs - every backend task here
- orchestrator create-from-preset - `code/agent-orchestrator/src/agent_orchestrator/api/clusters.py:_create_from_preset` - fire task (deterministic slug per schedule+fire time)
- orchestrator post message - `code/agent-orchestrator/src/agent_orchestrator/api/messages.py:post_message` - fire task
- message outcome polling - `code/agent-orchestrator/bench/runner.py:_finished` - run tracker (overlap check, run status)
- singleton worker - `code/agent-orchestrator/src/agent_orchestrator/runtime/singleton.py:advisory_singleton` - scheduler loop (exactly one firing instance)
- guarded transition - `code/agent-orchestrator/src/agent_orchestrator/db/queue.py:_transition` - runs table
- forward-only migrator - `code/agent-orchestrator/src/agent_orchestrator/db/migrate.py:run_migrations` - schema
- chart components loop and postgres source - `code/agent-orchestrator/chart/agent-orchestrator/templates/deployment.yaml` - chart
- CI workflow - `code/agent-orchestrator/.github/workflows/ci.yaml` - repo CI
- component scaffold - `scripts/init_engine/scaffold.py:write` - repo creation via `mise run component:add`
- db + app release pair - `code/agents-helmfile/helmfile.yaml.gotmpl` - releases agents-schedule-db, agents-schedule
- settings menu - `code/agent-orchestrator/frontend/src/layout/SessionsMenu.tsx:SessionsMenu` - menu entry (via frontend-decoupling contract)

### do-not-build
- Kubernetes CronJob per schedule - decoupled from Kubernetes APIs; a singleton loop over the service's own table - AGENTS.md "What this project is building"
- a second orchestrator client / DB layer - the shared library from agents-webhook-microservice - `../agents-webhook-microservice/discovery.md`
- a cron parser - a maintained library (chosen by a research-docs lens) - S-F2
- prompt on presets - the schedule row carries the prompt; the message call sends it - `code/agent-orchestrator/src/agent_orchestrator/api/messages.py:post_message`
- turn-completion callback in the orchestrator - polling the message gives the outcome - `code/agent-orchestrator/src/agent_orchestrator/api/messages.py` L99

### fix-as-ac
- double fire on restart or two replicas - scheduler loop - firing is claimed by a status-guarded insert keyed on (schedule_id, fire_time) under the advisory singleton; a restart never starts the same fire twice
- missed-run storm - scheduler loop - after downtime at most one catch-up run per schedule (S-F1 parity)
- stamp advances on skip - scheduler loop - a skipped (overlap) firing still advances last-fired, recorded as ignored with reason
- non-idempotent create+message - fire task - deterministic slug, 409 resolves the existing cluster, message id recorded before leaving `new`
- invalid cron saved - schedules API - expression validated (5 fields) and the timezone checked as IANA on write; 422 with the reason

### ideas
- adopted: Next(lastStamp) due check with collapse of missed runs - TN/internal/controller/projectscan.go:activityDue
- adopted: skip while previous run in flight - TN/internal/controller/projectscan.go:inflightRefineTask
- rejected: fixed per-activity cron fields on a CRD - the request is user-defined cron-to-preset mappings - TN/api/v1alpha1/project_types.go:ScmCron
- rejected: process-local timezone - ambiguous across pods; explicit IANA zone per schedule (Q1) - TN projectscan.go (no TZ handling)
- open: per-repo phase-shift jitter (scanOffset) - only relevant if many schedules share a time; not requested - TN/internal/controller/projectscan.go:scanOffset
