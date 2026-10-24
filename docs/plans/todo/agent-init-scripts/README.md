---
title: agent init scripts
blockers: [hive-mode-leadership-handove]
stage: build
owner: ""
repos: [agent-orchestrator, any-mcp, claude-code-wrapper, agents-helmfile]
created: 2026-10-24
---

# agent init scripts

## Project brief

What: Per-cluster init scripts stored on ClusterSpec and presets, run once per cluster, visible to the agent and editable by it
How: init_scripts field, a once-per-cluster run guarded by the orchestrator, scripts surfaced in the workdir and CLAUDE.md, an edit tool in the shared orchestrator any-mcp plugin writing to the cluster and its preset
Why: An agent knows how its environment was built and can improve it for the next cluster

## Description

User request (2026-10-24), verbatim:

"agent configuration epic:
* init scripts in the lab platform must be exposed to an agent that's been initialised with them (so it knows how it's initialised + it's able to edit it next time)
* init scripts are running once per cluster"

Scope confirmation (user, 2026-10-24): init scripts do not exist in agent-orchestrator yet (only the wrapper's per-pod init.setup_commands); this epic adds them to ClusterSpec and presets. An agent edit goes to the cluster's stored spec AND its source preset when there is one, so the next cluster from that preset gets it. The edit tool lives in the single shared "orchestrator" any-mcp plugin owned by the hive-mode-leadership-handove epic.

## Goals



## Non-goals



## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
