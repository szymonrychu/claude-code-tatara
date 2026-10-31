---
title: agents-schedule deploy
repos: [agents-helmfile, agents-web]
created: 2026-10-25
owner: Szymon Richert
rung: 1
---

# agents-schedule deploy

## What and why

What: The agents-helmfile and agents-web half of agents-schedule-microservice: deploy the agents-schedule service (CNPG database, release, service token), the live smoke step, the agents-web Schedules page and its hamburger menu entry
How: agents-web gets a typed schedules client, form, run list, page and menu entry between Webhooks and Presets; agents-helmfile gets the agents-schedule-db and agents-schedule releases, the SOPS service token, the schedules backend in the agents-web values and a smoke schedule step, then apply and smoke
Why: Scheduled agent runs from presets, as in tatara-new; split from agents-schedule-microservice so the service epic can land without waiting on the rename-dependent deploy and UI work

Split from epic agents-schedule-microservice on 2026-10-25 (orchestrator ruling): this epic holds its agents-helmfile and agents-web tasks, unchanged in scope. It runs after orchestrator-rename-sessions (agents-orchestrator names, sessions) and after agents-schedule-microservice (the service, chart and v0.1.0 release it deploys). Decisions D12 and the deploy half of D14 are in this epic's design.md; everything else is in `../agents-schedule-microservice/design.md`.

Original user request (2026-10-25), verbatim: "## agents-schedule microservice
  * separate microservice allowing to map cronjob to preset - similar to agents-webhooks (maps cronjob to preset), lives in webUI in hamburger menu"

## Scope ladder

### Rung 1: agreed scope (migrated)

- 1.1: A Schedules page in agents-web, between Webhooks and Presets in the hamburger menu, manages schedules and shows run history with a session link.
- 1.2: agents-schedule v0.1.0 is deployed with its own CNPG database to the agents namespace through agents-helmfile (service token, release pair, agents-web backend config), and the live smoke covers it.

## Agreed scope

Rung 1, migrated from the epic format: the epic's goals were its agreed scope.

## Non-goals

- No change to the agents-schedule service code, chart or release: epic agents-schedule-microservice owns them and is a blocker.
- No Kubernetes CronJob, no prompt on presets, no orchestrator API change, no session deletion by the schedule service.
- No shared UI kit or backend registry code: agents-webhook-microservice and frontend-decoupling own them.

## Design

Migrated from the epic format; the design sections without a plan.md heading are under Migrated notes.

## Decisions

### D12: UI in agents-web

`src/schedules/`: API client typed from the vendored `openapi/schedules.json`, `ScheduleForm` (cron, timezone, `PresetSelect`, prompt, live preview), `ScheduleRuns` (`RunStatusChip`, session link, `usePoll`), `SchedulesPage` (enable/disable, run now, edit, delete with confirm, expandable runs). The menu entry is registered in `src/backends/registry.ts` (`agents-web-backend-registry`) at its reserved order 30, giving Sessions 10, Webhooks 20, Schedules 30, Presets 40 (gate Q7, `web-settings-menu-order`), shown only when `config.json` lists the `schedules` backend. Gates Q6, Q7. Approvals A2, A4.

### D14: Release and deploy

Tag v0.1.0 on the merged main commit (chart 0.1.0). agents-helmfile: release `agents-schedule-db` (cnpg/cluster 0.9.0) and `agents-schedule` (needs the db; DB URL from `agents-schedule-db-cluster-app` key `uri`; orchestrator `http://agents-orchestrator-services:8002` (`orch-services-service`) with `orchestrator.token` from SOPS `values/agents-schedule/default.secrets.yaml`; host `lab.szymonrichert.pl` path `/schedules`); `bootstrap-secrets.sh` writes the token (raw into `values/agents-schedule/default.secrets.yaml`, its sha256 as `serviceApi.tokenHashes.agents-schedule` into `values/agents-orchestrator/service-token-agents-schedule.secrets.yaml`, as agents-webhook task helmfile-service-token); the agents-web values gain the `schedules` backend and the agents-web pin moves to the build with the Schedules page; the smoke gains a schedule step; then `mise run apply` and `mise run smoke`. Gate Q10. Approval A6.

## Open questions

none

## Research

none recorded in the epic format

## Irreversible operations

none

## Migrated notes

### README.md: Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-26)

Acted on:
- web-schedule-form: a tsc error and a missing Intl fallback.
- web-schedules-page: "cluster" wording broke the nomenclature test, plus a type cast.
- deploy-schedule: a stale test_values_dir_moved list blocked the apply guard.
Dropped:
- Security medium "SSO bypass via http-insecure 8080". The app allowlist checks only the socket peer: proxy_headers=False, tested against a real uvicorn server in agents-schedule.
- A NetworkPolicy backstop for the namespace (cross-service, not this epic).
- Shared S3 backup credentials with agents-webhook-db (same accepted practice).
- TLS Secret reuse (per the URL layout).
- Scope audit claim that menu.ts drops onOpenSession: wrong, menu.ts:10 passes it.
Evidence:
- agents-helmfile `mise run test` 155 passed, lint clean.
- agents-web main CI green, npm test 373 passed.
- Live apply at e16b726 (agents-schedule rev 1, agents-schedule-db rev 1, agents-web rev 8, agents-orchestrator rev 2).
- smoke: OK after an agents-orchestrator api restart.

### design.md: Summary

The agents-helmfile and agents-web half of epic agents-schedule-microservice, split out with scope unchanged. This
epic deploys the agents-schedule service (CNPG database, release, SOPS service token, agents-web backend config, smoke
step) and adds the Schedules page to agents-web. The service, chart, image and v0.1.0 release are built by the
blocker agents-schedule-microservice; the renamed orchestrator (agents-orchestrator, sessions) by the blocker
orchestrator-rename-sessions. The shared decisions (D1-D11, D13, D15), the contracts of the service and the open
questions are in `../agents-schedule-microservice/design.md`; this file holds D12 and the deploy half of D14, copied
verbatim with their numbers.

### design.md: Intent and why

See `../agents-schedule-microservice/design.md` (Intent and why). The split only separates what needs the
agents-orchestrator names live (deploy, smoke) and the web UI from the service build.

### design.md: Goals

- G6: the Schedules page in agents-web manages schedules and shows runs with a session link; its menu entry sits between Webhooks and Presets and appears only when the backend is configured.
- G8: v0.1.0 is deployed with its CNPG database to the agents namespace, and the live smoke covers it.

### design.md: Non-goals

- Any change to the agents-schedule service, chart or release (agents-schedule-microservice).
- No new shared UI kit or backend registry code (agents-webhook-microservice, frontend-decoupling).

### design.md: Constraints

- Blocked by orchestrator-rename-sessions and agents-schedule-microservice (README blockers); task depends_on entries that pointed at tasks of the other epic (release-v0-1-0, chart-ingress-and-test-hook, api-docs-and-openapi) are dropped, the epic blocker covers them.
- Live applies (`mise run apply`) are run by the orchestrator in the main session.

### design.md: Decision coverage

| Decision | Tasks |
|---|---|
| D12 UI in agents-web | web-schedules-api-client, web-schedule-form, web-schedule-runs-list, web-schedules-page, web-schedules-menu-entry, web-config-schedules-backend |
| D14 Release and deploy | helmfile-schedule-db-release, helmfile-schedule-release, schedule-service-token, web-config-schedules-backend, smoke-schedule-check, deploy-schedule |

### design.md: Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `web-schedules-client` | web-schedules-api-client | web-schedule-form, web-schedule-runs-list, web-schedules-page | `code/agents-web/src/schedules/api.ts` |
| `web-schedule-form` | web-schedule-form | web-schedules-page | `code/agents-web/src/schedules/ScheduleForm.tsx` |
| `web-schedule-runs` | web-schedule-runs-list | web-schedules-page | `code/agents-web/src/schedules/ScheduleRuns.tsx` |
| `web-schedules-page` | web-schedules-page | web-schedules-menu-entry | `code/agents-web/src/schedules/SchedulesPage.tsx` |
| `agents-schedule-db-release` | helmfile-schedule-db-release | helmfile-schedule-release | `code/agents-helmfile/helmfile.yaml.gotmpl` |
| `agents-schedule-release-values` | helmfile-schedule-release | deploy-schedule | `code/agents-helmfile/values/agents-schedule/common.yaml` |
| `agents-web-schedules-config` | web-config-schedules-backend | deploy-schedule | `code/agents-helmfile/values/agents-web/common.yaml` |

Consumed from agents-schedule-microservice: `agents-schedule-api`, `agents-schedule-chart`, `agents-schedule-image`, `agents-schedule-release`, `agents-schedule-settings-env`. Consumed from the rename epic: the agents-orchestrator names (`agents-orchestrator-services:8002`, `agents-orchestrator-proxy`, `agents-orchestrator-tls`, `values/agents-orchestrator/`). Others as in the original design (Contracts, consumed list).

### design.md: Review focus

- schedule-service-token and helmfile-schedule-release: the api pod behind SSO, the orchestrator reached only on the service port, no secret printed.
- web-schedules-menu-entry: the entry uses the reserved slot 30 and appears only with the backend configured.

### approvals.json

- A2: Map a cron schedule to a preset (with a prompt), managed as schedules. [decisions: D3, D4, D7, D12] [tasks: web-schedule-form, web-schedules-page] [status: approved]
- A4: The schedules UI lives in the web UI (agents-web) hamburger menu. [decisions: D12] [tasks: web-schedules-api-client, web-schedule-form, web-schedule-runs-list, web-schedules-page, web-schedules-menu-entry, web-config-schedules-backend] [status: approved]
- A5: Headless parity: a documented API and an API-only e2e for every capability. [decisions: D11] [tasks: smoke-schedule-check] [status: approved]
- A6: Releases, pin bumps, the CNPG database and helmfile apply plus smoke are tasks of this epic. [decisions: D13, D14] [tasks: helmfile-schedule-db-release, helmfile-schedule-release, schedule-service-token, smoke-schedule-check, deploy-schedule] [status: approved]
- A8: Runs after agents-webhook-microservice and frontend-decoupling and consumes the shared parts they own (DB and queue helpers, orchestrator client, service-to-service auth, preset binding, UI kit and page pattern); builds none of them. [decisions: D2] [tasks: web-schedule-form] [status: approved]
