---
title: agents-schedule microservice
blockers: [agents-schedule-component, agents-webhook-microservice, frontend-decoupling, configuration-improvements, agent-init-scripts, cluster-scaling]
stage: build
owner: ""
repos: [agents-schedule]
created: 2026-10-25
---

# agents-schedule microservice

## Project brief

What: A separate agents-schedule microservice mapping cron schedules to presets, with a web UI entry in the hamburger menu
How: New Python component with its own DB, cron-to-preset mappings, triggering sessions through the orchestrator API, modelled on agents-webhook
Why: Scheduled agent runs from presets, as in tatara-new

## Description

User request (2026-10-25), verbatim. Overall target: "Target getting more and more from tatara system (/Users/szymonri/Documents/tatara-new)"

"## agents-schedule microservice
  * separate microservice allowing to map cronjob to preset - similar to agents-webhooks (maps cronjob to preset), lives in webUI in hamburger menu"

## Goals

- The agents-schedule service maps 5-field cron schedules (IANA timezone, default Europe/Warsaw) to presets with a prompt, fires each due schedule once, starts a session from the preset (or, when the preset sets `reuse_running_agent` and the schedule's earlier session still runs, posts the prompt there) through the orchestrator service port and tracks the run to handled or failed.
- Missed runs collapse into one catch-up run; a fire while the previous run is in flight is recorded ignored (previous_running); at most 3 runs in progress, 1 per schedule.
- `/schedules/api/v1` is documented with a committed openapi.json and covered route by route by an API-only kind e2e.
- v0.1.0 is released (tag, chart 0.1.0, image); deploy, the Schedules page and the live smoke are epic agents-schedule-deploy.

## Non-goals

- No Kubernetes CronJob, no prompt on presets, no orchestrator API change, no session deletion by this service.
- No shared library, orchestrator client, dispatch, fake orchestrator or UI kit code: agents-webhook-microservice and frontend-decoupling own them.
- The repo creation itself is epic agents-schedule-component.

Split 2026-10-25 (orchestrator ruling, scope unchanged): the agents-helmfile and agents-web tasks (deploy-schedule, helmfile-schedule-db-release, helmfile-schedule-release, schedule-service-token, smoke-schedule-check, web-config-schedules-backend, web-schedule-form, web-schedule-runs-list, web-schedules-api-client, web-schedules-menu-entry, web-schedules-page) moved to epic agents-schedule-deploy, which is blocked by this epic.

## Time

Estimate: 0 min | Actual: 0 min | Remaining estimate: 0 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
