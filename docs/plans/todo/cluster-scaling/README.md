---
title: cluster scaling
blockers: [hive-mode-leadership-handove]
stage: build
owner: ""
repos: [agent-orchestrator, any-mcp, claude-code-wrapper, agents-helmfile]
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



## Non-goals



## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
