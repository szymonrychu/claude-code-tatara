---
title: leadership requests api
status: in-progress
repo: agent-orchestrator
value: the leader and the user can ask for a leadership change through one queue
files: [src/agent_orchestrator/db/leadership.py, src/agent_orchestrator/api/agent.py, src/agent_orchestrator/api/clusters.py, src/agent_orchestrator/api/schemas.py, tests/test_api_leadership.py, README.md, openapi.json, frontend/src/api/schema.d.ts]
verify: "uv run pytest tests/test_api_leadership.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [agent-api-me, migration-0003-hive]
owns: [orch-leader-read]
uses: [orch-agent-api-auth, orch-hive-tables]
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

# leadership requests api

## Requirement

Leadership requests enter the queue (Q4 handover only, Q10 user override, X2). `db/leadership.py` (api-side functions):

- `insert_request(conn, cluster_id, kind, from_agent_id, to_agent_id, reason, epoch) -> int` inserts a queued `leadership_requests` row and sends `NOTIFY leadership_requested` with `{cluster_id}`.
- `current_leader(conn, cluster_id) -> Leader | None` (agent_id, pod_name, epoch); cluster-scaling reuses it for leader-only scale and `leader_would_leave`.

Routes:
- `POST /agent/v1/leadership/handover {to?: pod_name, reason: str 1..500, epoch: int}` -> 202 `{request_id}`; pre-checks (the dispatcher re-checks at apply time): 409 `alone` for a non-hive cluster, 409 `not_leader` when the caller is not the current leader, 409 `stale_epoch` when `epoch` differs from the current epoch, 404 `not_found` for an unknown `to`. No takeover route exists.
- `POST /api/v1/clusters/{id}/leader {agent_id}` (public, the UI "make leader") -> 202 `{request_id}` with kind `user`; 404 for an unknown cluster or an agent of another cluster; 409 `alone` for a non-hive cluster.
- Schemas in `api/schemas.py`; README `## API` and `## Agent API`; `openapi.json` and `frontend/src/api/schema.d.ts` regenerated.

## Acceptance conditions

- AC1: the leader's handover request is queued with 202 and NOTIFY leadership_requested is sent [evidence: test:tests/test_api_leadership.py::test_handover_queued]
- AC2: a non-leader gets 409 not_leader, a stale epoch 409 stale_epoch, an unknown target 404, an alone cluster 409 alone [evidence: test:tests/test_api_leadership.py::test_handover_prechecks]
- AC3: the public make-leader route queues a user request and rejects foreign agents and alone clusters [evidence: test:tests/test_api_leadership.py::test_user_make_leader]
- AC4: current_leader returns the leader row or None [evidence: test:tests/test_api_leadership.py::test_current_leader]
- AC5: README, openapi.json and schema.d.ts agree [evidence: command:uv run pytest tests/test_readme_api.py -q]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/db/leadership.py`
- `src/agent_orchestrator/api/agent.py`
- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/api/schemas.py`
- `tests/test_api_leadership.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`

## Interfaces

- Owns part `orch-leader-read` (cross-epic contract): `db/leadership.py` `insert_request`, `current_leader`.
- Routes `POST /agent/v1/leadership/handover`, `POST /api/v1/clusters/{id}/leader`.

## Expected outcome

The leader and the user can queue leadership changes; members are refused at the door.

## Steps

- Red: write `tests/test_api_leadership.py` for AC1-AC4; run `uv run pytest tests/test_api_leadership.py -q`: fails.
- Green: repo functions, routes, schemas, README, openapi and schema regeneration; run the verify command: passes.

## Notes

- Queue-table pattern: api inserts, NOTIFY; the dispatcher decides (dispatcher-leadership-pass).
