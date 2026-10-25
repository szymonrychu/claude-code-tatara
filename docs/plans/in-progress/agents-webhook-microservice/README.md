---
title: agents-webhook microservice
blockers: [frontend-decoupling, agents-webhook-component, agent-init-scripts, cluster-scaling]
stage: build
owner: Szymon Richert
repos: [agents-common, agents-webhook, agent-orchestrator, agents-helmfile, agents-web]
created: 2026-10-25
---

# agents-webhook microservice

## Project brief

What: A separate agents-webhook microservice with its own database: receives GitHub/GitLab PR/MR and issue webhooks and Grafana alerts on per-webhook URLs https://<base>/webhook/<suffix> (one type, one preset, basic auth each), queues them FIFO with content-aware dedup and limits, sends them to the scheduler API, optionally routes later events to the agent still running for the item, with a web UI to manage the webhook endpoints and see recent events
How: New Python component with its own DB (endpoints and an event queue table), dedup keys per endpoint, a client of the orchestrator API, an opt-in reuse_running_agent preset field, a UI entry between Clusters and Presets
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

Re-plan requirement (2026-10-25), verbatim:

"Add an ability to create webhook url in form of https://<base>/webhook/<random string>.
Such webhook will be defined as one of the supported types on creation.
When creating such webhook url user can provide:
* <random string> url suffix (by default it's random, user can supply any unique string)
* basic-auth credentials (by default random u/p are provided, user can override both)

User is required to provide a preset that will be used to run the webhook along with a type of the webhook (grafana alert/gitlab-issue/gitlab-mr/github-issue/github-pr). only these sink endpoints will be used onwards for any webhooks and such url will be unique for each assignment."

"Another requirement- as long as an agent handling specific event is running, it will receive any new webhooks/events instead of creating new one."

"(agent reuse is an optional feature, it can be set during preset creation)"

User decision (2026-10-25): re-plan this in-progress epic around these per-webhook endpoints; they replace the per-source ingest and the mapping table, which supersedes the mapping part of the original request above.

## Goals

- A new service, agents-webhook, with its own Postgres database, receives GitHub and GitLab PR/MR events (created, updated), issue events (created, updated) and comments, and Grafana alerts on per-webhook public URLs https://lab.szymonrichert.pl/webhook/<suffix>; each endpoint is created with exactly one type (grafana-alert, gitlab-issue, gitlab-mr, github-issue, github-pr), one required preset, a random or user-supplied unique suffix and random or user-supplied basic-auth credentials, and these endpoints are the only ingest path.
- Credentials are stored as salted hashes, checked in constant time, the password is shown once, unknown suffixes are indistinguishable from wrong credentials, and repeated failed authentications are throttled.
- Every received event is stored in a FIFO queue table with content-aware dedup per endpoint: platform/repo/mr-id for PRs and MRs, platform/repo/issue-id for issues and comments, the alert labels for Grafana.
- Limits hold: at most 3 events in progress at once and 1 per endpoint, a 500-event queue cap, a 5 MiB body cap.
- An endpoint event starts an agent cluster from the endpoint's preset through the orchestrator API, sends the event as the first prompt and tracks the run until the first turn ends; when the preset sets reuse_running_agent, later events for the same item go to the agent still running for it instead of a new cluster.
- A Webhooks entry in the web UI, between Clusters and Presets, creates endpoints (type, preset, optional suffix, optional credentials), shows the full URL and credentials once, rotates credentials, deletes endpoints, and lists recent events with their status (new, in-progress, handled, ignored, failed); the preset form has a Reuse running agent switch.
- The orchestrator accepts calls from other in-cluster services through bearer service tokens on a dedicated internal port, and presets carry the optional reuse_running_agent field.
- The shared library agents-common (settings, DB and queue helpers, orchestrator client, run tracker, preset binding, agent-reuse helpers in v0.2.0) and the web trigger UI kit are built here for agents-schedule-microservice to reuse.
- Everything is released, pinned, deployed with its CNPG database in the agents namespace and proven by the smoke; every capability has a documented API and an API-only e2e.

## Non-goals

- No forge write-back: the service posts no comments or statuses to GitHub or GitLab.
- No cluster cleanup: the service never deletes clusters; autoclose belongs to configuration-improvements.
- No rate limiting of successful deliveries and no per-source signature secrets; one URL per assignment instead.
- No editing of an endpoint's type or preset (delete and recreate) and no revealing a password after creation.
- No prompt field on presets or ClusterSpec; the prompt is a message.
- No change to the existing `/api/v1` routes of the orchestrator beyond the additive optional spec field.

## Gate questions

Re-plan 2026-10-25. Earlier working answers stand except where superseded (Q1 second half, Q2, Q3 auth and paths, Q4, Q7; see design.md Open questions). Each new or changed decision below is worded so that "yes" accepts it; answer "no" to override.

13. Endpoints: https://lab.szymonrichert.pl/webhook/<suffix>, a 32-char random URL-safe suffix by default or a unique user suffix ([A-Za-z0-9._~-]{1,128}), exactly one of the five types, one required preset, an optional prompt template; created, listed, credential-rotated and deleted, never edited (recreate to change type or preset). Yes?
14. Credentials: random username wh-<8 hex> and a 43-char random password by default, both overridable (password at least 16 chars), stored only as a salted scrypt hash; the password is shown once at create or rotate and never revealable later. Yes?
15. Enumeration: unknown or deleted suffix, missing or malformed header, wrong username or password all get the identical 401 with WWW-Authenticate Basic, a dummy scrypt runs for unknown suffixes, and auth is checked before the body is read. Yes?
16. Brute force: more than 10 failed authentications a minute from one client get 429 with Retry-After (in memory per ingest replica; client from X-Forwarded-For only behind the trusted ingress CIDR); successful deliveries stay unlimited. Yes?
17. The per-source HMAC/token checks and their three already-bootstrapped, never-applied SOPS secrets are dropped; an event of another type at an endpoint is stored ignored type_mismatch; endpoint_removed replaces no_mapping and mapping_removed. Yes?
18. Dedup keys are scoped per endpoint; latest-wins while new is kept; exact provider redeliveries (X-GitHub-Delivery, X-Gitlab-Event-UUID) are ignored as duplicate. Yes?
19. Agent reuse (when on): a new event whose dedup key matches an event whose cluster is still running (GET /clusters/{id} on the service port answers and it is not deleting or discarded, whether or not its first turn completed) is delivered to that cluster as an update message and recorded handled with a link to the parent run; a new cluster starts only when none runs for the key; autoclose ends it. Not the alternative reading "any event on the same endpoint goes to its running agent". Yes?
20. Reuse is opt-in per preset as the sparse spec field reuse_running_agent (default false); the orchestrator ignores it, so it applies only to trigger-service runs and user-created clusters ignore it; the worker reads it from the preset when it claims an event; agents-schedule honours it too, keyed by the schedule. Yes?
21. With reuse off, an event for a key already in progress waits until that run's first turn ends and then starts its own cluster (replacing the old update-message-while-in-progress rule). Yes?
22. Deliveries for one key go one at a time in arrival order, wait in the orchestrator queue while the agent is busy and are never merged, and count as handled once sent; if the cluster is discarded before or during delivery the event falls back to a new cluster and nothing is lost. Yes?
23. Limits: 3 in progress overall and 1 per endpoint (was per mapping); deliveries to a running agent bypass the caps; 500-event queue cap; 5 MiB body cap. Yes?
24. The shared reuse support ships as agents-common v0.2.0 (a new irreversible tag; v0.1.0 untouched) and agents-webhook moves its pin to v0.2.0. Yes?
25. The public ingest uses the singular /webhook/ prefix from your URL form, a second agents-webhook prefix beside the SSO-protected /webhooks/api/v1, still in its own Deployment without SSO. Yes?
26. The Webhooks page has an Endpoints section (create dialog with type, preset, optional suffix, optional credentials, optional template; a one-time credentials dialog with the full URL, copy buttons and per-type hints; a list with URL, type, preset, username, rotate and delete behind a confirm) above the recent events with status and endpoint filters, plus a Reuse running agent switch in the preset form. Yes?

## Time

Estimate: 281 agent-min remaining (32 open tasks) | Critical path: 118 min | Actual: see RETRO at close

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
