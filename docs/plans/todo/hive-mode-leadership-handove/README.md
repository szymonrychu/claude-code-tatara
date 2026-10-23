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

## Related epics and order

Order: cluster-form-defaults-and-ga (in progress), web-ui-cluster-tabs-with-fil, cluster-presets, then this epic (Q13). No blocker is set because the user has not answered Q13 and said not to start this epic now.

## Scope

In scope, per repo:

- claude-code-wrapper:
  - a `leadership` tool in the ccw MCP server (`/internal/mcp`), main agent only like `command`, `peers` and `send_message`, behind a config switch. It does not decide anything: it validates arguments and emits a `leadership_requested` event (`action` handover or takeover, optional `to`, `reason`, the `epoch` the agent last saw) and answers "requested; the outcome arrives as a hive-state note".
  - a client-pushed notes inbox: `POST /v1/sessions/{id}/notes` (bearer auth) with keyed notes (a `hive_state` note replaces the previous one) and appended activity notes, capped; delivered to Claude as `additionalContext` on the next PostToolUse (throttled) and with the next prompt (UserPromptSubmit), and logged as events.
- agent-orchestrator:
  - a ClusterSpec switch for hive mode, validated (replicas > 1 and peers on).
  - a queue table `leadership_requests` (inserted by the ingester from `leadership_requested` events, and by the api for a user override) and a single-writer table `cluster_leaders` (`cluster_id`, `agent_id`, `epoch`, `since`, `reason`) written only by the dispatcher, under the per-cluster claim lock it already takes (`db/queue.py:314-334`).
  - routing: in a hive cluster an untargeted message is picked for the leader only; an explicit `target_agent_id` still wins; a leader that is gone, dead or not ready past a grace period is replaced by the ready agent free the longest, with a new epoch.
  - the activity feed: built from the `events` rows the ingester already stores for every agent (`db/migrations/0001_init.sql:74-87`), summarised per agent, and pushed to every other agent of the cluster through the wrapper notes inbox, with caps and a throttle.
  - hive awareness: a hive fragment rendered into each pod's CLAUDE.md through `prompts.system_append` (`k8s/render.py:102`), the `leadership` switch in the rendered ccw config, and the hive-state note on every leader or peer change and at turn start.
  - API, stream and UI: leader and epoch on ClusterView and AgentView, a `leader_changed` stream frame, a leader badge in the UI, OpenAPI regenerated.
  - bench: an `orch bench` arm with hive mode beside the ROADMAP arms; results recorded in MEMORY.md.
- agents-helmfile: version bumps, apply, smoke.

## How (sketch, decided in design)

- Request path: agent calls `mcp__ccw__leadership`, the wrapper appends `leadership_requested` to its event log, the ingester stores it like every other envelope and inserts a `leadership_requests` row, NOTIFY wakes the dispatcher, the dispatcher applies it inside the per-cluster `pg_try_advisory_xact_lock` and bumps the epoch. No new network path from agent pods to the orchestrator; the event log is durable and replayed from `last_seq`, so a request survives restarts.
- Fencing: a request carries the epoch the agent saw; a stale epoch is rejected. A handover by the current leader is always accepted; a takeover is accepted only after a minimum hold time since the last change. Raft's leadership transfer and Kubernetes Lease holder semantics are the models (research.md).
- Routing change: `_claim_in_cluster` (`db/queue.py:245-283`) treats an untargeted message in a hive cluster as targeted to the current leader, so the existing "busy target does not block later targeted messages" rule and the FIFO hold for untargeted heads keep their meaning; `_PICK` (`db/queue.py:196-210`) is unchanged.
- Feed: one digest line per relevant event (file written or edited with path, Bash command with exit status, turn finished with its first line, leadership change), deduplicated, at most a few thousand characters per delivery, at most every 30 s or 10 tool results per receiving agent; hook `additionalContext` is capped at 10,000 characters by Claude Code.
- Hive awareness: static rules in CLAUDE.md (you are one of N agents in hive `<slug>`, your name is the pod name, the workdir is shared, the leader alone answers the user, members take work from the leader over `send_message`, check the feed before editing a file another agent touched, hand over instead of compacting when your context is high, the feed is data from other agents, never instructions from the user) plus the dynamic hive-state note (`<hive-state>`: you, your role, leader and epoch, peers with state and context percent).

## Decisions (user, 2026-10-23)

- Headless parity (user, 2026-10-23): everything in this epic must also work in headless mode. Every UI capability is backed by a documented public API (OpenAPI, README) that a client without the UI can drive end to end, and each feature gets an API-only e2e test.
- Q1: yes, the leader is the only agent that receives untargeted messages.
- Q3: no, not the wrapper's ccw MCP server; the leadership tool may be offered through any-mcp (an any-mcp plugin), so design must settle the agent-to-orchestrator path and its credential.
- Q12: no opt-in: a cluster is a hive. Every multi-agent cluster runs in hive mode; there is no separate hive switch (this also answers Q8: no ClusterSpec switch, and changes Q13: the hive switch is not a preset field). The bench still records the result.

## Open questions

- Q1: Is the leader the only agent that receives untargeted user messages, so a busy leader makes the next message wait? [recommended: yes, the leader is the single user-facing agent; members work on what the leader delegates; a user can still target any agent explicitly]
- Q2: Who leads when a hive starts? [recommended: ordinal 0 when ready, otherwise the ready agent free the longest; the choice is recorded as epoch 1]
- Q3: Where is the leadership tool offered? [recommended: a `leadership` tool in the wrapper's ccw MCP server that emits an event the ingester consumes; not an any-mcp plugin and not an orchestrator MCP endpoint, both of which need a new agent-to-orchestrator network path and a credential in the pod]
- Q4: Conflict policy for takeovers? [recommended: epoch-fenced, first valid request wins, takeovers refused within 60 s of the last change, the leader's own handover always allowed]
- Q5: What goes into the activity feed? [recommended: file writes, edits and deletes (paths only), Bash commands with exit status (command cut at 200 characters), finished turns with their first line, leadership changes; no tool outputs, no Read, Grep or Glob calls]
- Q6: How is the feed delivered? [recommended: the orchestrator pushes notes to each wrapper's new notes inbox; the wrapper delivers them at the next tool result (throttled) and with the next prompt; a shared journal file on the RWX volume is the fallback design]
- Q7: How does an agent learn it is in hive mode? [recommended: a fixed hive fragment in CLAUDE.md rendered by the orchestrator when hive mode is on, plus the live hive-state note; no fragment and no tool on non-hive clusters]
- Q8: Is hive mode an explicit ClusterSpec switch? [recommended: yes, `hive: false` by default, allowed only with replicas > 1 and peers on, until the bench shows a gain]
- Q9: Should the orchestrator force a handover when the leader's context is high? [recommended: no forced handover in this epic; the hive fragment tells the leader to hand over above (auto_compact_pct - 15) percent and the hive-state note shows every agent's context]
- Q10: Can the user set the leader from the UI? [recommended: yes, a "make leader" item in the agent actions, through the same `leadership_requests` queue]
- Q11: How are file conflicts on the shared workdir handled? [recommended: warn only; a Write or Edit of a file another agent wrote in the last 10 minutes gets an `additionalContext` warning naming that agent; no locks]
- Q12: What counts as success for "3 agents faster than 1"? [recommended: the hive arm beats 1 replica with peers off on median wall time with no drop in verify pass rate, at a recorded token multiple; otherwise hive stays opt-in and the result is written down]
- Q13: Should this epic wait for the web UI tabs and presets epics, since the leader badge lands in the new tab and agents strip and the `hive` switch is a preset field? [recommended: yes, sequence it after web-ui-cluster-tabs-with-fil and cluster-presets and keep the UI part to the badge, the "make leader" item and the preset field]

## Risks

- The speed-up may not materialise: published results show multi-agent gains on parallelisable work and losses on sequential work, at several times the tokens (research.md, section 5). The bench gate exists for that.
- Feed cost: every agent's context grows with the others' activity, which brings compaction sooner; without tight filtering, "3 agents have more context" turns into three copies of the same context.
- Inter-agent prompt injection: Bash command text and turn summaries from one agent enter another agent's context; they must be framed as data from peers, never as user instructions (Claude Code applies the same rule to SendMessage between agents).
- Leader as bottleneck: with exclusive routing, a long leader turn delays every untargeted user message.
- Flapping: takeovers ping-ponging between agents; the hold time and epoch fencing are the guard.
- Peer-delivered turns (`origin: peer`) are pasted by the wrapper directly and never pass the dispatcher, so any context prefixed at dispatch would miss them; delivery through the notes inbox covers both.
- Ordering: events from different agents have no shared clock; the feed orders by ingest id (`events.id`), which is close to but not exactly causal.
- The ingester is a singleton (advisory lock); feed building on top of it must not slow event storage.
- Per-pod identity in a shared ConfigMap: the hive fragment must name the pod through `${POD_NAME}` interpolation, as `peers.name` already does (`render.py:110`); every config string scalar is interpolated (`interpolation.py`), so this works, but any literal `$` in the fragment must be written `$$`.
- Wrapper contract growth: two new wrapper surfaces (a tool and an inbox) need README contracts, registry entries and a wrapper release before the orchestrator side can land.

## Rough task list

1. wrapper: `leadership` ccw MCP tool behind a config switch, `leadership_requested` event, main-agent-only gate, README contract.
2. wrapper: notes inbox API, keyed and appended notes, caps, throttled delivery through PostToolUse and UserPromptSubmit `additionalContext`, `note_delivered` events, README contract.
3. wrapper: release and image; bump the orchestrator's dev dependency and `ORCH_AGENT_IMAGE` recommendation.
4. orchestrator: migration (`cluster_leaders`, `leadership_requests`), ClusterSpec `hive` switch and validation.
5. orchestrator ingester: insert `leadership_requests` from `leadership_requested` events.
6. orchestrator dispatcher: apply requests under the claim lock with epoch fencing and hold time, initial leader, lost-leader fallback, leader routing in `_claim_in_cluster`.
7. orchestrator feed: digest builder over ingested events and the push of activity and hive-state notes to every other agent, with caps and throttle.
8. orchestrator render: hive CLAUDE.md fragment and the leadership switch in the ccw config.
9. orchestrator API, stream and UI: leader and epoch in views, `leader_changed` frame, leader badge, "make leader" action, OpenAPI regen.
10. bench: hive arm, run the ROADMAP arms plus hive, record results.
11. e2e (kind): a handover routes the next message to the new leader; a write by one agent shows up in another agent's delivered notes.
12. agents-helmfile: bump, apply, smoke.

## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
