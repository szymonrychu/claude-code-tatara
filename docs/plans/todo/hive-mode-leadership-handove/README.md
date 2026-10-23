---
title: hive mode leadership handover and shared activity feed
blockers: []
stage: build
owner: ""
repos: [agent-orchestrator, claude-code-wrapper, agents-helmfile]
created: 2026-10-23
---

# hive mode leadership handover and shared activity feed

## Project brief

What: In clustered (hive) mode agents hand over or take over cluster leadership with a tool, the orchestrator routes the next request to the leader, and every agent sees the others' tool calls and file writes and knows it works in a hive
How: A leadership tool in the wrapper's ccw MCP server emits an event the ingester already streams; the dispatcher applies epoch-fenced requests under its per-cluster claim lock and prefers the leader in the pick; a feed built from ingested events is pushed to each agent through a new wrapper notes inbox delivered as hook additionalContext; a hive CLAUDE.md fragment and a live hive-state note tell each agent its role
Why: Let 3 agents split work and keep fresh context by handing the user-facing role over instead of compacting, without them redoing or clobbering each other's work; whether it is faster is measured with orch bench

## Description

User request (2026-10-23), verbatim:

"Next epic concerning orchestrator:
in clustered mode, agents are offered a tool to hand-over or take-over cluster leadership, orchestrator respects this and routes next request, to another agent.
All agents should be aware of tool calls, file creation etc.
Aim here is to speed-up work (3 agents will work faster than 1, will have more context than 1.. maybe even 2)
Only research around this, describe with epics. Don't work on it RN"

Added requirement (2026-10-23): "Agents must be aware, that they work in hive mode".

"Clustered mode" is an agent-orchestrator cluster with more than one replica and peers on (ClusterSpec.peers, spec.py). This epic calls that mode, with leadership and the shared feed switched on, "hive mode".

Research findings with citations are in research.md next to this README. Do not start this epic before the user answers the open questions; the user said not to work on it now.

## Goals

- Hive mode is a per-cluster switch; in hive mode exactly one agent is the leader at a time, recorded by the orchestrator with an epoch.
- Every agent's main thread has a leadership tool (hand over to a named or any other agent, take over), offered through the wrapper's existing ccw MCP server.
- The orchestrator applies leadership requests in one place, fenced by epoch, and routes the next untargeted request of the cluster to the leader; an explicit user target still wins; a lost leader falls back to another ready agent.
- Every agent learns about the other agents' tool calls, file writes and finished turns through one capped, throttled activity feed built from the events the orchestrator already ingests.
- Every agent knows it works in hive mode: a hive fragment in its CLAUDE.md (role rules, tools, shared workdir), plus a live hive-state note (its own name, the leader and epoch, the peers with state and context) delivered at turn start and on change.
- The UI and API show the current leader; the stream carries leader changes.
- The speed-up claim is measured, not assumed: an `orch bench` arm with hive mode against the existing arms, results recorded.

## Non-goals

- No consensus protocol between agents: the orchestrator is the single authority for leadership.
- No hard file locks on the shared workdir; conflicts are surfaced as warnings in the feed.
- No change to non-hive clusters: round-robin dispatch stays as is when hive mode is off.
- No use of Claude Code agent teams inside the pods (native SendMessage stays disabled with peers on).
- No implementation now: research and epic only, as the user asked.

## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
