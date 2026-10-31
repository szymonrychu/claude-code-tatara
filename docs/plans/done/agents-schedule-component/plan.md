---
title: agents-schedule component
repos: []
created: 2026-10-25
owner: Szymon Richert
rung: 1
---

# agents-schedule component

## What and why

What: Create the agents-schedule component repo
How: workbench:component-add makes the public GitHub repo and submodule; the Harbor CI secrets are set on it
Why: agents-schedule-microservice builds a new Python service; its tasks need code/agents-schedule to exist before they run

Split out of agents-schedule-microservice (2026-10-25) because ticket.py refuses an epic that mixes superrepo (meta) and component tasks, and every agents-schedule task needs `code/agents-schedule` to exist before its run starts (same split as agents-web-component). User decision (agents-schedule-microservice): creating the GitHub repo agents-schedule via workbench:component-add is an outward-facing operation, an explicit task listed at the gate.

User request (2026-10-25), verbatim, from agents-schedule-microservice: "## agents-schedule microservice
  * separate microservice allowing to map cronjob to preset - similar to agents-webhooks (maps cronjob to preset), lives in webUI in hamburger menu"

## Scope ladder

### Rung 1: agreed scope (migrated)

- 1.1: The public GitHub repo szymonrychu/agents-schedule exists, created by `mise run component:add`, and is the submodule `code/agents-schedule` of the workbench, tracking main.
- 1.2: The repo has the CI secrets `HARBOR_USERNAME` and `HARBOR_PASSWORD`, and its README, MEMORY and AGENTS say what the component is.

## Agreed scope

Rung 1, migrated from the epic format: the epic's goals were its agreed scope.

## Non-goals

- No service code, image, chart or CI (agents-schedule-microservice tasks).
- No other repo is created and no existing component changes.

## Design

none recorded in the epic format

## Decisions

none recorded in the epic format

## Open questions

none

## Research

none recorded in the epic format

## Irreversible operations

none

## Migrated notes

### README.md: Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-25)

Evidence: reviewer PASS all ACs incl scope audit; AC3 secrets set by user and verified; superrepo mise run test all green, lint clean.
Orchestrator ran component:add (classifier refuses public repo creation in subagents).

### approvals.json

- A1: Create the public GitHub repo szymonrychu/agents-schedule via workbench:component-add (outward-facing, listed at the gate), as the submodule code/agents-schedule, with its Harbor CI secrets. [decisions: ] [tasks: create-agents-schedule-repo] [status: approved]
