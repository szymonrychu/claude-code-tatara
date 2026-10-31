---
title: agents-webhook component
repos: []
created: 2026-10-25
owner: Szymon Richert
rung: 1
---

# agents-webhook component

## What and why

What: Create the agents-common and agents-webhook component repos
How: workbench:component-add makes each public GitHub repo and its submodule under code/
Why: agents-webhook-microservice builds a shared library and a service in two new repos; its tasks need code/agents-common and code/agents-webhook to exist before they run

Split out of agents-webhook-microservice (2026-10-25) because ticket.py refuses an epic that mixes superrepo (meta) and component tasks, and every agents-common and agents-webhook task of agents-webhook-microservice needs `code/agents-common` and `code/agents-webhook` to exist before its run starts. User decision (agents-webhook-microservice): creating the GitHub repos agents-webhook and agents-common via workbench:component-add is outward-facing, explicit tasks listed at the gate.

User request (2026-10-25), verbatim, from agents-webhook-microservice: "## agents-webhook microservice
  * separate microservice agents-webhook, with it's own database- it's responsible for getting webhook, caching it in FIFO queue and sending them into scheduler api
  (with content aware deduplication and limits)."

## Scope ladder

### Rung 1: agreed scope (migrated)

- 1.1: The public GitHub repo szymonrychu/agents-common exists, created by `mise run component:add`, and is the submodule `code/agents-common` (branch main) of the workbench.
- 1.2: The public GitHub repo szymonrychu/agents-webhook exists the same way as `code/agents-webhook`.
- 1.3: Both scaffolds pass their smoke test and `mise run lint`, and AGENTS.md lists both components with their roles.

## Agreed scope

Rung 1, migrated from the epic format: the epic's goals were its agreed scope.

## Non-goals

- No package, Dockerfile, CI, chart or service code in the new repos (agents-webhook-microservice tasks common-scaffold and webhook-scaffold onward).
- No Harbor repository or CI secret setup (agents-webhook-microservice task webhook-ci-images).

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

Evidence: reviewer PASS both tasks, all ACs met, scope audit clean; superrepo mise run test all green, lint clean.
Orchestrator ran component:add for both repos (classifier refuses public repo creation in subagents; user-approved allow rule). architecture.md root label fixed in 4dcb409.

### approvals.json

- A6: Creating the public GitHub repos szymonrychu/agents-common and szymonrychu/agents-webhook via workbench:component-add is an outward-facing operation, explicit tasks listed at the agents-webhook-microservice gate (user decision, 2026-10-25). [decisions: ] [tasks: create-agents-common-repo, create-agents-webhook-repo] [status: approved]
