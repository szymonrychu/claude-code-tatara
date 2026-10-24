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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
