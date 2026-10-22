---
title: agent-orchestrator
blockers: [claude-code-wrapper orchestrator support, any-mcp]
stage: build
owner: ""
repos: [agent-orchestrator]
created: 2026-10-22
---

# agent-orchestrator

## Project brief

What: 
How: 
Why: 

## Description

agent-orchestrator: microservice web UI and headless API for orchestrating Kubernetes pods running claude-code-wrapper. Left ribbon lists active pods or clusters with waiting/working state, running-pod count and a circular 0-100% context gauge; the main view is a lazily loaded chat of agent activity (inputs, outputs, thinking, tool calls). Clusters are defined and discarded from the UI; messages go round-robin to the agent free the longest; cluster agents share an RWX CephFS PVC and can message each other; every session starts with any-mcp preinstalled. The headless API is the unified router for future tatara and magic-trainer use. Theme copied from the ros2 web UI. Design: /private/tmp/claude-501/-Users-szymonri-Documents-claude-code-tatara/21d1a847-8d6b-4ee4-a271-ba52ec27cf3b/scratchpad/orch/design-orchestrator.md.

## Goals

- Headless /api/v1 REST plus SSE covering clusters, agents, messages, events and checks.
- Round-robin dispatch to the agent free the longest, queued while all are busy.
- Cluster create/edit/discard reconciled into StatefulSet, headless Service, RWX PVC, ConfigMap, Secret.
- Web UI: ribbon with state, pod count and context gauge; virtualised chat with backward paging and live updates; cluster forms and discard dialog.
- Agent image with any-mcp preinstalled.
- A bench CLI to compare round-robin, multiple agents and peer messaging.
- CI builds and pushes both images to Harbor.

## Non-goals

- No authentication (LAN-only for now).
- No special prompts for clustered agents.
- No answering AskUserQuestion from the UI.

## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
