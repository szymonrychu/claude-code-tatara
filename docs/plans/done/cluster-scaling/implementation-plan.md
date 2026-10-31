# cluster scaling implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: scale down drain

- Status: done
- Files: `src/agent_orchestrator/reconciler/loop.py`, `src/agent_orchestrator/settings.py`, `README.md`, `MEMORY.md`, `tests/test_reconciler.py`
- Verify: `uv run --frozen pytest -q tests/test_reconciler.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: e91c1bba8febbc434c5c80f8f25c214068d62c8c

#### Requirement

Drain on scale-down so a busy agent finishes its turn before its pod goes (design D3; user S1, Q4; foundation D3, D4). In `src/agent_orchestrator/reconciler/loop.py` `_converge`: agents with `ordinal >= spec.replicas` that are not gone are draining. An agent is busy when its `agent_status.state` is `busy` or a `messages` row with its `agent_id` is `dispatching` or `verifying`. The StatefulSet is applied with replicas `max(spec.replicas, 1 + highest busy draining ordinal)`, so idle agents above the highest busy one go at once (StatefulSet removes from the top) and the rest go as they become idle. The drain deadline is the new setting `scale_drain_seconds` (`ORCH_SCALE_DRAIN_SECONDS`, default 900, > 0) counted from the first tick that saw the drain; after it the StatefulSet gets `spec.replicas` regardless and an interrupted turn takes the existing verify path. Render with `cluster.model_copy` overriding only `spec.replicas`, so only `StatefulSet.spec.replicas` differs from the target render. `clusters.status` gains `drain: {target, since, waiting: [ordinals]}` while draining and drops it when done; `status.replicas` and phase math keep using the target `spec.replicas`; the message adds `draining <n> agents`. Draining agents stay `ready = false` (the existing `_observe` rule), so the dispatcher, leader selection and session bootstrap never pick them. Raising replicas during a drain ends it with no pod restart. README: the setting in `## Configuration` and a drain paragraph in `### Reconcile loop`; MEMORY.md dated entry with the why (a removed pod mid-turn loses the turn; the bound keeps a stuck turn from pinning capacity).

#### Acceptance conditions

- AC1: a busy draining agent keeps its pod until idle, then the StatefulSet drops to the target [evidence: test:tests/test_reconciler.py::test_scale_down_keeps_busy_agent_until_idle]
- AC2: idle draining agents above the highest busy one are removed in the first tick [evidence: test:tests/test_reconciler.py::test_scale_down_removes_idle_agents_at_once]
- AC3: after ORCH_SCALE_DRAIN_SECONDS the StatefulSet gets spec.replicas even with a busy agent [evidence: test:tests/test_reconciler.py::test_scale_down_drain_deadline]
- AC4: raising replicas during a drain clears status.drain and deletes no pod [evidence: test:tests/test_reconciler.py::test_scale_up_cancels_drain]
- AC5: during a drain only StatefulSet.spec.replicas differs from the target render; ConfigMap, Secret, Service and pod template are identical [evidence: test:tests/test_reconciler.py::test_drain_changes_only_statefulset_replicas]
- AC6: status.drain carries target, since and waiting while draining and is absent afterwards [evidence: test:tests/test_reconciler.py::test_drain_status_reported]
- AC7: the existing scale-down gone marking stays green [evidence: test:tests/test_reconciler.py::test_scale_down_marks_gone]
- AC8: README documents ORCH_SCALE_DRAIN_SECONDS and the drain [evidence: command:grep -q "ORCH_SCALE_DRAIN_SECONDS" README.md]
- AC9: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/reconciler/loop.py`
- `src/agent_orchestrator/settings.py`
- `README.md`
- `MEMORY.md`
- `tests/test_reconciler.py`

#### Interfaces

- Builds `clusters.status.drain {target, since, waiting}` (part `scale-drain-status`, reconciler-written) and setting `Settings.scale_drain_seconds` / `ORCH_SCALE_DRAIN_SECONDS`.
- Reads `agent_status.state` (ingester-written) and `messages.status`/`agent_id` (dispatcher-written); writes only `clusters.status` and `agents` rows as today.
- Keeps the hive hash invariant: render input differs only in `spec.replicas`.

#### Expected outcome

After a scale-down an agent in the middle of a turn finishes it, then its pod goes; idle agents above it go at once; nothing waits longer than the drain bound.

#### Steps

- Red: add the six tests to `tests/test_reconciler.py` using the existing fake kube and `env` fixture (set `agent_status.state` and a `dispatching` message directly); run `uv run --frozen pytest -q tests/test_reconciler.py -k "drain or scale"`: they fail.
- Green: compute the effective replicas and status.drain in `_converge`; add the setting with its validator; README and MEMORY.md; run the verify command.

#### Notes

- `drain.since` lives in `status` so it survives a reconciler failover; compare with `now()` from the database or the loop clock consistently with existing status timestamps.
- `_observe` keeps using the target `spec.replicas` for readiness, so draining agents are never `ready`; do not change that rule.
- The hive dispatcher's lost-leader fallback and `hive_state` push react to the gone marking; nothing to add there.
- The unchanged-status test (`test_unchanged_status_is_not_rewritten`) must stay green: write `status.drain` only when it changes.

### S2: scale replicas repo

- Status: done
- Files: `src/agent_orchestrator/db/clusters.py`, `tests/test_clusters_repo.py`, `MEMORY.md`
- Verify: `uv run --frozen pytest -q tests/test_clusters_repo.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 8446f551f292d48a4b6e209713eae58529722462

#### Requirement

Add the one writer of the runtime replica count (design D1; user S2, S3, Q4; foundation D4). In `src/agent_orchestrator/db/clusters.py` add `ScaleRefused(Exception)` with a `code` attribute, a frozen `ScaleOutcome(cluster_id, replicas, previous_replicas, max_replicas)` and `async def set_replicas(conn, cluster_id, replicas, *, caller_agent_id: uuid.UUID | None = None) -> ScaleOutcome`. In one transaction: lock the cluster row (`SELECT ... FOR UPDATE`); a missing row raises the existing `ClusterNotFound`; then refuse in this order: `desired != 'active'` -> `cluster_deleting`; `caller_agent_id` given and not the `agent_id` of the cluster's `cluster_leaders` row (hive migration 0003, read only here) -> `not_leader`; `spec.static` -> `static_cluster`; `replicas` outside `1..spec.max_replicas` -> `out_of_range`; a current leader whose agent `ordinal >= replicas` -> `leader_would_leave`. An unchanged value returns the outcome with no UPDATE and no NOTIFY. Otherwise `UPDATE clusters SET spec = jsonb_set(spec, '{replicas}', to_jsonb(%s))` guarded by `desired = 'active'`, leaving `generation` and `observed_generation` unchanged and every other spec key byte-identical, then NOTIFY `cluster_changed` in the same transaction. The stored spec still loads as `ClusterSpec`. Add a dated MEMORY.md entry (2026-10-24): `spec.replicas` is scale-writable in place by the api only, no generation bump, refusal codes and why (the hash invariant keeps a replica change off the pod template; Q4 forbids removing the leader).

#### Acceptance conditions

- AC1: set_replicas writes spec.replicas, keeps generation, observed_generation and every other spec key, and notifies cluster_changed [evidence: test:tests/test_clusters_repo.py::test_set_replicas_updates_spec_without_generation_bump]
- AC2: deleting, static and out-of-range (0 and max_replicas + 1) requests raise ScaleRefused with cluster_deleting, static_cluster and out_of_range and write nothing [evidence: test:tests/test_clusters_repo.py::test_set_replicas_refusals]
- AC3: a caller that is not the leader gets not_leader, a scale that would remove the leader's ordinal gets leader_would_leave, and a cluster with no leader row scales freely [evidence: test:tests/test_clusters_repo.py::test_set_replicas_leader_rules]
- AC4: an unchanged value returns the outcome without UPDATE or NOTIFY [evidence: test:tests/test_clusters_repo.py::test_set_replicas_unchanged_is_noop]
- AC5: the writer exists in the clusters repo [evidence: symbol:src/agent_orchestrator/db/clusters.py::set_replicas]
- AC6: MEMORY.md records the in-place replica write and leader_would_leave [evidence: command:grep -q "leader_would_leave" MEMORY.md]
- AC7: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/db/clusters.py`
- `tests/test_clusters_repo.py`
- `MEMORY.md`

#### Interfaces

- Builds `src/agent_orchestrator/db/clusters.py::set_replicas`, `ScaleRefused` (codes `cluster_deleting`, `not_leader`, `static_cluster`, `out_of_range`, `leader_would_leave`), `ScaleOutcome` (part `scale-replicas-write`).
- Consumes from hive-mode-leadership-handove: `ClusterSpec.max_replicas`, `static` (F3, `spec.py`), table `cluster_leaders` (F5, `db/migrations/0003_hive.sql`, written by the dispatcher only; read here), writer rule "`spec.replicas` mutable in place, no generation bump" (README `## API` Versioning, written by hive).

#### Expected outcome

The api process can change `clusters.spec.replicas` of an active cluster under the leader and cap rules, and the reconciler picks it up through `cluster_changed`.

#### Steps

- Red: add the four tests to `tests/test_clusters_repo.py` (insert `cluster_leaders` and `agents` rows directly); run `uv run --frozen pytest -q tests/test_clusters_repo.py -k set_replicas`: they fail on the missing import.
- Green: implement `set_replicas`; rerun: passes. Add the MEMORY.md entry; run the verify command.

#### Notes

- `jsonb_set` keeps every other key; assert byte equality of the other spec keys by loading the row before and after.
- Lock order: the cluster row first (`FOR UPDATE`), then read `cluster_leaders` joined to `agents` for the leader ordinal; never write `cluster_leaders` or `agents` (single writer: dispatcher and reconciler).
- Reuse `_fetch`, `_notify` and `ClusterNotFound` in the same module.

### S3: scale tool allow

- Status: done
- Files: `src/agent_orchestrator/k8s/on_start.py`, `tests/test_render.py`
- Verify: `uv run --frozen pytest -q tests/test_render.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 69a3929c7b56c667ac316fb2ffda47fa62ae4b10

#### Requirement

Expose the scale tool only on scalable clusters (design D4; user S3, Q7, X1; foundation D2). In `src/agent_orchestrator/k8s/on_start.py`, where hive-mode-leadership-handove F3 renders the merged `orchestrator` any-mcp plugin entry and its `allow` list, include the scale tool (`scale`, as F3 names tools in `allow`) if and only if `spec.scalable` (hive and not static). Alone clusters (`max_replicas == 1`, so a static single pod) and static multi-pod clusters render no scale tool; a scalable cluster renders it at any current `replicas`, including 1. The rendered ConfigMap (and so the pod-template hash) must not depend on `spec.replicas`: the hive hash-invariant test stays green and a new test proves the allow list is identical for the same spec at replicas 1 and at max_replicas.

#### Acceptance conditions

- AC1: the scale tool is in the orchestrator entry's allow list only when the cluster is scalable, for alone, static multi-pod, scalable at 1 and scalable at max specs [evidence: test:tests/test_render.py::test_scale_tool_allowed_only_when_scalable]
- AC2: the allow list and on-start script are identical for one spec rendered at replicas 1 and at max_replicas [evidence: test:tests/test_render.py::test_scale_allow_independent_of_replicas]
- AC3: the hive hash invariant stays green [evidence: test:tests/test_render.py::test_runtime_fields_change_only_statefulset_replicas]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/k8s/on_start.py`
- `tests/test_render.py`

#### Interfaces

- Changes the `allow` list of the `orchestrator` plugin entry rendered in `src/agent_orchestrator/k8s/on_start.py` by hive F3 (foundation D2: init tools always, hive tools when `hive`, `scale` when `scalable`).
- Keeps `tests/test_render.py::test_runtime_fields_change_only_statefulset_replicas` (hive hash invariant) green.

#### Expected outcome

Agents of scalable clusters load `orchestrator_scale`; static and alone agents never see it, and scaling never changes the rendered config.

#### Steps

- Red: add the two tests to `tests/test_render.py`; run `uv run --frozen pytest -q tests/test_render.py -k scale`: the scalable case fails (no scale tool).
- Green: add the condition where F3 builds `allow`; run the verify command.

#### Notes

- Use the derived `spec.scalable` property from F3; do not read the live replica count anywhere in render.
- If F3 already renders `scale` under the same condition, this task only adds the two pinning tests and says so in the result.

### S4: public scale route

- Status: done
- Files: `src/agent_orchestrator/api/clusters.py`, `src/agent_orchestrator/api/schemas.py`, `README.md`, `openapi.json`, `frontend/src/api/schema.d.ts`, `tests/test_api_scale.py`
- Verify: `uv run --frozen pytest -q tests/test_api_scale.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 126947162cca4e6a9c5241d9b51dcf331a3878aa

#### Requirement

Add the public scale route for headless parity (design D2, D5; user S2, S3, X2; foundation D4). `POST /api/v1/clusters/{cluster_id}/scale` in `src/agent_orchestrator/api/clusters.py`, body `ScaleRequest {replicas: int}` (extra fields forbidden), answers 202 with `ScaleResult {cluster_id, replicas, previous_replicas, max_replicas}` (both models in `api/schemas.py`; the agent route reuses them). It calls `db.clusters.set_replicas` with no caller agent and maps `ScaleRefused`: `static_cluster` 409, `out_of_range` 422, `leader_would_leave` 409, `cluster_deleting` 409; unknown cluster 404 `not_found`; a malformed body 422 `invalid_request`. The route imports neither `k8s` nor `wrapper` (existing guard test). README.md: an H3 for the route, the four codes added to `## API` Error codes, the `max_replicas` and `static` spec fields in the `POST /api/v1/clusters` field list when not yet there, and a `### Scaling` section under `## API` that documents cap, static and replicas for API callers: `max_replicas` (1..`ORCH_MAX_REPLICAS`, default `replicas`, fixed at create), `static` (requires `max_replicas == replicas`), derived hive/alone/scalable, `spec.replicas` changed in place by this route and the agent route with no generation bump and no restart of surviving pods, scale-down removes the highest ordinals after the drain (D3), the leader is never removed (`leader_would_leave`; make another agent leader first), new pods never re-run init scripts. Regenerate `openapi.json` and `frontend/src/api/schema.d.ts`.

#### Acceptance conditions

- AC1: scaling up and down answers 202 with the ScaleResult and the cluster view shows the new spec.replicas with an unchanged generation [evidence: test:tests/test_api_scale.py::test_scale_returns_202_and_updates_view]
- AC2: static_cluster 409, out_of_range 422, cluster_deleting 409, not_found 404 and invalid_request 422 are returned in the documented error shape [evidence: test:tests/test_api_scale.py::test_scale_refusals_map_to_error_codes]
- AC3: a scale that would remove the current leader answers 409 leader_would_leave and changes nothing [evidence: test:tests/test_api_scale.py::test_scale_leader_would_leave]
- AC4: the route is documented and openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_every_route_documented]
- AC5: openapi.json is regenerated [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC6: README documents cap, static and replicas for API callers [evidence: doc-section:README.md#Scaling]
- AC7: the frontend types match openapi.json [evidence: command:cd frontend && npm run check:api]
- AC8: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/api/schemas.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`
- `tests/test_api_scale.py`

#### Interfaces

- Builds `POST /api/v1/clusters/{cluster_id}/scale` (part `orch-cluster-scale-api`, registered cross-epic, consumers agents-helmfile smoke) and `api/schemas.py::ScaleRequest`, `ScaleResult` (part `scale-schemas`).
- Uses `db/clusters.py::set_replicas` (part `scale-replicas-write`).
- README `### Scaling` is the API caller's reference for cap, static, replicas, drain (`status.drain {target, since, waiting}`, built by scale-down-drain) and the leader rule.

#### Expected outcome

`curl -X POST .../clusters/<id>/scale -d '{"replicas":3}'` answers 202 and the cluster grows; every refusal has a documented code.

#### Steps

- Red: write `tests/test_api_scale.py` with the three tests (factories for the cluster, a `cluster_leaders` row for the leader case); run `uv run --frozen pytest -q tests/test_api_scale.py`: fails with 404/405.
- Green: add the schemas and route; document in README; run `uv run python -m agent_orchestrator.api.openapi > openapi.json` and `npm --prefix frontend run gen:api`; run the verify command and `cd frontend && npm run check:api`.

#### Notes

- Follow the existing `ApiError(status, code, message)` pattern in `api/errors.py`; no new error class is needed.
- `ClusterSpec` and the ClusterView already carry `max_replicas` and `static` after hive F3; this task adds only docs for them where missing.
- The route sits beside `create_cluster` and uses the same `Pool` dependency; no `_CREATE_LOCK` (the row lock in `set_replicas` serialises scale calls per cluster).

### S5: agent scale route

- Status: done
- Files: `src/agent_orchestrator/api/agent.py`, `README.md`, `openapi.json`, `frontend/src/api/schema.d.ts`, `tests/test_agent_scale.py`
- Verify: `uv run --frozen pytest -q tests/test_agent_scale.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 0e946497dbd1f4ba9875b743aa1d1157fc2cc441

#### Requirement

Add the agent-facing scale route behind the leader check (design D2, D4; user S2, X1, Q4; foundation D1, D2). In `src/agent_orchestrator/api/agent.py` (the `/agent/v1` router built by hive-mode-leadership-handove F4) add `POST /agent/v1/scale` taking `ScaleRequest` and answering 202 `ScaleResult`. The caller is the agents row returned by F4's `require_agent()` dependency (token, `X-Orch-Cluster` and caller IP equal to `agents.pod_ip`); the route calls `set_replicas(..., caller_agent_id=agent.id)` and maps `not_leader` 403, `static_cluster` 409, `out_of_range` 422, `leader_would_leave` 409, `cluster_deleting` 409; authentication failures stay those of `require_agent()` (401, 403 `forbidden`). The route is served only on the agent port (F4 port branch): the same path on the public port answers 404, and `/api/v1/clusters/{id}/scale` is not reachable on the agent port. Document it in README `## Agent API` with its errors, in F4's format, and regenerate `openapi.json` and `frontend/src/api/schema.d.ts` when F4 includes agent routes there. Contract test: drive the `orchestrator_scale` tool of the pinned any-mcp `OrchestratorPlugin` (F1, release v0.2.0) against the orchestrator app and assert the tool returns the 202 body for the leader and reports `not_leader` as a tool error for another agent, so a mismatch between the plugin and this route fails here.

#### Acceptance conditions

- AC1: the leader's call answers 202 and spec.replicas changes [evidence: test:tests/test_agent_scale.py::test_leader_scales_202]
- AC2: a ready non-leader agent of the same cluster gets 403 not_leader and nothing changes [evidence: test:tests/test_agent_scale.py::test_non_leader_refused_403]
- AC3: static_cluster, out_of_range and leader_would_leave are mapped like the public route; a missing token is 401 and a foreign caller IP is 403 forbidden [evidence: test:tests/test_agent_scale.py::test_agent_scale_refusals]
- AC4: /agent/v1/scale is 404 on the public port and the public scale route is 404 on the agent port [evidence: test:tests/test_agent_scale.py::test_scale_ports_are_separate]
- AC5: the any-mcp orchestrator_scale tool round-trips against the route for the leader and surfaces not_leader for another agent [evidence: test:tests/test_agent_scale.py::test_plugin_scale_tool_contract]
- AC6: README documents the agent scale route [evidence: command:grep -q "/agent/v1/scale" README.md]
- AC7: README and openapi checks stay green [evidence: command:uv run --frozen pytest -q tests/test_readme_api.py]
- AC8: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/api/agent.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`
- `tests/test_agent_scale.py`

#### Interfaces

- Builds `POST /agent/v1/scale` (part `orch-agent-scale-api`, registered cross-epic; consumer: the any-mcp `OrchestratorPlugin.scale` tool, foundation contract `POST /agent/v1/scale {replicas} -> 202; errors static_cluster, out_of_range, leader_would_leave, not_leader`).
- Uses `set_replicas` (part `scale-replicas-write`), `ScaleRequest`/`ScaleResult` (part `scale-schemas`).
- Consumes from hive-mode-leadership-handove: `api/agent.py` router and `require_agent()` (F4), agent port branch in `api/allowlist.py` (F4), `OrchestratorPlugin` tool `orchestrator_scale` (F1, any-mcp v0.2.0 pinned by F3).

#### Expected outcome

The leader agent's `orchestrator_scale` tool call changes the cluster's replica count; any other agent is refused with `not_leader`.

#### Steps

- Red: write `tests/test_agent_scale.py` (agents rows with `pod_ip` equal to the test client host, a `cluster_leaders` row); run `uv run --frozen pytest -q tests/test_agent_scale.py`: fails with 404.
- Green: add the route; document; regenerate openapi and schema types when F4 includes agent routes; run the verify command.

#### Notes

- Copy the client setup F4 uses in its own agent-route tests (two-socket app, caller IP); do not build a second harness.
- Plugin contract test: prefer `any_mcp.testing` with the plugin's HTTP client pointed at the app through an ASGI transport; when the plugin cannot take an injected transport, serve the app with uvicorn on an ephemeral localhost port inside the test.
- Main-agent-only gating of the tool is the wrapper's job (`claude.main_agent_only_tools`, rendered by F3); nothing to add here.

### S6: scale ui control

- Status: done
- Files: `frontend/src/chat/ScaleControl.tsx`, `frontend/src/chat/ScaleControl.test.tsx`, `frontend/src/chat/ChatView.tsx`, `frontend/src/api/client.ts`
- Verify: `cd frontend && npx vitest run src/chat/ScaleControl.test.tsx && npm run lint`
- Verified head: b484c95d547ff7f70f72ebe5969a717407413621

#### Requirement

Add the scale control to the cluster view (design D5; user S2, S3, X2). New `frontend/src/chat/ScaleControl.tsx`, rendered by `frontend/src/chat/ChatView.tsx` in the header next to the agents strip for the selected cluster. It shows `<spec.replicas> of <spec.max_replicas> agents` and two IconButtons, aria-labels "Remove an agent" and "Add an agent", that call the new `scaleCluster(clusterId, {replicas})` in `frontend/src/api/client.ts` (`POST /clusters/{id}/scale`, typed from `schema.d.ts`) with replicas minus or plus one. Buttons are disabled at the bounds (1 and max_replicas) and while a request is in flight. A static cluster shows the count with both buttons disabled and the tooltip "Static cluster: scaling is off"; an alone cluster (max_replicas 1) renders no control. The control does not update optimistically: the count follows the cluster view from the status stream. An API error is shown inline under the control with the API message; for `leader_would_leave` the text adds "Make another agent leader first."

#### Acceptance conditions

- AC1: clicking Add an agent posts replicas + 1 to /clusters/{id}/scale and Remove an agent posts replicas - 1 [evidence: command:cd frontend && npx vitest run src/chat/ScaleControl.test.tsx -t "posts scale"]
- AC2: the buttons are disabled at 1, at max_replicas and while a request is in flight [evidence: command:cd frontend && npx vitest run src/chat/ScaleControl.test.tsx -t "bounds"]
- AC3: a static cluster shows disabled buttons with the static tooltip and an alone cluster renders no control [evidence: command:cd frontend && npx vitest run src/chat/ScaleControl.test.tsx -t "static and alone"]
- AC4: an API error is shown inline, with the make-leader hint for leader_would_leave [evidence: command:cd frontend && npx vitest run src/chat/ScaleControl.test.tsx -t "errors"]
- AC5: lint and typecheck build pass [evidence: command:cd frontend && npm run lint && npm run build]

#### Files

- `frontend/src/chat/ScaleControl.tsx`
- `frontend/src/chat/ScaleControl.test.tsx`
- `frontend/src/chat/ChatView.tsx`
- `frontend/src/api/client.ts`

#### Interfaces

- Consumes `POST /api/v1/clusters/{cluster_id}/scale` (part `orch-cluster-scale-api`) via `frontend/src/api/client.ts::scaleCluster`, and `ClusterView.spec.replicas`, `max_replicas`, `static`.

#### Expected outcome

The chat header of a scalable cluster shows the agent count with add and remove buttons that scale it through the public API.

#### Steps

- Red: write `frontend/src/chat/ScaleControl.test.tsx` with the four cases (mock `fetch` like the existing component tests); run `cd frontend && npx vitest run src/chat/ScaleControl.test.tsx`: fails.
- Green: add `scaleCluster`, the component and its mount in ChatView; run the verify command and `npm run build`.

#### Notes

- Reuse the MUI IconButton and Tooltip patterns of `layout/TopBar.tsx` and the TOKENS font sizes.
- No new route or field: the control reads the cluster view it already has.

### S7: smoke scale check

- Status: done
- Files: `scripts/smoke.sh`, `tests/test_smoke_script.py`, `README.md`
- Verify: `uv run --frozen pytest -q tests/test_smoke_script.py && mise run lint`
- Verified head: 0dd5aa28cc96dbe9ed2a4c8cebc9fa1b800ca49e

#### Requirement

Extend the live smoke to prove scaling on the deployed orchestrator (design D6; user S1, S2, X2). In `scripts/smoke.sh` the smoke cluster is created with `{replicas: 1, max_replicas: 2}`; after the existing any-mcp checks it records pod-0's uid, posts `POST /api/v1/clusters/{id}/scale {replicas: 2}` (expects 202), waits for pod-1 Ready within `SMOKE_TIMEOUT_S`, posts `{replicas: 1}`, waits until pod-1 is gone, and fails with a named message when a step times out, a scale answer is not 202, or pod-0's uid changed. Cleanup stays in the existing trap. `tests/test_smoke_script.py`: the fake API and fake kubectl serve the scale route and the pod-1 lifecycle; tests for the happy path, a refused scale, and pod-0 restarted. README smoke section names the scale step.

#### Acceptance conditions

- AC1: the happy path scales 1 to 2 to 1, keeps pod-0's uid and exits 0 with cleanup [evidence: test:tests/test_smoke_script.py::test_happy_path_exits_zero_and_cleans_up]
- AC2: a scale answer other than 202 fails with a named message and cleans up [evidence: test:tests/test_smoke_script.py::test_scale_refused_fails]
- AC3: a changed pod-0 uid after scaling fails with a named message [evidence: test:tests/test_smoke_script.py::test_pod0_restart_fails]
- AC4: the script stays strict, bounded and shellcheck clean [evidence: test:tests/test_smoke_script.py::test_script_is_shellcheck_clean]
- AC5: lint passes [evidence: command:mise run lint]

#### Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

#### Interfaces

- Consumes `POST /api/v1/clusters/{cluster_id}/scale` (part `orch-cluster-scale-api`) and `max_replicas` on the raw spec create.

#### Expected outcome

`mise run smoke` against the live namespace scales its cluster 1 to 2 to 1 and confirms pod-0 was never restarted.

#### Steps

- Red: extend the fakes and add `test_scale_refused_fails` and `test_pod0_restart_fails`; run `uv run --frozen pytest -q tests/test_smoke_script.py`: fails.
- Green: add the scale step to `scripts/smoke.sh`; run the verify command.

#### Notes

- Keep every curl and wait bounded by the existing timeout variables; `test_script_is_strict_bounded_and_traps` must stay green.
- The smoke runs against the live API only after deploy-pin-scaling applies the release.

### S8: agents strip leaving mark

- Status: done
- Files: `frontend/src/chat/AgentsStrip.tsx`, `frontend/src/chat/AgentsStrip.test.tsx`, `frontend/src/chat/ChatView.tsx`
- Verify: `cd frontend && npx vitest run src/chat/AgentsStrip.test.tsx && npm run lint`
- Verified head: ffc9148a079b6d12b863d1731a8593e877779772

#### Requirement

Show which agents are leaving during a scale-down (design D3, D5; user S1, X2). In `frontend/src/chat/AgentsStrip.tsx` an agent with `ordinal >= cluster.spec.replicas` that is not gone carries a "leaving" label (also in its aria-label); when `cluster.status.drain.waiting` includes its ordinal the label reads "leaving after its turn". `frontend/src/chat/ChatView.tsx` passes `replicas` and the drain waiting list from the cluster view. The strip keeps its existing filter behaviour. API callers derive the same from `ClusterView.spec.replicas`, `AgentView.ordinal` and `status.drain` (documented by the public scale route task).

#### Acceptance conditions

- AC1: an agent above spec.replicas shows "leaving" and an agent in status.drain.waiting shows "leaving after its turn" [evidence: command:cd frontend && npx vitest run src/chat/AgentsStrip.test.tsx -t "leaving"]
- AC2: agents within spec.replicas show no leaving label and the filter toggle still works [evidence: command:cd frontend && npx vitest run src/chat/AgentsStrip.test.tsx]
- AC3: lint and typecheck build pass [evidence: command:cd frontend && npm run lint && npm run build]

#### Files

- `frontend/src/chat/AgentsStrip.tsx`
- `frontend/src/chat/AgentsStrip.test.tsx`
- `frontend/src/chat/ChatView.tsx`

#### Interfaces

- Consumes `ClusterView.status.drain.waiting` (part `scale-drain-status`) and `ClusterView.spec.replicas`.
- `AgentsStripProps` gains `replicas: number` and `drainWaiting?: number[]`.

#### Expected outcome

During a scale-down the agents strip marks the leaving agents and those still finishing a turn.

#### Steps

- Red: add the leaving cases to `frontend/src/chat/AgentsStrip.test.tsx`; run `cd frontend && npx vitest run src/chat/AgentsStrip.test.tsx -t leaving`: fails.
- Green: add the props and labels; pass them from ChatView; run the verify command and `npm run build`.

#### Notes

- `status` is a free-form dict in the types; read `drain` defensively (absent when no drain).

### S9: kind e2e scaling

- Status: done
- Files: `tests/e2e/test_e2e_kind.py`, `e2e/values-kind.yaml`
- Verify: `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 41567ec89755b9c214ff4523aec02e482d5d8c2b

#### Requirement

Prove dynamic join and leave, the scale routes and the static switch on kind through the API alone (design D1-D4; user S1, S2, S3, Q2, Q4, Q7, X2). In `tests/e2e/test_e2e_kind.py` (marker `e2e`, `mise run test:e2e`, PR CI `e2e` job) add, using `/api/v1` over the port-forward, `kubectl` only for pod uids and annotations, and `kubectl exec` into agent pods for `/agent/v1` (the foundation D1 pattern; the fake claude cannot call MCP tools):
- `test_scale_up_and_down_keeps_surviving_pods`: a cluster `{replicas: 1, max_replicas: 3}`; record pod uids and the config-hash annotation; `POST .../scale {replicas: 3}` is 202; three agents become ready; pod-0 keeps its uid and the hash annotation is unchanged; agent-0's `/agent/v1/me` lists three members and the leader is unchanged (a joining agent never leads, Q2); `POST .../scale {replicas: 2}`: agent-2's pod is gone, its AgentView is `gone`, pods 0 and 1 keep their uids, `/agent/v1/me` lists two members.
- `test_scale_refusals`: `replicas` 0 and 4 are 422 `out_of_range`; a static cluster `{replicas: 2, max_replicas: 2, static: true}` is 409 `static_cluster`; after `POST .../leader` makes agent-2 leader (hive route) a scale to 2 is 409 `leader_would_leave`.
- `test_agent_scale_leader_only`: from the leader pod `POST $ORCH_AGENT_URL/agent/v1/scale` with `$ORCH_AGENT_TOKEN` is 202; from another agent pod it is 403 `not_leader`.
- `test_static_single_pod_is_alone`: `{replicas: 1, max_replicas: 1, static: true}`: the pod's rendered any-mcp config has no scale or hive tools in the orchestrator entry's allow list and the rendered ccw config has peers disabled.
- When the scripted fake claude can hold a turn open (check `e2e/agent-test.scenario.json`), `test_scale_down_waits_for_busy_agent`: a turn targeted at the top agent is still running when the scale-down is posted, the pod stays until the turn is sent, then goes; otherwise the drain is pinned by the reconciler unit tests and this is stated in the task result.
Every cluster a test creates is deleted in its teardown; raise `ORCH_MAX_CLUSTERS` in `e2e/values-kind.yaml` only if needed.

#### Acceptance conditions

- AC1: the new e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC2: scale up and down keeps surviving pod uids and the config hash, and members join and leave in /agent/v1/me with the leader unchanged [evidence: judgement:tests/e2e/test_e2e_kind.py::test_scale_up_and_down_keeps_surviving_pods reviewed; executed by the PR CI e2e job]
- AC3: out_of_range, static_cluster, leader_would_leave and agent-route not_leader are asserted through the API only [evidence: judgement:tests/e2e/test_e2e_kind.py refusal and leader-only tests reviewed; executed by the PR CI e2e job]
- AC4: a static single-pod cluster has no scale or hive tools and peers off [evidence: judgement:tests/e2e/test_e2e_kind.py::test_static_single_pod_is_alone reviewed; executed by the PR CI e2e job]
- AC5: every cluster an e2e test creates is deleted in its teardown [evidence: judgement:tests/e2e/test_e2e_kind.py teardown reviewed]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `tests/e2e/test_e2e_kind.py`
- `e2e/values-kind.yaml`

#### Interfaces

- Uses `orch-cluster-scale-api`, `orch-agent-scale-api`, `scale-drain-status`; hive routes `POST /api/v1/clusters/{id}/leader` and `GET /agent/v1/me`, pod env `ORCH_AGENT_URL`, `ORCH_AGENT_TOKEN` (hive F4).
- Existing helpers `api`, `kubectl`, `wait_for`, `agents_of` in `tests/e2e/test_e2e_kind.py`.

#### Expected outcome

The PR CI e2e job shows on kind that a cluster scales up and down through the API with surviving pods untouched, the leader and static rules hold, and a static single pod is alone.

#### Steps

- Add the tests; run `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py`: the new tests are listed.
- Run the verify command: passes. The full run happens in the PR CI e2e job.

#### Ruling

- 2026-10-25 accepted: test-only deliverable (the e2e test is the change); verified for real by CI e2e on the PR

#### Notes

- The agent image is the wrapper image (Python present): exec `python3 -c` with urllib for the agent-route calls, reading the token from the pod env inside the exec so it never appears in test output.
- Pod uids and the config-hash annotation come from `kubectl get pods -l agents.szymonrichert.pl/cluster=<slug> -o jsonpath`.
- Scale tests create their own clusters (not the shared module cluster) and run before the discard test.

### S10: deploy pin scaling

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agent-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster" && uv run ruff check . && uv run ruff format --check .`
- Verified head: not obtained: the verify script did not run

#### Requirement

Release and deploy this epic to the agents namespace (design D6; user S1, S2, S3, X2). The orchestrator release is the main build of this epic's merged agent-orchestrator commit: chart `oci://harbor.szymonrichert.pl/charts/agent-orchestrator` `0.1.0-main.<sha7>` and image `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` (contracts `agent-orchestrator-chart`, `agent-orchestrator-image`); no any-mcp or wrapper release is needed (the scale tool ships in any-mcp v0.2.0 from hive F1, already pinned). In agents-helmfile: `helmfile.yaml.gotmpl` release `agent-orchestrator` chart version `0.1.0-main.<sha7>`, `values/agent-orchestrator/common.yaml` `image.tag` `<sha7>`, `tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image` asserts both carry the sha (offline, text read). The sha is filled with `ticket.py amend` once the orchestrator merge lands on main (precedent `docs/plans/done/cluster-presets/tasks/deploy-pin-presets.md`). Then run `mise run diff` (only the orchestrator chart version and image tag change), `mise run apply` and `mise run smoke` (which now includes the scale step) against the expected kube context.

#### Acceptance conditions

- AC1: the chart version and image tag agree on the orchestrator sha, read offline [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the published chart exists for the pinned version [evidence: command:v=$(grep -A3 'name: agent-orchestrator$' helmfile.yaml.gotmpl | sed -n 's/.*version: //p'); helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator --version "$v"]
- AC3: helmfile apply of the agents namespace succeeds [evidence: judgement:the apply output (helm revision and chart) quoted in the task notes; never run apply as AC evidence]
- AC4: the live smoke passes, including the scale step [evidence: command:mise run smoke]
- AC5: only the orchestrator chart version and image tag change [evidence: judgement:the task diff and mise run diff output reviewed]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

- Consumes the published chart `oci://harbor.szymonrichert.pl/charts/agent-orchestrator` `0.1.0-main.<sha7>` and image `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` (contracts `agent-orchestrator-chart`, `agent-orchestrator-image`).

#### Expected outcome

The agents namespace runs this epic's orchestrator and the live smoke, including the scale step, passes.

#### Steps

- Update `test_orchestrator_pin_matches_image` to the new sha; run it: fails.
- Change the two pins; run the verify command: passes.
- `mise run diff`: only the orchestrator chart version and image tag change. `mise run apply`, then `mise run smoke`: both exit 0.

#### Ruling

- 2026-10-25 accepted: pin landed (ed0233a), PR #17 merged; orchestrator applied helm rev 13 under the user's apply approval; post-apply diff clean; smoke OK incl scale 1->2->1

#### Notes

- Runs after the orchestrator epic branch merges to main; its sha is filled with `ticket.py amend` then (precedent cluster-presets deploy-pin-presets).
- Starts from agents-helmfile main after the hive epic's deploy pin, so the any-mcp v0.2.0 smoke check is already in place.
- `test_release_chart_version_and_needs` and `test_db_secret_matches_rendered_cnpg_cluster` pull charts and are deselected in the verify, not changed.
- `mise run apply` is guarded by lint, test and the kube-context check (`EXPECTED_KUBE_CONTEXT`).

Orchestrator notes (2026-10-25): pin 3b9926d landed on cluster-scaling (ed0233a, rebased onto main 8ff9753), agents-helmfile PR #17 merged. Pre-apply `mise run diff`: only `helm.sh/chart 0.1.0-main.a5b5a75 -> 0.1.0-main.3b9926d` and `app.kubernetes.io/version "a5b5a75" -> "3b9926d"` (live had been rolled back to a5b5a75 by the verifier running AC3's apply at rev 12). `mise run apply`: helm revision 13, chart agent-orchestrator-0.1.0-main.3b9926d deployed. Post-apply diff: `No affected releases`. `mise run smoke` last line: `smoke: OK` (scale 1->2->1, pod-0 uid kept, init scripts succeeded).

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none

## Rulings (migrated)

- kind-e2e-scaling: accept true, at 2026-10-25T07:56:39Z: test-only deliverable (the e2e test is the change); verified for real by CI e2e on the PR
- deploy-pin-scaling: accept true, at 2026-10-25T08:55:13Z: pin landed (ed0233a), PR #17 merged; orchestrator applied helm rev 13 under the user's apply approval; post-apply diff clean; smoke OK incl scale 1->2->1
