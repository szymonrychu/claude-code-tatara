---
title: agents-schedule microservice
blockers: [agents-schedule-component, agents-webhook-microservice, frontend-decoupling, configuration-improvements, agent-init-scripts, cluster-scaling]
stage: build
owner: ""
repos: [agents-schedule, agents-web, agents-helmfile]
created: 2026-10-25
---

# agents-schedule microservice

## Project brief

What: A separate agents-schedule microservice mapping cron schedules to presets, with a web UI entry in the hamburger menu
How: New Python component with its own DB, cron-to-preset mappings, triggering clusters through the orchestrator API, modelled on agents-webhook
Why: Scheduled agent runs from presets, as in tatara-new

## Description

User request (2026-10-25), verbatim. Overall target: "Target getting more and more from tatara system (/Users/szymonri/Documents/tatara-new)"

"## agents-schedule microservice
  * separate microservice allowing to map cronjob to preset - similar to agents-webhooks (maps cronjob to preset), lives in webUI in hamburger menu"

## Goals

- The agents-schedule service maps 5-field cron schedules (IANA timezone, default Europe/Warsaw) to presets with a prompt, fires each due schedule once, starts a cluster from the preset through the orchestrator service port and tracks the run to handled or failed.
- Missed runs collapse into one catch-up run; a fire while the previous run is in flight is recorded ignored (previous_running); at most 3 runs in progress, 1 per schedule.
- `/schedules/api/v1` is documented with a committed openapi.json and covered route by route by an API-only kind e2e.
- A Schedules page in agents-web, between Webhooks and Presets in the hamburger menu, manages schedules and shows run history.
- v0.1.0 is released and deployed with its own CNPG database to the agents namespace; the live smoke covers it.

## Non-goals

- No Kubernetes CronJob, no prompt on presets, no orchestrator API change, no cluster deletion by this service.
- No shared library, orchestrator client, dispatch, fake orchestrator or UI kit code: agents-webhook-microservice and frontend-decoupling own them.
- The repo creation itself is epic agents-schedule-component.

## Time

Estimate: 157 agent-min | Critical path: 68 min | Expected wall at P=2.9: 2.3 h (k=2.0) | Actual: 0 min | Remaining estimate: 157 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
