---
title: frontend decoupling
blockers: [agent-init-scripts, cluster-scaling, agents-web-component]
stage: review
owner: Szymon Richert
repos: [agents-web, agent-orchestrator, agents-helmfile]
created: 2026-10-25
---

# frontend decoupling

## Project brief

What: Decouple the web frontend from the orchestrator microservice
How: The frontend ships and runs on its own, talking to the orchestrator only through its documented HTTP API
Why: Services talk only through the queue or HTTP; new microservices (webhook, schedule) need UI entries without living in the orchestrator

## Description

User request (2026-10-25), verbatim. Overall target: "Target getting more and more from tatara system (/Users/szymonri/Documents/tatara-new)"

"## frontend decoupling
  * decouple frontend from orchestrator microservice"

## Goals

- The web UI lives in its own component `agents-web` (TypeScript, history of `agent-orchestrator/frontend` kept) with its own static image (nginx-unprivileged), chart and CI, published to Harbor.
- The browser stays on one host, `lab.szymonrichert.pl`: ingress path routing sends `/` to agents-web, `/api` to the orchestrator, and reserves one prefix per later service; no CORS.
- The UI reads its backends from a runtime `config.json` set by its chart; a backend's menu entries appear only when it is configured, so webhook and schedule add UI entries without touching the orchestrator.
- The orchestrator no longer builds or serves the UI: no node stage, no `SpaStaticFiles`, no `ORCH_STATIC_DIR`, no npm in its CI; `GET /` on the api is a JSON 404. Its API stays documented and tested API-only and the kind e2e keeps passing.
- Released and deployed in two steps: agents-web release plus ingress split, smoked live; then the orchestrator without the UI, smoked live.

Design: design.md. Runs after agent-init-scripts and cluster-scaling (their UI moves with the rest) and after agents-web-component creates `code/agents-web`.

## Non-goals

- No UI feature change and no new backend: webhook and schedule UIs are their own epics, built on this epic's contracts.
- No CORS, no BFF or gateway, no auth layer in the web app, no subdomain per service, no micro-frontends.
- No browser e2e (Playwright): vitest, the image smoke and the live smoke cover it.
- No change to the oauth2-proxy injector or the `agent-orchestrator-proxy` Secret.

## Time

Estimate: 86 agent-min | Critical path: 56 min | Expected wall at P=1.5: 1.9 h (k=2.0) | Actual: 0 min | Remaining estimate: 86 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-25)

- Repo name: user asked about "agents-frontend", then chose "Keep agents-web as is".
- create repo step and every live apply run by the orchestrator (classifier refuses them in subagents; user approved rules).
- web-chart-config-ingress: fix rounds: test:chart glob (Node 24), helm test pod pinned and hardened.
- web-backend-menu: fix round: menu entries memoised (warn per render).
- orch-drop-frontend-build: AC7 amended (contradicted the requirement's sync:api README note); AC6 evidenced by PR #13 CI e2e pass.
- deploy-pin-web: first live apply failed on duplicate imagePullSecrets (chart concat of values + global); root fix agents-web PR #2 (dedupe), re-pinned to db1f482; agent-orchestrator untouched by the failed apply.
- smoke-web-ui: two live bugs fixed after cutover (port-forward hit the SSO sidecar; config.json keyed by id); user confirmed UI loads (Q6).
- security: MEDIUM regctl-installer@main pinned (fix PR); MEDIUM in-cluster http-insecure port to static UI: dropped (static content, NetworkPolicy is new scope); LOW mutable base tags, missing nginx security headers, origin check scope: dropped (match existing repos / speculative).
- epic review: whole-diff PASS; findings acted on: chart config.json validation parity with parseConfig and helm test bypassing the sidecar (agents-web PR #4), regctl-installer pinned (PR #3); re-pinned live to cedcbbc (task repin-web-after-review-fixes, helmfile PR #19), smoke OK.
- PRs merged: agents-web #1 #2 #3 #4, agent-orchestrator #13, agents-helmfile #18 #19. Live: agents-web 0.1.0-main.cedcbbc on /, agent-orchestrator 0.1.0-main.a4be86b (API-only) on /api.
