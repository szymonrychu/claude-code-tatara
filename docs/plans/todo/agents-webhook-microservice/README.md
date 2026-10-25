---
title: agents-webhook microservice
blockers: [frontend-decoupling, agents-webhook-component, agent-init-scripts, cluster-scaling]
stage: build
owner: ""
repos: [agents-common, agents-webhook, agent-orchestrator, agents-helmfile, agents-web]
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

- A new service, agents-webhook, with its own Postgres database, receives GitHub and GitLab PR/MR events (created, updated), issue events (created, updated) and comments, and Grafana alerts on public endpoints that check each source's signature.
- Every received event is stored in a FIFO queue table with content-aware dedup: platform/repo/mr-id for PRs and MRs, platform/repo/issue-id for issues and comments, the alert labels for Grafana.
- Limits hold: at most 3 events in progress at once and 1 per mapping, a 500-event queue cap, a 5 MiB body cap.
- A mapped event starts an agent cluster from its preset through the orchestrator API, sends the event as the first prompt and tracks the run until the first turn ends.
- A Webhooks entry in the web UI, between Clusters and Presets, lists recent events with their status (new, in-progress, handled, ignored, failed), maps an event to a preset and removes a mapping.
- The orchestrator accepts calls from other in-cluster services through bearer service tokens on a dedicated internal port.
- The shared library agents-common (settings, DB and queue helpers, orchestrator client, run tracker, preset binding) and the web trigger UI kit are built here for agents-schedule-microservice to reuse.
- Everything is released, pinned, deployed with its CNPG database in the agents namespace and proven by the smoke; every capability has a documented API and an API-only e2e.

## Non-goals

- No forge write-back: the service posts no comments or statuses to GitHub or GitLab.
- No cluster cleanup: the service never deletes clusters; autoclose belongs to configuration-improvements.
- No per-minute rate limiting and no per-project routing; one deployment serves one GitHub, one GitLab and one Grafana.
- No prompt field on presets or ClusterSpec; the prompt is a message.
- No change to the existing `/api/v1` routes of the orchestrator.

## Gate questions

Working answers are taken at the recommended answer under the standing approval (MEMORY.md 2026-10-23). Each is worded so that "yes" accepts it; answer "no" to override. The same questions are in design.md `## Open questions`.

1. Dedup: while the earlier event with the same key is `new`, the newer payload replaces it and keeps its FIFO place; while it is `in-progress`, the newer one is sent as an update message message to the same cluster and recorded `handled`, linked to it. Yes?
2. Limits mean concurrency caps (3 in progress overall, 1 per mapping, FIFO with alerts first), a 5 MiB body cap and a 500-event queue cap (newer events `ignored`, reason `queue_full`), with no per-minute rate limit. Yes?
3. Incoming auth is tatara-new parity (GitHub HMAC `X-Hub-Signature-256`, GitLab `X-Gitlab-Token`, Grafana `Authorization: Bearer`), one secret per source in a SOPS Secret, and the ingest endpoints are public at `https://lab.szymonrichert.pl/webhooks/<source>` in their own Deployment without SSO. Yes?
4. Ignored (still listed, with the reason): no mapping matches, the actor is a configured bot login, the action is closed, merged, labeled or a title-only edit, the Grafana status is resolved, a duplicate under 1, or the queue is full. Yes?
5. A fifth status `failed` (create, message or turn failed, or the run timed out after 1 h) with a reason. Yes?
6. An event is `handled` when its first turn completes; the service never deletes clusters (cleanup comes from autoclose in configuration-improvements). Yes?
7. A mapping is (source, kind mr|issue|comment|alert, repo or any, Grafana label subset) to a preset plus an optional prompt template; the most specific match wins; a mapping can be created from an event row and removed; creating one does not re-queue past events. Yes?
8. An optional global author allowlist: when set, issue and comment events from other authors are `ignored`. Yes?
9. Service-to-service auth: the orchestrator gets bearer service tokens (`ORCH_SERVICE_TOKENS`, sha256 hashes from a Secret) on a dedicated internal port 8002 that serves only the routes a trigger service needs. Yes?
10. Shared code lives in a new library component `agents-common`, pinned by git tag `v0.1.0` as any-mcp is. Yes?
11. The new GitHub repos `szymonrychu/agents-common` and `szymonrychu/agents-webhook` are public, like the other components, and are created with `workbench:component-add` by the separate meta epic agents-webhook-component, which runs before this one. Yes?
12. The Harbor repos `containers/agents-webhook` and `charts/agents-webhook` are used with the same `HARBOR_USERNAME`/`HARBOR_PASSWORD` CI secrets as agent-orchestrator, set on the new repo. Yes?

## Time

Estimate: 203 agent-min | Critical path: 105 min | Expected wall at P=3.0: 3.5 h (k=2.0) | Actual: 0 min | Remaining estimate: 203 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
