---
title: cluster scaling
blockers: [hive-mode-leadership-handove]
stage: review
owner: Szymon Richert
repos: [agent-orchestrator, agents-helmfile]
created: 2026-10-24
---

# cluster scaling

## Project brief

What: Agents join and leave a running cluster dynamically; the leader scales the cluster between 1 and a cap set at init
How: dynamic peer membership and hive-state updates on join and leave, a scale tool in the shared orchestrator any-mcp plugin, a per-cluster cap and a static switch
Why: A hive grows for parallel work and shrinks back without restarts

## Description

User request (2026-10-24), verbatim:

"scalling epic (extends "hive-mode" epic):
* it must be possible to dynamically join/leave agent cluster
* agents are offered tool, that allows to increase/decrease pods in the cluster (from 1 to N)"

Scope confirmation (user, 2026-10-24):
- The cap N is set at cluster init (a ClusterSpec field); the leader can scale the cluster within that cap.
- Scaling tools can be disabled per cluster: the cluster is then static. A static cluster with 1 pod has hive and messaging tools disabled: the agent is alone.
- The scale tool lives in the single shared "orchestrator" any-mcp plugin owned by the hive-mode-leadership-handove epic.

## Goals

- The leader agent scales its cluster between 1 and the cap set at init (ceiling 16) with the orchestrator_scale tool; users and headless callers do the same through POST /api/v1/clusters/{id}/scale and a scale control.
- Agents join and leave without restarting the others: surviving pod uids and the config hash stay unchanged; a busy leaving agent finishes its turn first; the leader is never removed.
- A static cluster cannot be scaled and offers no scale tool; a static single pod is alone.
- The cap and static switch are set in the preset form; every capability has a documented API and an API-only e2e test.
- Released and deployed: deploy pin, apply and a smoke with a scale step.

Design: design.md. Foundation (binding): hive-mode-leadership-handove F1-F5 provide the spec fields, seeds from the cap, agent API, plugin and leader tables; this epic consumes them.

## Non-goals

- No new spec fields, membership code, any-mcp or wrapper change (hive epic).
- No choice of which agent leaves (StatefulSet removes the highest ordinals), no autoscaling.

## Time

Estimate: 54 agent-min | Critical path: 27 min | Expected wall at P=1.5: 1.2 h (k=2.0) | Actual: 1 min | Remaining estimate: 5 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
