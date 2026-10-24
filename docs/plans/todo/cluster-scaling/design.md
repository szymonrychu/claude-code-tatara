# cluster scaling design

## Summary

Agents join and leave a running cluster without restarting the others, and the leader agent scales its cluster between 1 and the cap `max_replicas` set at init (ceiling 16) with the `orchestrator_scale` tool. A static cluster cannot be scaled; a static single pod is alone (no hive, peers or messaging tools). Users and headless callers get the same through `POST /api/v1/clusters/{id}/scale`, a scale control in the cluster view, and the cap and static switch in the preset form. A scale-down drains busy agents before their pods go and never removes the leader. The shared parts (spec fields, seeds from the cap, hash invariant, agent API and identity, plugin, leader tables) are built by hive-mode-leadership-handove (foundation F1-F5); this epic consumes them.

## Intent and why

User request 2026-10-24: "it must be possible to dynamically join/leave agent cluster" and "agents are offered tool, that allows to increase/decrease pods in the cluster (from 1 to N)". A hive grows for parallel work and shrinks back without restarts. Today a replica change rewrites the peers seed list inside the hashed ConfigMap and rolls every pod, and the spec is immutable (PATCH 405); scaling therefore needs an in-place, pod-template-neutral replica write.

## Goals

- `POST /api/v1/clusters/{id}/scale` and `POST /agent/v1/scale` change `spec.replicas` of an active cluster in place, within 1..`max_replicas`, with no generation bump and no restart of surviving pods (pod uids and config hash unchanged, e2e).
- Only the current leader may call the agent route (`not_leader` otherwise); a static cluster refuses (`static_cluster`); a scale that would remove the leader is refused (`leader_would_leave`).
- A scale-down removes the highest ordinals; a busy agent among them finishes its turn first, bounded by `ORCH_SCALE_DRAIN_SECONDS`.
- New agents join the peers membership and `/agent/v1/me` members; leaving agents drop out, the leader stays.
- The scale tool is listed only for scalable clusters; static single-pod agents are alone.
- The UI sets the cap and static switch per preset and scales a running cluster; every UI capability has a documented API and an API-only e2e test.
- The epic is released and deployed: deploy pin, `mise run apply`, `mise run smoke` with a scale step.

## Non-goals

- No new spec fields: `max_replicas`, `static` and the derived `hive`/`alone`/`scalable` are hive F3's.
- No membership code: the wrapper's gossip with seeds from the cap (hive F3) already joins and drops members; `hive_state` pushes are hive's.
- No choice of which agent leaves: StatefulSet removes the highest ordinals.
- No autoscaling and no scale command kind in the queue.
- No any-mcp or wrapper change or release: the `orchestrator_scale` tool ships in any-mcp v0.2.0 (hive F1).

## Anti-goals

- Any scale that rolls surviving pods (a rendered ConfigMap byte that depends on the live replica count).
- A second writer of `clusters` or a write of `cluster_leaders` or `agents` from the api.
- Leadership moving because of scaling.

## Constraints

- Single writer per table: `clusters` (spec) api only; `clusters.status` reconciler; `cluster_leaders` dispatcher; `agents` reconciler; `agent_status` ingester.
- Every route, frame and table is in README, `openapi.json` and `frontend/src/api/schema.d.ts` (`tests/test_readme_api.py`).
- Python backend, TypeScript frontend; TDD; targeted verify per task.
- Executes after hive-mode-leadership-handove's F1-F5 and its dispatcher leadership pass land on main (README blocker). Contracts consumed from that epic, by foundation name:
  - `ClusterSpec.max_replicas`, `static`, derived `hive`, `alone`, `scalable` (`spec.py`, F3).
  - Hash invariant `tests/test_render.py::test_runtime_fields_change_only_statefulset_replicas` and seeds `peers.static = ordinals 0..max_replicas-1` (F3).
  - Rendered `orchestrator` plugin entry with Config and per-cluster `allow` (`k8s/on_start.py`, F3); `claude.main_agent_only_tools` rendered (F3, wrapper F2).
  - `/agent/v1` router, `require_agent()`, agent port branch, `ORCH_AGENT_URL`/`ORCH_AGENT_TOKEN` pod env (F4); `GET /agent/v1/me` members.
  - Table `cluster_leaders` (F5) and the dispatcher's leadership pass with lost-leader fallback; `POST /api/v1/clusters/{id}/leader`.
  - `OrchestratorPlugin` tool `orchestrator_scale` (any-mcp v0.2.0, F1).
  - Writer rule "`spec.replicas` and `spec.init_scripts` are the only mutable fields; PATCH stays 405" (README `## API` Versioning, hive).
- Files shared with agent-init-scripts (`api/agent.py`, `api/clusters.py`, `db/clusters.py`, README, `openapi.json`, `schema.d.ts`, `clusterSpecForm.ts`, `PresetForm.tsx`, `k8s/on_start.py`): the epic that lands second rebases.

## Decisions

### D1: One guarded in-place replica writer
`db/clusters.set_replicas` in the api process locks the cluster row and refuses in a fixed order: `cluster_deleting`, `not_leader` (only with a caller agent), `static_cluster`, `out_of_range` (outside 1..`max_replicas`), `leader_would_leave` (leader ordinal >= target). It then sets `spec.replicas` with `jsonb_set`, no generation bump, NOTIFY `cluster_changed`; an unchanged value is a no-op. Alternatives: a separate runtime table, or a `scale` command applied by the reconciler (both rejected in foundation D4: duplicate truth, extra hop). Refusal order is my call: a non-leader learns nothing about the cluster's state. Serves S2, S3, Q4.

### D2: Two routes, one shape
`POST /api/v1/clusters/{id}/scale` (no leader check) and `POST /agent/v1/scale` (leader only, identity from `require_agent()`) both take `ScaleRequest {replicas}` and answer 202 `ScaleResult {cluster_id, replicas, previous_replicas, max_replicas}`. Codes: `not_leader` 403, `static_cluster` 409, `out_of_range` 422, `leader_would_leave` 409, `cluster_deleting` 409. The shared result shape instead of a ClusterView on the public route is my call (headless parity: one client contract for tool and API). A contract test drives the real any-mcp plugin tool against the route. Serves S2, X1, X2.

### D3: Scale-down drains busy agents, bounded
Agents above the target are draining: never `ready`, so never dispatched to, never given leadership and never bootstrapped. The reconciler applies StatefulSet replicas `max(target, 1 + highest busy draining ordinal)` (busy: `agent_status.state = busy`, or a `dispatching`/`verifying` message), so idle top agents go at once. After `ORCH_SCALE_DRAIN_SECONDS` (default 900, my call) the target applies regardless and an interrupted turn takes the existing verify path. `clusters.status.drain {target, since, waiting}` reports it. Rendering overrides only `spec.replicas`, so the hash invariant holds. Alternatives: refuse a scale-down while a victim is busy (stalls the leader's tool call), or cut the turn (loses work). Serves S1, Q4.

### D4: Scale tool listed only when scalable
The rendered `orchestrator` plugin `allow` includes the scale tool iff `spec.scalable` (hive and not static), decided from init-time fields only, so scaling never changes the rendered config. A scalable cluster at 1 pod lists it; static and alone clusters never do. Serves S3, Q7, X1.

### D5: UI for cap, static and replicas, all on the public API
The preset form gets "Max agents" and "Static (no scaling)" (static locks the cap to replicas); the chat header gets a scale control (count of cap, add and remove, disabled at bounds and when static, hidden when alone, API errors inline); the agents strip marks leaving agents and those finishing a turn. Placement in the chat header rather than the top-bar tab is my call (the tab is per cluster in a list; the header is the selected cluster). README `### Scaling` documents cap, static, replicas and drain for API callers. Serves S2, S3, X2.

### D6: Release is the main build, deployed and smoked
The orchestrator release is the main build of this epic's merge (chart `0.1.0-main.<sha7>`, image `<sha7>`); agents-helmfile pins it, runs `mise run diff`, `mise run apply` and `mise run smoke`, and the smoke gains a scale step (1 to 2 to 1, pod-0 uid unchanged). No any-mcp or wrapper release: their changes ship with the hive epic. Serves REL, S1.

### D7: Scaling never moves leadership
A joining agent never leads (the first ready agent leads at hive start, Q2); a scale-down that would remove the leader is refused for agents and users alike (`leader_would_leave`; make another agent leader first through the hive route), consistent with handover-only (Q4). A leader lost for other reasons is replaced by the hive dispatcher's fallback. Alternative: auto-handover on scale-down (a takeover by the system, excluded by Q4). Serves Q2, Q4.

### D8: Join and leave reuse hive membership; this epic proves it
Membership stays the wrapper gossip seeded with all cap ordinals (hive F3) and `hive_state` pushes on agents join and leave (hive). This epic adds no membership code and proves it on kind: after scale up and down the surviving pods keep their uids and the config hash, and `/agent/v1/me` members follow. Serves S1.

### D9: S1 dynamic join and leave
Agents dynamically join and leave a running cluster (peers, hive state, leader fallback update without restarting the others). (user decision)

### D10: S2 cap at init, leader scales 1..N
The replica cap N is set at cluster init (ClusterSpec field, ceiling 16); the leader can scale between 1 and N with a tool. (user decision)

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| start-discovery (orchestrator) | ran: scratchpad brief-orchestrator.md | in-place apply patches only replicas (`reconciler/loop.py:203-236`); `upsert_agent` revives ordinals (`db/agents.py:71-79`); e2e pod-uid comparison (`tests/e2e/test_e2e_kind.py:726`) | live count outside spec (foundation D4) |
| start-discovery (wrapper, any-mcp) | ran: scratchpad brief-wrapper-anymcp.md | gossip join/leave needs no wrapper change (`peer_membership.py:131-166`); `allow` filters tools (`registry.py:247`) | tool reload on scale (`listChanged: False`) |
| architecture (foundation) | ran: scratchpad foundation.md D1-D6 | in-place `spec.replicas`, agent API identity, seeds from cap | per-agent tokens, wrapper-event request path |
| research-code-external | skipped: uvicorn multi-socket already verified in foundation D1 | none | none |
| research-papers | skipped: no algorithmic question | none | none |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| brief-orchestrator Plan inputs: cluster-scaling | spec cap field and static switch | do-not-build: hive F3; form fields in cap-static-preset-form |
| brief-orchestrator Plan inputs: cluster-scaling | live count outside the immutable spec | rejected: foundation D4 keeps it in `spec.replicas`; scale-replicas-repo |
| brief-orchestrator Plan inputs: cluster-scaling | seeds not from replicas, hash-constant test | do-not-build: hive F3; kept green by scale-tool-allow, scale-down-drain |
| brief-orchestrator Plan inputs: cluster-scaling | reconciler gone agents and leader fallback on leave | scale-down-drain; fallback do-not-build (hive dispatcher) |
| brief-orchestrator Plan inputs: cluster-scaling | leader-only scale tool, public route, UI control, e2e pod uids | agent-scale-route, public-scale-route, scale-ui-control, kind-e2e-scaling |
| brief-orchestrator Plan inputs: cluster-scaling | scale-down victim policy | scale-down-drain (D3), scale-replicas-repo (D7) |
| brief-wrapper-anymcp Plan inputs: cluster-scaling | no wrapper change for join/leave | do-not-build; proven by kind-e2e-scaling |
| brief-wrapper-anymcp Plan inputs: cluster-scaling | scale tool omitted when scaling is off | scale-tool-allow |
| brief-wrapper-anymcp Plan inputs: cluster-scaling | risk: busy agent removed mid-turn | scale-down-drain |
| brief-wrapper-anymcp Plan inputs: cluster-scaling | risk: per-pod any-mcp install latency on new pods | rejected: accepted cost, bounded by `ORCH_ON_START_TIMEOUT_SECONDS` |
| agents-helmfile smoke and deploy precedent | deploy pin by main build, apply, smoke | smoke-scale-check, deploy-pin-scaling |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 One guarded in-place replica writer | scale-replicas-repo, public-scale-route, agent-scale-route |
| D2 Two routes, one shape | public-scale-route, agent-scale-route |
| D3 Scale-down drains busy agents, bounded | scale-down-drain, agents-strip-leaving-mark |
| D4 Scale tool listed only when scalable | scale-tool-allow |
| D5 UI for cap, static and replicas | cap-static-preset-form, scale-ui-control, agents-strip-leaving-mark, public-scale-route |
| D6 Release is the main build, deployed and smoked | smoke-scale-check, deploy-pin-scaling |
| D7 Scaling never moves leadership | scale-replicas-repo, kind-e2e-scaling |
| D8 Join and leave reuse hive membership | kind-e2e-scaling |
| D9 S1 dynamic join and leave | scale-down-drain, agents-strip-leaving-mark, kind-e2e-scaling, smoke-scale-check, deploy-pin-scaling |
| D10 S2 cap at init, leader scales 1..N | scale-replicas-repo, public-scale-route, agent-scale-route, scale-ui-control, cap-static-preset-form, kind-e2e-scaling |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `scale-replicas-write` | scale-replicas-repo | public-scale-route, agent-scale-route | `code/agent-orchestrator/src/agent_orchestrator/db/clusters.py` |
| `scale-schemas` | public-scale-route | agent-scale-route | `code/agent-orchestrator/src/agent_orchestrator/api/schemas.py` |
| `orch-cluster-scale-api` | public-scale-route | scale-ui-control, kind-e2e-scaling, smoke-scale-check | `code/agent-orchestrator/README.md` |
| `orch-agent-scale-api` | agent-scale-route | kind-e2e-scaling | `code/agent-orchestrator/README.md` |
| `scale-drain-status` | scale-down-drain | agents-strip-leaving-mark, kind-e2e-scaling | `code/agent-orchestrator/src/agent_orchestrator/reconciler/loop.py` |

## Review focus

- `set_replicas`: row lock, refusal order, no generation bump, no write outside `spec.replicas`, NOTIFY in the same transaction.
- Agent route: identity strictly from `require_agent()`; leader check against `cluster_leaders`; served only on the agent port.
- Drain: effective replicas never below the target, never above the previous count; deadline from `status.drain.since`; no ConfigMap change (hash invariant).
- e2e: uids and config hash compared across scale up and down; teardown of every created cluster.

## Left to the builder

- Exact UI copy beyond the strings named in the tasks, and the visual layout of the scale control within the chat header.
- How the plugin contract test reaches the app (ASGI transport or an ephemeral uvicorn port).
- Whether the e2e drain test is feasible with the scripted fake claude.

## Assumptions and unknowns

- Hive F3 exposes `spec.scalable`/`hive`/`alone` as properties and names tools in `allow` by plugin tool name; confirmed by reading F3's merged code when this epic starts (probe: `grep -n scalable src/agent_orchestrator/spec.py`).
- The hive dispatcher refuses a handover to an agent that is not `ready`, so a draining agent cannot receive leadership after a scale-down; confirmed by the hive leadership-pass tests (probe: read them on main before scale-replicas-repo starts); if absent, scale-replicas-repo's tests surface it.
- F4 includes `/agent/v1` routes in `openapi.json` or not; agent-scale-route follows whichever convention F4 set.

## Open questions

none

## Irreversible operations in scope

- `mise run apply` of the agents namespace (deploy-pin-scaling): covered by the user's scope approval ("releases/bumps/helmfile apply-smoke as tasks"); reversible by re-pinning the previous chart and image and applying again.
- Publishing the main-build chart and image happens on the orchestrator merge to main (immutable versions); covered by the same approval.
