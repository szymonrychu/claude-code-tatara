---
title: agents-schedule component
blockers: []
stage: build
owner: Szymon Richert
repos: []
created: 2026-10-25
---

# agents-schedule component

## Project brief

What: Create the agents-schedule component repo
How: workbench:component-add makes the public GitHub repo and submodule; the Harbor CI secrets are set on it
Why: agents-schedule-microservice builds a new Python service; its tasks need code/agents-schedule to exist before they run

## Description

Split out of agents-schedule-microservice (2026-10-25) because ticket.py refuses an epic that mixes superrepo (meta) and component tasks, and every agents-schedule task needs `code/agents-schedule` to exist before its run starts (same split as agents-web-component). User decision (agents-schedule-microservice): creating the GitHub repo agents-schedule via workbench:component-add is an outward-facing operation, an explicit task listed at the gate.

User request (2026-10-25), verbatim, from agents-schedule-microservice: "## agents-schedule microservice
  * separate microservice allowing to map cronjob to preset - similar to agents-webhooks (maps cronjob to preset), lives in webUI in hamburger menu"

## Goals

- The public GitHub repo szymonrychu/agents-schedule exists, created by `mise run component:add`, and is the submodule `code/agents-schedule` of the workbench, tracking main.
- The repo has the CI secrets `HARBOR_USERNAME` and `HARBOR_PASSWORD`, and its README, MEMORY and AGENTS say what the component is.

## Non-goals

- No service code, image, chart or CI (agents-schedule-microservice tasks).
- No other repo is created and no existing component changes.

## Time

Estimate: 5 agent-min | Critical path: 5 min | Expected wall at P=1.5: 0.2 h (k=2.0) | Actual: 0 min | Remaining estimate: 5 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
