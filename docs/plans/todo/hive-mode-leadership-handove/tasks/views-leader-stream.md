---
title: views leader stream
status: todo
repo: agent-orchestrator
value: "API clients see who leads, the epoch and every agent's context, live"
files: [src/agent_orchestrator/api/schemas.py, src/agent_orchestrator/db/views.py, src/agent_orchestrator/api/clusters.py, src/agent_orchestrator/api/streams.py, tests/test_leader_views.py, README.md, openapi.json, frontend/src/api/schema.d.ts]
verify: "uv run pytest tests/test_leader_views.py tests/test_api_streams.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [dispatcher-leadership-pass, file-locks-api]
owns: [orch-leader-views]
uses: [orch-leadership-pass]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# views leader stream

## Requirement

The API shows the leader (X2, Q9, Q10). `ClusterView` gains `hive: bool`, `max_replicas: int`, `static: bool`, `leader_agent_id: uuid | null`, `leader_epoch: int | null`; `AgentView` gains `leader: bool` and exposes `context_pct` (add it when missing) so every agent's context is visible. `db/views.py` joins `cluster_leaders`. `/stream` emits a `leader_changed {cluster_id, agent_id, epoch}` frame on `NOTIFY leader_changed`, and the `cluster_status` / `agent_status` diffs carry the new fields. README frame list (enforced by `tests/test_readme_api.py`), `openapi.json`, `frontend/src/api/schema.d.ts`.

## Acceptance conditions

- AC1: ClusterView carries hive, max_replicas, static, leader_agent_id and leader_epoch [evidence: test:tests/test_leader_views.py::test_cluster_view_leader_fields]
- AC2: AgentView carries leader and context_pct [evidence: test:tests/test_leader_views.py::test_agent_view_leader_and_context]
- AC3: /stream emits leader_changed on NOTIFY leader_changed and the status diffs reflect the new leader [evidence: test:tests/test_leader_views.py::test_leader_changed_frame]
- AC4: README, openapi.json and schema.d.ts agree; stream tests pass [evidence: command:uv run pytest tests/test_readme_api.py tests/test_api_streams.py -q]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/api/schemas.py`
- `src/agent_orchestrator/db/views.py`
- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/api/streams.py`
- `tests/test_leader_views.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`

## Interfaces

- Owns part `orch-leader-views`: `ClusterView` and `AgentView` fields and the `leader_changed` frame.

## Expected outcome

A headless client sees the leader, the epoch and every agent's context, live.

## Steps

- Red: write `tests/test_leader_views.py` for AC1-AC3; run `uv run pytest tests/test_leader_views.py -q`: fails.
- Green: views, schemas, stream frame, README, openapi and schema regeneration; run the verify command: passes.

## Notes

- Views at `api/schemas.py:54-85`, built in `api/clusters.py:43-78`; frames in `api/streams.py:174-268`.
