---
title: agents-schedule microservice
blockers: []
stage: build
owner: ""
repos: [agents-schedule, agent-orchestrator, agents-helmfile]
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



## Non-goals



## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
