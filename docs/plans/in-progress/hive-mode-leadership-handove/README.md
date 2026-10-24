---
title: hive mode leadership handover and shared activity feed
blockers: []
stage: build
owner: Szymon Richert
repos: [any-mcp, claude-code-wrapper, agent-orchestrator, agents-helmfile]
created: 2026-10-23
---

# hive mode leadership handover and shared activity feed

## Project brief

What: Every multi-agent cluster is a hive: one leader at a time, recorded by the orchestrator with an epoch; the leader hands leadership over with a tool (or the user makes any agent leader); untargeted messages go to the leader; every agent sees the others' file writes, commands and finished turns, claims files with advisory locks, and knows from its tools that it works in a hive
How: One shared "orchestrator" any-mcp plugin calls a new agent-only port of the orchestrator API with a per-cluster token bound to the pod IP; the dispatcher applies epoch-fenced leadership requests under its per-cluster claim lock and routes to the leader; a feed and hive-state note built from ingested events reach each agent through a new wrapper notes inbox as hook additionalContext; tool visibility is fixed at render from the cluster's replica cap and static switch
Why: Let several agents split work and keep fresh context by handing the user-facing role over instead of compacting, without redoing or clobbering each other's work; whether it is faster is measured with orch bench

## Description

User request (2026-10-23), verbatim:

"Next epic concerning orchestrator:
in clustered mode, agents are offered a tool to hand-over or take-over cluster leadership, orchestrator respects this and routes next request, to another agent.
All agents should be aware of tool calls, file creation etc.
Aim here is to speed-up work (3 agents will work faster than 1, will have more context than 1.. maybe even 2)
Only research around this, describe with epics. Don't work on it RN"

Added requirement (2026-10-23): "Agents must be aware, that they work in hive mode".

On 2026-10-24 the user answered the open questions, confirmed the scope and asked to build it ("After confirming scope, run all at once"). Decisions: `docs/plans/todo/hive-mode-leadership-handove/design.md` and the list below.

A hive is any cluster whose replica cap `max_replicas` is above 1 (Q12: no opt-in switch). A cluster with cap 1 is alone: no hive, peers or messaging tools.

This epic also builds the foundation (F1-F5) that cluster-scaling and agent-init-scripts build on: the orchestrator any-mcp plugin, the wrapper notes inbox and main-agent gate, ClusterSpec `max_replicas` and `static` with render gating, the agent API, and migration 0003. Research findings with citations are in research.md next to this README.

## Goals

- Exactly one leader per hive, recorded by the orchestrator with an epoch; the first ready agent leads when a hive starts (Q2).
- Agents see an orchestrator any-mcp plugin (X1, Q3) whose tools hint the hive mode on load (Q7): `me`, `leadership_handover`, and advisory `lock_*` tools.
- Only the current leader hands leadership away, to a named or any agent; a stale epoch is rejected; no takeovers (Q4). The user can make any agent leader from the UI and the API (Q10).
- Untargeted messages go to the leader only; an explicit target still wins; a lost leader is replaced (Q1).
- Every hived agent gets the feed (file writes, edits and deletes as paths, Bash commands with exit status cut at 200 chars, finished turns with their first line, leadership changes; Q5) and a hive-state note, through the wrapper notes inbox as hook additionalContext at the next tool result (throttled) and the next prompt (Q6).
- Advisory file locks: claim, a warning on writing another agent's file, the leader reassigns or discards any lock (Q11).
- Context is visible per agent; handing over above `auto_compact_pct - 15` is advised, never forced (Q9).
- The UI and API show the leader; the stream carries leader changes; every UI capability has a documented public API and an API-only e2e test (X2).
- The speed-up claim is measured with an `orch bench` hive arm and recorded (Q12).
- Releases: any-mcp v0.2.0, claude-code-wrapper 0.2.0, orchestrator pins, agents-helmfile bump, apply and smoke.

## Non-goals

- No takeovers by agents and no forced handover (Q4, Q9).
- No hive switch in ClusterSpec (Q8, Q12); no CLAUDE.md hive fragment (Q7).
- No consensus protocol between agents: the orchestrator is the single authority for leadership.
- No hard file locks: locks are advisory.
- No Claude Code agent teams inside the pods (native SendMessage stays disabled with peers on).
- The scale route (cluster-scaling) and init scripts (agent-init-scripts) are built in their epics; this epic ships their plugin tools and extension points.

## Related epics and order

The earlier prerequisites (cluster-form-defaults-and-ga, web-ui-cluster-tabs-with-fil, cluster-presets) are done, so Q13 is moot. This epic runs first; cluster-scaling and agent-init-scripts are blocked by it and wait on its foundation tasks (design.md D6, `docs/plans/contracts.json`). workspace-ui-fixes shares the frontend but no files with this epic's tasks.

## Scope

- any-mcp: built-in `OrchestratorPlugin` with the full tool surface for all three epics; release v0.2.0.
- claude-code-wrapper: notes inbox (`POST /v1/sessions/{id}/notes`, keyed and appended notes, throttled delivery as additionalContext, events), `claude.main_agent_only_tools`; release 0.2.0.
- agent-orchestrator: ClusterSpec `max_replicas` and `static` (and their form inputs); migration 0003; agent port, token, pod-IP identity and `/agent/v1/me`; render gating (seeds from the cap, peers and notes only for hives, main-agent-only tools, lock-check webhook, plugin entry); leadership requests, dispatcher leadership pass and leader routing; advisory locks; feed and hive-state push; views, stream frame and UI; bench arm; kind e2e; pins; chart agents Service.
- agents-helmfile: version bumps, apply, smoke.

## Decisions (user)

- X1: one shared "orchestrator" any-mcp plugin carries every agent-to-orchestrator tool, with a per-cluster credential in the pod; built here.
- X2: headless parity: every UI capability has a documented public API and an API-only e2e test.
- Q1: yes, the leader is the only agent that receives untargeted messages.
- Q2: the first ready agent leads when a hive starts (epoch 1).
- Q3: the tools are offered through an any-mcp plugin, not the wrapper's ccw MCP server.
- Q4: handover only; only the current leader gives leadership away; stale epoch rejected.
- Q5: feed contents as in Goals; no tool outputs, no Read, Grep or Glob.
- Q6: delivered through the wrapper notes inbox as hook additionalContext.
- Q7: tools on load hint the mode; the notes inbox only for hived agents; a static single-pod cluster has no hive, peers or messaging tools.
- Q8 and Q12: no ClusterSpec hive switch; every multi-agent cluster is a hive; the bench records the result.
- Q9: no forced handover; advise only.
- Q10: user "make leader" in UI and API through the same queue; it overrides handover-only.
- Q11: advisory locks; the leader can reassign or discard a lock.
- Q13: moot, the prerequisite epics are done.

## Open questions

none

## Risks

- The speed-up may not materialise (research.md section 7); the bench run records the result.
- Feed cost: tight filtering, own-line removal, caps and throttle keep context growth bounded.
- Inter-agent prompt injection: notes are framed as data from peers, never user instructions.
- Leader as bottleneck: a long leader turn delays untargeted messages; explicit targets still dispatch.
- Opening an agent path to the orchestrator: a separate port, a per-cluster token and pod-IP binding; the public API stays closed to pods.
- One pod roll per existing cluster on upgrade (new env and rendered config).

## Rough task list

Task files under `tasks/`; foundation first (F1 orchestrator-plugin, any-mcp-release-v0-2-0; F2 main-agent-only-tools, wrapper-notes-inbox, wrapper-notes-delivery, wrapper-release-0-2-0; F3 spec-cap-static, agent-token-env-render, orch-pin-bumps, render-hive-gating, plugin-config-merge; F4 agent-port-listener, agents-pod-ip-observe, agent-api-me, chart-agents-service; F5 migration-0003-hive), then the hive tasks, then deploy and the bench run.

## Time

Estimate: 175 agent-min | Critical path: 58 min | Expected wall at P=3.0: 1.9 h (k=2.0) | Actual: 0 min | Remaining estimate: 175 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
