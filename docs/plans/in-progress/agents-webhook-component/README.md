---
title: agents-webhook component
blockers: []
stage: review
owner: Szymon Richert
repos: []
created: 2026-10-25
---

# agents-webhook component

## Project brief

What: Create the agents-common and agents-webhook component repos
How: workbench:component-add makes each public GitHub repo and its submodule under code/
Why: agents-webhook-microservice builds a shared library and a service in two new repos; its tasks need code/agents-common and code/agents-webhook to exist before they run

## Description

Split out of agents-webhook-microservice (2026-10-25) because ticket.py refuses an epic that mixes superrepo (meta) and component tasks, and every agents-common and agents-webhook task of agents-webhook-microservice needs `code/agents-common` and `code/agents-webhook` to exist before its run starts. User decision (agents-webhook-microservice): creating the GitHub repos agents-webhook and agents-common via workbench:component-add is outward-facing, explicit tasks listed at the gate.

User request (2026-10-25), verbatim, from agents-webhook-microservice: "## agents-webhook microservice
  * separate microservice agents-webhook, with it's own database- it's responsible for getting webhook, caching it in FIFO queue and sending them into scheduler api
  (with content aware deduplication and limits)."

## Goals

- The public GitHub repo szymonrychu/agents-common exists, created by `mise run component:add`, and is the submodule `code/agents-common` (branch main) of the workbench.
- The public GitHub repo szymonrychu/agents-webhook exists the same way as `code/agents-webhook`.
- Both scaffolds pass their smoke test and `mise run lint`, and AGENTS.md lists both components with their roles.

## Non-goals

- No package, Dockerfile, CI, chart or service code in the new repos (agents-webhook-microservice tasks common-scaffold and webhook-scaffold onward).
- No Harbor repository or CI secret setup (agents-webhook-microservice task webhook-ci-images).

## Time

Estimate: 10 agent-min | Critical path: 10 min | Expected wall at P=1.5: 0.3 h (k=2.0) | Actual: 0 min | Remaining estimate: 10 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-25)

Evidence: reviewer PASS both tasks, all ACs met, scope audit clean; superrepo mise run test all green, lint clean.
Orchestrator ran component:add for both repos (classifier refuses public repo creation in subagents; user-approved allow rule). architecture.md root label fixed in 4dcb409.
