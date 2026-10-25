---
title: agents-schedule deploy
blockers: [orchestrator-rename-sessions, agents-schedule-microservice]
stage: review
owner: Szymon Richert
repos: [agents-helmfile, agents-web]
created: 2026-10-25
---

# agents-schedule deploy

## Project brief

What: The agents-helmfile and agents-web half of agents-schedule-microservice: deploy the agents-schedule service (CNPG database, release, service token), the live smoke step, the agents-web Schedules page and its hamburger menu entry
How: agents-web gets a typed schedules client, form, run list, page and menu entry between Webhooks and Presets; agents-helmfile gets the agents-schedule-db and agents-schedule releases, the SOPS service token, the schedules backend in the agents-web values and a smoke schedule step, then apply and smoke
Why: Scheduled agent runs from presets, as in tatara-new; split from agents-schedule-microservice so the service epic can land without waiting on the rename-dependent deploy and UI work

## Description

Split from epic agents-schedule-microservice on 2026-10-25 (orchestrator ruling): this epic holds its agents-helmfile and agents-web tasks, unchanged in scope. It runs after orchestrator-rename-sessions (agents-orchestrator names, sessions) and after agents-schedule-microservice (the service, chart and v0.1.0 release it deploys). Decisions D12 and the deploy half of D14 are in this epic's design.md; everything else is in `../agents-schedule-microservice/design.md`.

Original user request (2026-10-25), verbatim: "## agents-schedule microservice
  * separate microservice allowing to map cronjob to preset - similar to agents-webhooks (maps cronjob to preset), lives in webUI in hamburger menu"

## Goals

- A Schedules page in agents-web, between Webhooks and Presets in the hamburger menu, manages schedules and shows run history with a session link.
- agents-schedule v0.1.0 is deployed with its own CNPG database to the agents namespace through agents-helmfile (service token, release pair, agents-web backend config), and the live smoke covers it.

## Non-goals

- No change to the agents-schedule service code, chart or release: epic agents-schedule-microservice owns them and is a blocker.
- No Kubernetes CronJob, no prompt on presets, no orchestrator API change, no session deletion by the schedule service.
- No shared UI kit or backend registry code: agents-webhook-microservice and frontend-decoupling own them.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
