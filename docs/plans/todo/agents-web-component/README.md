---
title: agents-web component
blockers: [agent-init-scripts, cluster-scaling]
stage: build
owner: ""
repos: []
created: 2026-10-25
---

# agents-web component

## Project brief

What: Create the agents-web component repo with the frontend history
How: workbench:component-add makes the public GitHub repo and submodule, then the agent-orchestrator frontend history is merged in at the repo root
Why: frontend-decoupling moves the UI into its own TypeScript component; its tasks need code/agents-web to exist before they run

## Description

Split out of frontend-decoupling (2026-10-25) because ticket.py refuses an epic that mixes superrepo (meta) and component tasks, and every agents-web task of frontend-decoupling needs `code/agents-web` to exist before its run starts. User decision (frontend-decoupling): creating the GitHub repo agents-web via workbench:component-add is an outward-facing operation, an explicit task listed at the gate.

User request (2026-10-25), verbatim, from frontend-decoupling: "## frontend decoupling
  * decouple frontend from orchestrator microservice"

## Goals

- The public GitHub repo szymonrychu/agents-web exists, created by `mise run component:add`, and is the submodule `code/agents-web` of the workbench.
- Its main carries the full history of `code/agent-orchestrator/frontend` (moved to the repo root) on top of the component scaffold, and `npm ci && npm test && npm run lint` pass there.

## Non-goals

- No change to the moved UI code, its API client, image, chart or CI (frontend-decoupling tasks).
- No deletion of `frontend/` from agent-orchestrator (frontend-decoupling task orch-drop-frontend-build).

## Time

Estimate: 5 agent-min | Critical path: 5 min | Expected wall at P=1.5: 0.2 h (k=2.0) | Actual: 0 min | Remaining estimate: 5 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
