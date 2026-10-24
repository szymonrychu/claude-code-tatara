# hive mode leadership handover and shared activity feed design

## Summary

Every multi-agent cluster (cap `max_replicas > 1`) is a hive: one agent leads, recorded by the orchestrator with an epoch; untargeted user messages go to the leader; only the leader hands leadership away (or the user overrides); every agent gets a live hive-state note and a filtered activity feed through a new wrapper notes inbox; agents claim files with advisory locks. Agents call the orchestrator through one any-mcp plugin (`orchestrator`) over a new agent-only port with a per-cluster token bound to the pod IP. This epic also builds the foundation parts F1-F5 that cluster-scaling and agent-init-scripts build on, and it ships the releases (any-mcp v0.2.0, wrapper 0.2.0, orchestrator pins, helmfile bump, apply and smoke).

## Intent and why

The user wants 3 agents to work faster than 1 and to keep fresh context by handing the user-facing role over instead of compacting, without redoing or clobbering each other's work, and every agent must know it works in a hive (README `## Description`). The user approved the scope on 2026-10-24 and asked to run all of it at once.

## Goals

- Exactly one leader per hive, epoch-fenced, applied by the dispatcher under the per-cluster claim lock; first ready agent leads at start (Q2).
- Untargeted messages go to the leader; explicit targets win; a lost leader is replaced (Q1).
- Handover only, by the current leader, stale epoch rejected; the user can make any agent leader through UI and API (Q4, Q10).
- Hive awareness from the tool descriptions loaded at start and the hive-state note; the notes inbox only for hived agents; a static single-pod cluster gets no hive, peers or messaging tools (Q7).
- Feed: file writes and edits (paths), Bash commands with exit status (200 chars), finished turns (first line), leadership changes; nothing else (Q5), delivered as hook additionalContext (Q6).
- Advisory locks: claim, warn on a write to another agent's file, leader reassigns or discards (Q11).
- Headless parity: every UI capability has a documented public API and an API-only e2e test (X2).
- The speed-up is measured and recorded (Q12).
- Foundation parts F1-F5 land first so the other two epics can start.

## Non-goals

- No takeovers by agents (Q4), no forced handover (Q9), no hive switch in ClusterSpec (Q8, Q12).
- No consensus protocol between agents; no hard file locks.
- No CLAUDE.md hive fragment (Q7).
- The scale route and tool wiring (cluster-scaling) and init scripts (agent-init-scripts) are built in their epics; this epic ships the plugin tools for them and the extension points.

## Anti-goals

- Scaling or any runtime field rolling every pod (the ConfigMap hash must not depend on the live replica count).
- Opening the public `/api/v1` to agent pods.
- An alone (single-pod) cluster changing behaviour beyond the one upgrade roll.
- The feed flooding agent context (caps, own-line removal, throttle).

## Constraints

- Single writer per table; queue tables change rows only through status-guarded updates (AGENTS.md).
- The api has no auth; the agent surface gets its own port and token (foundation D1).
- ccw lists tools at boot only (`listChanged: False`), so tool visibility is fixed at render.
- `tests/test_readme_api.py` enforces README, openapi.json and schema.d.ts for every route, frame and table.
- The orchestrator pins any-mcp by tag and the wrapper by commit; a new rendered key needs the wrapper release first.

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

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| start-discovery (orchestrator) | ran: brief-orchestrator.md | claim lock reuse, queue-table pattern, checks Job shape, import pin | ingester-built feed |
| start-discovery (wrapper, any-mcp) | ran: brief-wrapper-anymcp.md | built-in plugin, notes inbox, webhook lock check, allow filter | OpenAPI-plugin variant (network I/O in load_tools) |
| architecture (foundation) | ran: foundation.md D1-D6 | second socket, seeds from cap, render-time gating | per-agent tokens, separate agent-api process |
| research-papers / prior art | ran: research.md sections 3, 6, 7 | Raft leadership transfer, fencing tokens, Kubernetes Leases, MetaGPT filtered pool | full traces, agent-team takeover |

## Research inputs

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

## Decision coverage

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

## Contracts

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

## Review focus

- `api/agent.py` `require_agent`: constant-time compare, one answer for every token failure, direct-peer IP only, gone agents never authenticate.
- The port gate: nothing but `/agent/v1` on the agent port; nothing of `/agent/v1` on the main port; the allowlist untouched on the main port.
- `leadership_pass` and `_claim_in_cluster`: one lock, status-guarded updates, epoch fencing, no target_gone for untargeted messages.
- The hash invariant: no live replica count anywhere in ConfigMap, Secret, Service or pod template.
- Notes framing: peer text is data, never user instructions; caps below 10,000 characters; no I/O in hooks.
- The token never on disk: literal `${ORCH_AGENT_TOKEN}` in the any-mcp config.

## Left to the builder

- Exact text of descriptions and notes within the stated content and caps.
- Internal module layout inside the named files; extra helper functions.
- Whether the note store hangs off the session manager or the router.
- Bucket size of context in the state hash (10% stated as default).

## Assumptions and unknowns

- Claude Code passes its env (the passthrough list) to stdio MCP children: confirmed by the e2e identity and notes tests in kind (probe), and the existing any-mcp install test already relies on PATH.
- The agent image has `python3` for `kubectl exec` probes: confirmed when kind-e2e-hive runs; fall back to the wrapper's own interpreter path.
- Harbor and GitHub releases are reachable for the tag pushes: the release tasks check and report.

## Open questions

none

## Irreversible operations in scope

- Push tag `v0.2.0` on any-mcp `main` (task any-mcp-release-v0-2-0); tags never move once pushed.
- Push tag `v0.2.0` on claude-code-wrapper `main` (task wrapper-release-0-2-0), which publishes images `:0.2.0` and `:latest`.
- `mise run apply` of agents-helmfile to the live namespace (task helmfile-apply-smoke); existing agent clusters roll their pods once (new env, rendered config).
- Migration 0003 on the live database (forward-only, additive: three tables and one nullable column).
