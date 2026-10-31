---
title: hive mode leadership handover and shared activity feed
repos: [any-mcp, claude-code-wrapper, agent-orchestrator, agents-helmfile]
created: 2026-10-23
owner: Szymon Richert
rung: 1
---

# hive mode leadership handover and shared activity feed

## What and why

What: Every multi-agent cluster is a hive: one leader at a time, recorded by the orchestrator with an epoch; the leader hands leadership over with a tool (or the user makes any agent leader); untargeted messages go to the leader; every agent sees the others' file writes, commands and finished turns, claims files with advisory locks, and knows from its tools that it works in a hive
How: One shared "orchestrator" any-mcp plugin calls a new agent-only port of the orchestrator API with a per-cluster token bound to the pod IP; the dispatcher applies epoch-fenced leadership requests under its per-cluster claim lock and routes to the leader; a feed and hive-state note built from ingested events reach each agent through a new wrapper notes inbox as hook additionalContext; tool visibility is fixed at render from the cluster's replica cap and static switch
Why: Let several agents split work and keep fresh context by handing the user-facing role over instead of compacting, without redoing or clobbering each other's work; whether it is faster is measured with orch bench

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

## Scope ladder

### Rung 1: agreed scope (migrated)

- 1.1: Exactly one leader per hive, recorded by the orchestrator with an epoch; the first ready agent leads when a hive starts (Q2).
- 1.2: Agents see an orchestrator any-mcp plugin (X1, Q3) whose tools hint the hive mode on load (Q7): `me`, `leadership_handover`, and advisory `lock_*` tools.
- 1.3: Only the current leader hands leadership away, to a named or any agent; a stale epoch is rejected; no takeovers (Q4). The user can make any agent leader from the UI and the API (Q10).
- 1.4: Untargeted messages go to the leader only; an explicit target still wins; a lost leader is replaced (Q1).
- 1.5: Every hived agent gets the feed (file writes, edits and deletes as paths, Bash commands with exit status cut at 200 chars, finished turns with their first line, leadership changes; Q5) and a hive-state note, through the wrapper notes inbox as hook additionalContext at the next tool result (throttled) and the next prompt (Q6).
- 1.6: Advisory file locks: claim, a warning on writing another agent's file, the leader reassigns or discards any lock (Q11).
- 1.7: Context is visible per agent; handing over above `auto_compact_pct - 15` is advised, never forced (Q9).
- 1.8: The UI and API show the leader; the stream carries leader changes; every UI capability has a documented public API and an API-only e2e test (X2).
- 1.9: The speed-up claim is measured with an `orch bench` hive arm and recorded (Q12).
- 1.10: Releases: any-mcp v0.2.0, claude-code-wrapper 0.2.0, orchestrator pins, agents-helmfile bump, apply and smoke.

## Agreed scope

Rung 1, migrated from the epic format: the epic's goals were its agreed scope.

## Non-goals

- No takeovers by agents and no forced handover (Q4, Q9).
- No hive switch in ClusterSpec (Q8, Q12); no CLAUDE.md hive fragment (Q7).
- No consensus protocol between agents: the orchestrator is the single authority for leadership.
- No hard file locks: locks are advisory.
- No Claude Code agent teams inside the pods (native SendMessage stays disabled with peers on).
- The scale route (cluster-scaling) and init scripts (agent-init-scripts) are built in their epics; this epic ships their plugin tools and extension points.

## Design

Migrated from the epic format; the design sections without a plan.md heading are under Migrated notes.

## Decisions

### D1: Agent-to-orchestrator path is a second port of orch api
A second listening socket of `orch api` (`ORCH_AGENT_PORT`, 8001) serves only `/agent/v1/*`, behind `HMAC(master_key, "agent:<cluster_id>")` mounted from the cluster Secret, plus caller-IP binding to `agents.pod_ip`; the matching agents row is the caller's identity. Alternatives rejected: per-agent tokens (one Secret per StatefulSet), wrapper events and ingester (async, no answers), a separate agent-api process (second writer), same port with an exempt prefix (rides the ingress). Source: foundation.md D1. Serves F.

### D2: Tool visibility fixed at render; main-agent-only tools in the wrapper gate
The plugin entry's `allow` list comes from immutable spec fields only (`hive`, later `scalable`); descriptions come from plugin Config. Subagents are denied `mcp__any-mcp__orchestrator_*` through the new wrapper key `claude.main_agent_only_tools`. Rejected: reloading tools on scale, accepting subagent calls. Source: foundation.md D2. Serves F.

### D3: Membership stays wrapper gossip; seeds from the cap; hive state pushed
`peers.static` lists ordinals `0..max_replicas-1`; the orchestrator pushes the keyed `hive_state` note on leader and membership change. Source: foundation.md D3. Serves F, H.

### D4: spec.replicas and spec.init_scripts are the only in-place spec fields
This epic owns the rule and the hash-invariant test; cluster-scaling and agent-init-scripts write the fields. Source: foundation.md D4. Serves F.

### D5: Spec vocabulary max_replicas, static and derived hive
`max_replicas` defaults to `replicas`, `static` requires `max_replicas == replicas`, `hive = max_replicas > 1`, `alone = not hive`, `scalable = hive and not static`; the preset and cluster forms gain both fields (my call: this epic owns the fields, so it owns their form inputs). Serves F.

### D6: Foundation first, releases are tasks
F1 any-mcp plugin and v0.2.0, F2 wrapper notes inbox, gate and 0.2.0, F3 spec, render and pins, F4 agent API, F5 migration 0003 land first; tags, pins, helmfile bump, apply and smoke are explicit tasks. Source: foundation.md D6. Serves F, R.

### D7: The dispatcher is the single leadership authority
`leadership_requests` is a queue (api inserts from the agent route and the public make-leader route; dispatcher decides); `cluster_leaders` is written only by the dispatcher inside the per-cluster claim advisory lock, so a change and a claim never interleave. Rejected: ingester-inserted requests from wrapper events (async, superseded by X1). Serves H.

### D8: Leader-only routing in _claim_in_cluster
An untargeted message in a cluster with a leader row behaves as targeted to the leader; explicit targets win; `_PICK` unchanged. Serves H.

### D9: Feed and hive state built in the dispatcher, delivered through the notes inbox
Digest from stored `events`, cursor in `cluster_leaders`, pushed by the dispatcher (not the singleton ingester, so event storage is never slowed); the wrapper delivers at the next prompt and throttled tool results. Rejected: digest prefixed at dispatch (misses peer-delivered turns), shared journal file (orchestrator has no mount). Serves H.

### D10: Advisory locks written by the api, checked through a rendered wrapper webhook
`file_locks` (api writer) with claim, release, list, leader reassign and discard; a blocking `onAgentToolCall` webhook with `on_error: allow` and a 2 s timeout returns `additional_context` naming the holder, never denies. No wrapper code needed. Serves H.

### D11: Leader in views, a leader_changed frame and the agents strip
ClusterView and AgentView carry leader, epoch, cap, static and context; `/stream` emits `leader_changed`; the UI shows a badge and a "Make leader" action. Serves H.

### D12: Bench arm and a recorded run
A `hive3` arm and a recorded run after deploy; no switch follows either way. Serves H.

### D13: API-only kind e2e drives agent routes through kubectl exec
The fake claude cannot call MCP tools, so agent calls run from inside agent pods with the pod's own token and URL. Serves H.

### D14: Grace and push interval are module constants
`LEADER_GRACE_SECONDS = 30`, `PUSH_INTERVAL_SECONDS = 10` (my call; keeps settings churn and file overlap out). Serves H.

### D15: The plugin is built into any-mcp
`any_mcp.orchestrator:OrchestratorPlugin` ships in any-mcp (precedent `openapi.py`), so the onStart install line stays one pip install. Rejected: a separate package with an extra pip line. Source: brief-wrapper-anymcp `### Answers for the "orchestrator" plugin`. Serves F.

### D16: Shared orchestrator plugin with a per-cluster credential
One shared orchestrator any-mcp plugin carries every agent-to-orchestrator tool (leadership, file locks, scale, init-script edit) with a per-cluster scoped credential in the pod; built once here, the other epics add tools to it. (user decision)

### D17: Headless parity
Headless parity: every UI capability has a documented public API and an API-only e2e test. (user decision)

### D18: Leader-only routing
The leader is the only agent that receives untargeted messages; an explicit target still wins. (user decision)

### D19: First ready agent leads
The first ready agent leads when a hive starts, at epoch 1. (user decision)

### D20: Tools through any-mcp, not ccw
Leadership and the other agent tools are offered through an any-mcp plugin, not the wrapper's ccw MCP server. (user decision)

### D21: Handover only, epoch fenced
Handover only, no takeovers by agents: only the current leader gives leadership away, to a named or any agent; a stale epoch is rejected. (user decision)

### D22: Feed contents
Feed: file writes, edits and deletes (paths only), Bash commands with exit status cut at 200 chars, finished turns with their first line, leadership changes; no tool outputs, no Read, Grep or Glob. (user decision)

### D23: Delivery through the notes inbox
The feed is delivered through the wrapper notes inbox as hook additionalContext at the next tool result (throttled) and the next prompt. (user decision)

### D24: Awareness from tool descriptions; alone clusters
Tools on load hint the hive mode (no CLAUDE.md fragment); the wrapper notes inbox is enabled only for hived agents; a static single-pod cluster gets no hive, peers or messaging tools: the agent is alone. (user decision)

### D25: No hive switch
No ClusterSpec hive switch. (user decision)

### D26: Advise, never force, handover
No forced handover; advise handing over above auto_compact_pct - 15 and keep every agent's context visible. (user decision)

### D27: User make leader
The user can make any agent leader from the UI and the API through the same leadership queue; a user request overrides handover-only. (user decision)

### D28: Advisory locks
Advisory file locks: agents claim files, a write to a file claimed by another agent is warned, the leader can reassign or discard any lock. (user decision)

### D29: Every multi-agent cluster is a hive
Every multi-agent cluster is a hive, no opt-in; the bench still records the result. (user decision)

### D30: Prerequisites done
Moot: the prerequisite epics are done; the leader UI lands in the existing agents strip. (user decision)

## Open questions

none

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| start-discovery (orchestrator) | ran: brief-orchestrator.md | claim lock reuse, queue-table pattern, checks Job shape, import pin | ingester-built feed |
| start-discovery (wrapper, any-mcp) | ran: brief-wrapper-anymcp.md | built-in plugin, notes inbox, webhook lock check, allow filter | OpenAPI-plugin variant (network I/O in load_tools) |
| architecture (foundation) | ran: foundation.md D1-D6 | second socket, seeds from cap, render-time gating | per-agent tokens, separate agent-api process |
| research-papers / prior art | ran: research.md sections 3, 6, 7 | Raft leadership transfer, fencing tokens, Kubernetes Leases, MetaGPT filtered pool | full traces, agent-team takeover |

### Research inputs

| Source | Entry | Lands in |
|---|---|---|
| brief-orchestrator `### Auth` | no agent path; tokens.py purposes; pod IP not stored | agent-port-listener, agent-token-env-render, agents-pod-ip-observe, agent-api-me |
| brief-orchestrator `### k8s rendering` | seeds from replicas put the count in the hash | render-hive-gating |
| brief-orchestrator `### Dispatcher and queue` | per-cluster advisory lock; `_claim_in_cluster` | dispatcher-leadership-pass, leader-routing |
| brief-orchestrator `### API routers and stream frames` | README/openapi/schema drift tests; import pin | every API task, agent-api-me |
| brief-orchestrator risk (6) | `spec.any_mcp_config` replaces the default wholesale | plugin-config-merge |
| brief-wrapper-anymcp `### Hooks and additionalContext` | UserPromptSubmit returns allow; webhook headers | wrapper-notes-delivery, render-hive-gating |
| brief-wrapper-anymcp `### ccw MCP server and gating` | gate is prefix-hardcoded | main-agent-only-tools |
| brief-wrapper-anymcp `### Release and pinning` | test_release.py, test_images.py, helmfile equality | any-mcp-release-v0-2-0, wrapper-release-0-2-0, orch-pin-bumps, helmfile-deploy-pin |
| research.md section 7 | feed cost model: paths and exit codes only, caps | hive-feed-digest |
| research.md section 3 | fencing and Raft transfer | dispatcher-leadership-pass |

## Irreversible operations

- Push tag `v0.2.0` on any-mcp `main` (task any-mcp-release-v0-2-0); tags never move once pushed.
- Push tag `v0.2.0` on claude-code-wrapper `main` (task wrapper-release-0-2-0), which publishes images `:0.2.0` and `:latest`.
- `mise run apply` of agents-helmfile to the live namespace (task helmfile-apply-smoke); existing agent clusters roll their pods once (new env, rendered config).
- Migration 0003 on the live database (forward-only, additive: three tables and one nullable column).

## Migrated notes

### README.md: Related epics and order

The earlier prerequisites (cluster-form-defaults-and-ga, web-ui-cluster-tabs-with-fil, cluster-presets) are done, so Q13 is moot. This epic runs first; cluster-scaling and agent-init-scripts are blocked by it and wait on its foundation tasks (design.md D6, `docs/plans/contracts.json`). workspace-ui-fixes shares the frontend but no files with this epic's tasks.

### README.md: Scope

- any-mcp: built-in `OrchestratorPlugin` with the full tool surface for all three epics; release v0.2.0.
- claude-code-wrapper: notes inbox (`POST /v1/sessions/{id}/notes`, keyed and appended notes, throttled delivery as additionalContext, events), `claude.main_agent_only_tools`; release 0.2.0.
- agent-orchestrator: ClusterSpec `max_replicas` and `static` (and their form inputs); migration 0003; agent port, token, pod-IP identity and `/agent/v1/me`; render gating (seeds from the cap, peers and notes only for hives, main-agent-only tools, lock-check webhook, plugin entry); leadership requests, dispatcher leadership pass and leader routing; advisory locks; feed and hive-state push; views, stream frame and UI; bench arm; kind e2e; pins; chart agents Service.
- agents-helmfile: version bumps, apply, smoke.

### README.md: Decisions (user)

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

### README.md: Open questions

none

### README.md: Risks

- The speed-up may not materialise (research.md section 7); the bench run records the result.
- Feed cost: tight filtering, own-line removal, caps and throttle keep context growth bounded.
- Inter-agent prompt injection: notes are framed as data from peers, never user instructions.
- Leader as bottleneck: a long leader turn delays untargeted messages; explicit targets still dispatch.
- Opening an agent path to the orchestrator: a separate port, a per-cluster token and pod-IP binding; the public API stays closed to pods.
- One pod roll per existing cluster on upgrade (new env and rendered config).
- The subagent gate (`main_agent_only_tools`) is best-effort, not a security boundary: subagents share the pod, and Bash can read `ORCH_AGENT_TOKEN`.
- Election and failover are poll-driven (`dispatch_poll_seconds`): the first ready agent is the lowest-ordinal ready agent at the first pass that sees one, within the poll window.

### README.md: Rough task list

Task files under `tasks/`; foundation first (F1 orchestrator-plugin, any-mcp-release-v0-2-0; F2 main-agent-only-tools, wrapper-notes-inbox, wrapper-notes-delivery, wrapper-release-0-2-0; F3 spec-cap-static, agent-token-env-render, orch-pin-bumps, render-hive-gating, plugin-config-merge; F4 agent-port-listener, agents-pod-ip-observe, agent-api-me, chart-agents-service; F5 migration-0003-hive), then the hive tasks, then deploy and the bench run.

### README.md: Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-25)

Hand-orchestrated run (user asked to continue without the workflow), 2026-10-24 to 2026-10-25.
Every task: one implementer and one sonnet reviewer, at most two fix rounds, landed via worktree-merge.
Scope audit (sonnet) on agent-orchestrator 50324ee plus any-mcp v0.2.0 and wrapper 0.2.0: no gaps; the three post-merge tasks were then delivered and reviewed (PASS).
PRs merged with green CI: any-mcp #2, claude-code-wrapper #3, agent-orchestrator #8 (kind e2e green) and #9, agents-helmfile #11, #12, #13.
Live: release revision applied with chart 0.1.0-main.a5b5a75, wrapper :0.2.0 (sha7 tags are pruned in Harbor), any-mcp v0.2.0; smoke OK including a 200 from /agent/v1/me in an agent pod and a leader in a 2-replica hive.
User request during the run: the LAN-only ingress allowlist was removed (agents-helmfile #12); the node-IP denylist stays.

### design.md: Summary

Every multi-agent cluster (cap `max_replicas > 1`) is a hive: one agent leads, recorded by the orchestrator with an epoch; untargeted user messages go to the leader; only the leader hands leadership away (or the user overrides); every agent gets a live hive-state note and a filtered activity feed through a new wrapper notes inbox; agents claim files with advisory locks. Agents call the orchestrator through one any-mcp plugin (`orchestrator`) over a new agent-only port with a per-cluster token bound to the pod IP. This epic also builds the foundation parts F1-F5 that cluster-scaling and agent-init-scripts build on, and it ships the releases (any-mcp v0.2.0, wrapper 0.2.0, orchestrator pins, helmfile bump, apply and smoke).

### design.md: Intent and why

The user wants 3 agents to work faster than 1 and to keep fresh context by handing the user-facing role over instead of compacting, without redoing or clobbering each other's work, and every agent must know it works in a hive (README `## Description`). The user approved the scope on 2026-10-24 and asked to run all of it at once.

### design.md: Goals

- Exactly one leader per hive, epoch-fenced, applied by the dispatcher under the per-cluster claim lock; first ready agent leads at start (Q2).
- Untargeted messages go to the leader; explicit targets win; a lost leader is replaced (Q1).
- Handover only, by the current leader, stale epoch rejected; the user can make any agent leader through UI and API (Q4, Q10).
- Hive awareness from the tool descriptions loaded at start and the hive-state note; the notes inbox only for hived agents; a static single-pod cluster gets no hive, peers or messaging tools (Q7).
- Feed: file writes and edits (paths), Bash commands with exit status (200 chars), finished turns (first line), leadership changes; nothing else (Q5), delivered as hook additionalContext (Q6).
- Advisory locks: claim, warn on a write to another agent's file, leader reassigns or discards (Q11).
- Headless parity: every UI capability has a documented public API and an API-only e2e test (X2).
- The speed-up is measured and recorded (Q12).
- Foundation parts F1-F5 land first so the other two epics can start.

### design.md: Non-goals

- No takeovers by agents (Q4), no forced handover (Q9), no hive switch in ClusterSpec (Q8, Q12).
- No consensus protocol between agents; no hard file locks.
- No CLAUDE.md hive fragment (Q7).
- The scale route and tool wiring (cluster-scaling) and init scripts (agent-init-scripts) are built in their epics; this epic ships the plugin tools for them and the extension points.

### design.md: Anti-goals

- Scaling or any runtime field rolling every pod (the ConfigMap hash must not depend on the live replica count).
- Opening the public `/api/v1` to agent pods.
- An alone (single-pod) cluster changing behaviour beyond the one upgrade roll.
- The feed flooding agent context (caps, own-line removal, throttle).

### design.md: Constraints

- Single writer per table; queue tables change rows only through status-guarded updates (AGENTS.md).
- The api has no auth; the agent surface gets its own port and token (foundation D1).
- ccw lists tools at boot only (`listChanged: False`), so tool visibility is fixed at render.
- `tests/test_readme_api.py` enforces README, openapi.json and schema.d.ts for every route, frame and table.
- The orchestrator pins any-mcp by tag and the wrapper by commit; a new rendered key needs the wrapper release first.

### design.md: Risks

- Subagent gate is not a security boundary (interrogate verdict 2026-10-24 item 8; wrapper README trust model): the agent token is readable from Bash in the pod; the gate only stops accidental subagent calls.
- Election and failover latency is bounded by the dispatch poll interval, not instantaneous (interrogate verdict 2026-10-24 item 9).
- Peer text in notes and locks/check context is escaped and framed as data; an unescaped path would let a peer forge a block.

### design.md: Decision coverage

| Decision | Tasks |
|---|---|
| D1 Agent-to-orchestrator path | agent-port-listener, agent-api-me, agent-token-env-render, agents-pod-ip-observe, chart-agents-service |
| D2 Tool visibility and main-agent gate | main-agent-only-tools, render-hive-gating, plugin-config-merge, orchestrator-plugin |
| D3 Seeds from the cap and hive state | render-hive-gating, hive-state-push-loop |
| D4 In-place spec fields rule | hive-docs-memory, render-hive-gating |
| D5 Spec vocabulary | spec-cap-static, spec-form-cap-static |
| D6 Foundation first, releases are tasks | any-mcp-release-v0-2-0, wrapper-release-0-2-0, orch-pin-bumps, helmfile-deploy-pin, helmfile-apply-smoke, migration-0003-hive |
| D7 Dispatcher leadership authority | leadership-requests-api, dispatcher-leadership-pass, migration-0003-hive |
| D8 Leader-only routing | leader-routing |
| D9 Feed and hive state | hive-feed-digest, hive-state-push-loop, wrapper-notes-inbox, wrapper-notes-delivery |
| D10 Advisory locks | file-locks-api, render-hive-gating, migration-0003-hive |
| D11 Views, frame, UI | views-leader-stream, ui-leader-badge |
| D12 Bench | bench-hive-arm, bench-run-record |
| D13 kind e2e | kind-e2e-hive |
| D14 Module constants | dispatcher-leadership-pass, hive-state-push-loop |
| D15 Plugin built into any-mcp | orchestrator-plugin |
| D16 Shared orchestrator plugin with a per-cluster credential | orchestrator-plugin, plugin-config-merge, agent-token-env-render, agent-api-me |
| D17 Headless parity | leadership-requests-api, views-leader-stream, ui-leader-badge, kind-e2e-hive |
| D18 Leader-only routing | leader-routing |
| D19 First ready agent leads | dispatcher-leadership-pass |
| D20 Tools through any-mcp, not ccw | orchestrator-plugin, agent-port-listener |
| D21 Handover only, epoch fenced | leadership-requests-api, dispatcher-leadership-pass |
| D22 Feed contents | hive-feed-digest |
| D23 Delivery through the notes inbox | wrapper-notes-inbox, wrapper-notes-delivery, hive-state-push-loop |
| D24 Awareness from tool descriptions; alone clusters | orchestrator-plugin, render-hive-gating, plugin-config-merge, wrapper-notes-inbox |
| D25 No hive switch | spec-cap-static |
| D26 Advise, never force, handover | orchestrator-plugin, hive-state-push-loop, views-leader-stream, ui-leader-badge |
| D27 User make leader | leadership-requests-api, dispatcher-leadership-pass, ui-leader-badge |
| D28 Advisory locks | file-locks-api, render-hive-gating, orchestrator-plugin |
| D29 Every multi-agent cluster is a hive | spec-cap-static, bench-hive-arm, bench-run-record |
| D30 Prerequisites done | ui-leader-badge |

### design.md: Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| any-mcp-orchestrator-plugin | orchestrator-plugin | any-mcp-release-v0-2-0, plugin-config-merge | any-mcp `src/any_mcp/orchestrator.py` |
| any-mcp-release-v0-2-0 | any-mcp-release-v0-2-0 | orch-pin-bumps | any-mcp `pyproject.toml`, tag v0.2.0 |
| wrapper-main-agent-only-tools | main-agent-only-tools | wrapper-release-0-2-0, render-hive-gating | wrapper `src/claude_code_wrapper/config.py` |
| wrapper-notes-inbox | wrapper-notes-inbox | wrapper-notes-delivery, wrapper-release-0-2-0, render-hive-gating | wrapper README `## Notes` |
| wrapper-release-0-2-0 | wrapper-release-0-2-0 | orch-pin-bumps | wrapper `pyproject.toml`, image `<sha7>` |
| orch-hive-tables | migration-0003-hive | agents-pod-ip-observe, agent-api-me, leadership-requests-api, dispatcher-leadership-pass, file-locks-api | `db/migrations/0003_hive.sql` |
| orch-spec-cap-static | spec-cap-static | agent-token-env-render, render-hive-gating, plugin-config-merge, spec-form-cap-static, bench-hive-arm | `src/agent_orchestrator/spec.py` |
| orch-agent-port | agent-port-listener | agent-token-env-render, agent-api-me | `cli.py`, `api/allowlist.py`, `settings.py` |
| orch-agent-env | agent-token-env-render | agent-api-me, render-hive-gating | `tokens.py`, `k8s/render.py` |
| orch-agent-api-auth | agent-api-me | leadership-requests-api, file-locks-api | `api/agent.py` `require_agent` |
| orch-agents-service | chart-agents-service | kind-e2e-hive, helmfile-deploy-pin | `chart/agent-orchestrator/templates/service-agents.yaml` |
| orch-hive-pins | orch-pin-bumps | render-hive-gating, plugin-config-merge, hive-state-push-loop | `pyproject.toml`, `settings.py` |
| orch-render-hash-invariant | render-hive-gating | none | `tests/test_render.py::test_runtime_fields_change_only_statefulset_replicas` |
| orch-peer-seeds-cap | render-hive-gating | none | `k8s/render.py` |
| orch-plugin-entry | plugin-config-merge | kind-e2e-hive | `k8s/on_start.py` `orchestrator_allow` |
| orch-leader-read | leadership-requests-api | dispatcher-leadership-pass, file-locks-api | `db/leadership.py` `current_leader` |
| orch-leadership-pass | dispatcher-leadership-pass | leader-routing, hive-state-push-loop, views-leader-stream | `db/leadership.py` `leadership_pass` |
| orch-feed-digest | hive-feed-digest | hive-state-push-loop | `dispatcher/feed.py` |
| orch-hive-state-note | hive-state-push-loop | kind-e2e-hive | `dispatcher/hive.py` |
| orch-leader-views | views-leader-stream | ui-leader-badge, bench-hive-arm | `api/schemas.py` |
| orch-spec-runtime-mutable | hive-docs-memory | none | README `## API` Versioning |

Cross-epic consumers (cluster-scaling, agent-init-scripts) are registered in `docs/plans/contracts.json` under the same part names.

### design.md: Review focus

- `api/agent.py` `require_agent`: constant-time compare, one answer for every token failure, direct-peer IP only, gone agents never authenticate.
- The port gate: nothing but `/agent/v1` on the agent port; nothing of `/agent/v1` on the main port; the allowlist untouched on the main port.
- `leadership_pass` and `_claim_in_cluster`: one lock, status-guarded updates, epoch fencing, no target_gone for untargeted messages.
- The hash invariant: no live replica count anywhere in ConfigMap, Secret, Service or pod template.
- Notes framing: peer text is data, never user instructions; caps below 10,000 characters; no I/O in hooks.
- The token never on disk: literal `${ORCH_AGENT_TOKEN}` in the any-mcp config.

### design.md: Left to the builder

- Exact text of descriptions and notes within the stated content and caps.
- Internal module layout inside the named files; extra helper functions.
- Whether the note store hangs off the session manager or the router.
- Bucket size of context in the state hash (10% stated as default).

### design.md: Assumptions and unknowns

- Claude Code passes its env (the passthrough list) to stdio MCP children: confirmed by the e2e identity and notes tests in kind (probe), and the existing any-mcp install test already relies on PATH.
- The agent image has `python3` for `kubectl exec` probes: confirmed when kind-e2e-hive runs; fall back to the wrapper's own interpreter path.
- Harbor and GitHub releases are reachable for the tag pushes: the release tasks check and report.

### design.md: Builder check (2026-10-24)

Answered by docs or code: tool names and routes (orchestrator-plugin task, foundation contract table); built-in plugin path precedent (`openapi.py`); no I/O at load (`registry.py:87-122`); tag push only from merged main; env passthrough to stdio children (e2e probe); scale and init tool shapes (contracts `orch-agent-scale-api`, `orch-agent-init-scripts-api`, now AC10).
Minor, sensible defaults: context bucket 10% in the state hash (my call); tool error text is `<code>: <message>` (my call); lock path normalisation relative to the workdir (my call); feed throttle values as in the wrapper-notes tasks (my call).
Theirs: none.

### approvals.json

- F: Foundation F1-F5 (foundation.md D1-D6) built in this epic first: the any-mcp orchestrator plugin, the wrapper notes inbox and main-agent gate, ClusterSpec max_replicas and static with render gating and pins, the agent API with its port, token and pod-IP identity, and migration 0003. [decisions: D1, D2, D3, D4, D5, D6, D15] [tasks: orchestrator-plugin, main-agent-only-tools, wrapper-notes-inbox, wrapper-notes-delivery, migration-0003-hive, spec-cap-static, spec-form-cap-static, agent-port-listener, agents-pod-ip-observe, agent-token-env-render, agent-api-me, chart-agents-service, render-hive-gating, plugin-config-merge, hive-docs-memory] [status: approved]
- H: Hive mode: dispatcher leadership authority with epoch fencing, leader-only routing, the activity feed and hive-state notes, advisory file locks, leader in views, stream and UI, the bench arm and API-only kind e2e. [decisions: D7, D8, D9, D10, D11, D12, D13, D14] [tasks: leadership-requests-api, dispatcher-leadership-pass, leader-routing, file-locks-api, hive-feed-digest, hive-state-push-loop, views-leader-stream, ui-leader-badge, bench-hive-arm, bench-run-record, kind-e2e-hive] [status: approved]
- R: Releases across repos are explicit tasks: any-mcp v0.2.0 tag, claude-code-wrapper 0.2.0 image and tag, the orchestrator pins, the agents-helmfile bump, apply and smoke. [decisions: D6] [tasks: any-mcp-release-v0-2-0, wrapper-release-0-2-0, orch-pin-bumps, helmfile-deploy-pin, helmfile-apply-smoke] [status: approved]
- X1: One shared orchestrator any-mcp plugin carries every agent-to-orchestrator tool (leadership, file locks, scale, init-script edit) with a per-cluster scoped credential in the pod; built once here, the other epics add tools to it. [decisions: D16] [tasks: orchestrator-plugin, plugin-config-merge, agent-token-env-render, agent-api-me] [status: approved]
- X2: Headless parity: every UI capability has a documented public API and an API-only e2e test. [decisions: D17] [tasks: leadership-requests-api, views-leader-stream, ui-leader-badge, kind-e2e-hive] [status: approved]
- Q1: The leader is the only agent that receives untargeted messages; an explicit target still wins. [decisions: D18] [tasks: leader-routing] [status: approved]
- Q2: The first ready agent leads when a hive starts, at epoch 1. [decisions: D19] [tasks: dispatcher-leadership-pass] [status: approved]
- Q3: Leadership and the other agent tools are offered through an any-mcp plugin, not the wrapper's ccw MCP server. [decisions: D20] [tasks: orchestrator-plugin, agent-port-listener] [status: approved]
- Q4: Handover only, no takeovers by agents: only the current leader gives leadership away, to a named or any agent; a stale epoch is rejected. [decisions: D21] [tasks: leadership-requests-api, dispatcher-leadership-pass] [status: approved]
- Q5: Feed: file writes, edits and deletes (paths only), Bash commands with exit status cut at 200 chars, finished turns with their first line, leadership changes; no tool outputs, no Read, Grep or Glob. [decisions: D22] [tasks: hive-feed-digest] [status: approved]
- Q6: The feed is delivered through the wrapper notes inbox as hook additionalContext at the next tool result (throttled) and the next prompt. [decisions: D23] [tasks: wrapper-notes-inbox, wrapper-notes-delivery, hive-state-push-loop] [status: approved]
- Q7: Tools on load hint the hive mode (no CLAUDE.md fragment); the wrapper notes inbox is enabled only for hived agents; a static single-pod cluster gets no hive, peers or messaging tools: the agent is alone. [decisions: D24] [tasks: orchestrator-plugin, render-hive-gating, plugin-config-merge, wrapper-notes-inbox] [status: approved]
- Q8: No ClusterSpec hive switch. [decisions: D25] [tasks: spec-cap-static] [status: approved]
- Q9: No forced handover; advise handing over above auto_compact_pct - 15 and keep every agent's context visible. [decisions: D26] [tasks: orchestrator-plugin, hive-state-push-loop, views-leader-stream, ui-leader-badge] [status: approved]
- Q10: The user can make any agent leader from the UI and the API through the same leadership queue; a user request overrides handover-only. [decisions: D27] [tasks: leadership-requests-api, dispatcher-leadership-pass, ui-leader-badge] [status: approved]
- Q11: Advisory file locks: agents claim files, a write to a file claimed by another agent is warned, the leader can reassign or discard any lock. [decisions: D28] [tasks: file-locks-api, render-hive-gating, orchestrator-plugin] [status: approved]
- Q12: Every multi-agent cluster is a hive, no opt-in; the bench still records the result. [decisions: D29] [tasks: spec-cap-static, bench-hive-arm, bench-run-record] [status: approved]
- Q13: Moot: the prerequisite epics are done; the leader UI lands in the existing agents strip. [decisions: D30] [tasks: ui-leader-badge] [status: approved]
