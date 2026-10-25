# agents-schedule deploy design

## Summary

The agents-helmfile and agents-web half of epic agents-schedule-microservice, split out with scope unchanged. This
epic deploys the agents-schedule service (CNPG database, release, SOPS service token, agents-web backend config, smoke
step) and adds the Schedules page to agents-web. The service, chart, image and v0.1.0 release are built by the
blocker agents-schedule-microservice; the renamed orchestrator (agents-orchestrator, sessions) by the blocker
orchestrator-rename-sessions. The shared decisions (D1-D11, D13, D15), the contracts of the service and the open
questions are in `../agents-schedule-microservice/design.md`; this file holds D12 and the deploy half of D14, copied
verbatim with their numbers.

## Intent and why

See `../agents-schedule-microservice/design.md` (Intent and why). The split only separates what needs the
agents-orchestrator names live (deploy, smoke) and the web UI from the service build.

## Goals

- G6: the Schedules page in agents-web manages schedules and shows runs with a session link; its menu entry sits between Webhooks and Presets and appears only when the backend is configured.
- G8: v0.1.0 is deployed with its CNPG database to the agents namespace, and the live smoke covers it.

## Non-goals

- Any change to the agents-schedule service, chart or release (agents-schedule-microservice).
- No new shared UI kit or backend registry code (agents-webhook-microservice, frontend-decoupling).

## Constraints

- Blocked by orchestrator-rename-sessions and agents-schedule-microservice (README blockers); task depends_on entries that pointed at tasks of the other epic (release-v0-1-0, chart-ingress-and-test-hook, api-docs-and-openapi) are dropped, the epic blocker covers them.
- Live applies (`mise run apply`) are run by the orchestrator in the main session.

## Decisions

### D12: UI in agents-web

`src/schedules/`: API client typed from the vendored `openapi/schedules.json`, `ScheduleForm` (cron, timezone, `PresetSelect`, prompt, live preview), `ScheduleRuns` (`RunStatusChip`, session link, `usePoll`), `SchedulesPage` (enable/disable, run now, edit, delete with confirm, expandable runs). The menu entry is registered in `src/backends/registry.ts` (`agents-web-backend-registry`) at its reserved order 30, giving Sessions 10, Webhooks 20, Schedules 30, Presets 40 (gate Q7, `web-settings-menu-order`), shown only when `config.json` lists the `schedules` backend. Gates Q6, Q7. Approvals A2, A4.

### D14: Release and deploy

Tag v0.1.0 on the merged main commit (chart 0.1.0). agents-helmfile: release `agents-schedule-db` (cnpg/cluster 0.9.0) and `agents-schedule` (needs the db; DB URL from `agents-schedule-db-cluster-app` key `uri`; orchestrator `http://agents-orchestrator-services:8002` (`orch-services-service`) with `orchestrator.token` from SOPS `values/agents-schedule/default.secrets.yaml`; host `lab.szymonrichert.pl` path `/schedules`); `bootstrap-secrets.sh` writes the token (raw into `values/agents-schedule/default.secrets.yaml`, its sha256 as `serviceApi.tokenHashes.agents-schedule` into `values/agents-orchestrator/service-token-agents-schedule.secrets.yaml`, as agents-webhook task helmfile-service-token); the agents-web values gain the `schedules` backend and the agents-web pin moves to the build with the Schedules page; the smoke gains a schedule step; then `mise run apply` and `mise run smoke`. Gate Q10. Approval A6.

## Decision coverage

| Decision | Tasks |
|---|---|
| D12 UI in agents-web | web-schedules-api-client, web-schedule-form, web-schedule-runs-list, web-schedules-page, web-schedules-menu-entry, web-config-schedules-backend |
| D14 Release and deploy | helmfile-schedule-db-release, helmfile-schedule-release, schedule-service-token, web-config-schedules-backend, smoke-schedule-check, deploy-schedule |

## Contracts

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

## Review focus

- schedule-service-token and helmfile-schedule-release: the api pod behind SSO, the orchestrator reached only on the service port, no secret printed.
- web-schedules-menu-entry: the entry uses the reserved slot 30 and appears only with the backend configured.
