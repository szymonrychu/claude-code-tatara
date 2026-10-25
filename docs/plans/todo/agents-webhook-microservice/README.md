---
title: agents-webhook microservice
blockers: []
stage: build
owner: ""
repos: [agents-webhook, agent-orchestrator, agents-helmfile]
created: 2026-10-25
---

# agents-webhook microservice

## Project brief

What: A separate agents-webhook microservice with its own database: receives GitHub/GitLab PR/MR and issue webhooks and Grafana alerts, queues them FIFO with content-aware dedup and limits, sends them to the scheduler API, with a web UI of recent events and event-to-preset mappings
How: New Python component with its own DB and queue table, dedup keys per source, a mapping table, a client of the orchestrator API, a UI entry between Clusters and Presets
Why: Events from forges and alerts start agent clusters from presets, as in tatara-new

## Description

User request (2026-10-25), verbatim. Overall target: "Target getting more and more from tatara system (/Users/szymonri/Documents/tatara-new)"

"## agents-webhook microservice
  * separate microservice agents-webhook, with it's own database- it's responsible for getting webhook, caching it in FIFO queue and sending them into scheduler api
  (with content aware deduplication and limits). supported webhooks:
    * gitlab/github MR/PR created/updated (deduplication around: platform/repo/mr-id)
    * gitlab/github issue created/updated and comment added (deduplication around: platform/repo/issue-id)
    * grafana alert (deduplication around alert labels)
  * agents-webhook microservice has webUI entry between clusters and presets
    * recent events (along with their status: new/in-progress/handled/ignored)
    * allows to map event to preset (so event triggers an agent cluster defined with preset), allows to remove such mapping"

## Goals



## Non-goals



## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
