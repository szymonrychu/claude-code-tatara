---
title: agent-orchestrator
blockers: [claude-code-wrapper orchestrator support, any-mcp]
stage: build
owner: Szymon Richert
repos: [agent-orchestrator]
created: 2026-10-22
---

# agent-orchestrator

## Project brief

What: agent-orchestrator, a new component (code/agent-orchestrator, public origin szymonrychu/agent-orchestrator): a web UI and headless /api/v1 that define, run, message and discard clusters of claude-code-wrapper pods in namespace agents, with a ribbon of live state and context gauges, a smart-loading chat of every agent, round-robin dispatch to the agent free the longest with automatic never-twice retries, peer messaging, a shared RWX CephFS workspace, any-mcp installed in every session by a rendered onStart hook, and its own Helm chart.
How: one Python repo and image with four processes (api, dispatcher, ingester, reconciler) coordinating only through a CNPG Postgres (SKIP LOCKED queues, LISTEN/NOTIFY hints, polling fallback); the reconciler server-side-applies a StatefulSet, headless Service, RWX PVC, ConfigMap and Secret per cluster, label-partitioned in one namespace, and discards everything after an optional JSONL history-export hook; the ingester stores every wrapper event; a React 19 / MUI 9 / Vite 8 frontend ported from the ros2 web UI theme uses only the public API; a bench CLI runs the experiment arms; GitHub CI pushes the orchestrator image to Harbor, publishes the chart (Postgres required, CNPG optional) to oci://harbor.szymonrichert.pl/charts and runs a kind e2e that installs it.
Why: the user wants to test whether round-robin plus multiple agents plus inter-agent messaging makes agents faster, more robust and more correct, and needs one router whose API tatara and magic-trainer will consume at scale.

## Description

agent-orchestrator: microservice web UI and headless API for orchestrating Kubernetes pods running claude-code-wrapper. Left ribbon lists active pods or clusters with waiting/working state, running-pod count and a circular 0-100% context gauge; the main view is a lazily loaded chat of agent activity (inputs, outputs, thinking, tool calls). Clusters are defined and discarded from the UI; messages go round-robin to the agent free the longest; cluster agents share an RWX CephFS PVC and can message each other; every session starts with any-mcp preinstalled. The headless API is the unified router for future tatara and magic-trainer use. Theme copied from the ros2 web UI. Design: design.md in this epic.

## Goals

- Headless /api/v1 REST plus SSE covering clusters, agents, messages, events and checks.
- Round-robin dispatch to the agent free the longest, queued while all are busy.
- Cluster create/edit/discard reconciled into StatefulSet, headless Service, RWX PVC, ConfigMap, Secret in namespace agents; discard deletes everything incl. history, after an optional pre-discard export hook.
- Web UI: ribbon with state, pod count and context gauge; virtualised chat with backward paging and live updates; cluster forms and discard dialog.
- any-mcp installed per agent pod by a rendered onStart hook from a pinned tag (no derived image); AskUserQuestion disabled, agents ask in writing.
- A bench CLI to compare round-robin, multiple agents and peer messaging.
- CI pushes the orchestrator image to Harbor and publishes the Helm chart chart/agent-orchestrator with immutable versions.

## Non-goals

- No authentication (LAN-only for now).
- No special prompts for clustered agents.
- No answering AskUserQuestion from the UI (the tool is disabled).
- No helmfile release or SOPS secrets (epic agents-helmfile).

## Time

Estimate: 274 agent-min | Critical path: 82 min | Expected wall at P=1.5: 6.1 h (k=2.0) | Actual: 0 min | Remaining estimate: 5 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-23)

Panel review (fable, opus, sonnet) of the implementation: acted on the ingress SNAT bypass (node-IP denylist at the ingress, chart values allow/denySourceRanges, README boundary), stored dead sessions resumed or replaced, ambiguous-deadline reservation released, wrapper 500/502 routed through the verifier, discard quiesces agents before export; all other design-review Act-on items verified implemented. Scope audit: A1-A27 landed, 354 AC refs resolve. Final tip: unit 393 passed, integration (real wrapper) 8 passed, kind e2e 8 passed, chart tests, lint, chart lint, frontend lint/test (90)/build all green.
Rulings: descriptive branch values from implementers rewritten to task branches; missing owner dependencies added for 21 tasks; renderer landed by cherry-picking its own commits onto the epic tip; parking-wording false positives accepted (readme, reconciler, session-bootstrap).
