---
title: file locks api
status: todo
repo: agent-orchestrator
value: agents claim files and get warned before editing a file another agent holds
files: [src/agent_orchestrator/db/file_locks.py, src/agent_orchestrator/api/agent.py, tests/test_api_locks.py, README.md, openapi.json, frontend/src/api/schema.d.ts]
verify: "uv run pytest tests/test_api_locks.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [leadership-requests-api]
owns: []
uses: [orch-agent-api-auth, orch-leader-read, orch-hive-tables]
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

# file locks api

## Requirement

Advisory file locks (Q11: agents claim files, a write to a file claimed by another agent is warned, the leader can reassign or discard any lock). `db/file_locks.py` (api is the single writer) and agent routes:

- Paths are normalised relative to the cluster workdir (`spec.workdir`): absolute paths under it are converted; `..` or paths outside give 400 `invalid_path`.
- `POST /agent/v1/locks/claim {paths: 1..50}` -> 200 `{claimed: [path], held: [{path, agent}]}`; a lock held by another live agent stays theirs; a lock held by a gone agent is taken over.
- `POST /agent/v1/locks/release {paths}` -> `{released: [path]}`, own locks only.
- `GET /agent/v1/locks` -> `{locks: [{path, agent, claimed_at}]}`, live agents only.
- `POST /agent/v1/locks/reassign {path, to: pod_name | null}` -> leader only (403 `not_leader`); `to` null discards the lock; unknown `to` 404 -> `{path, agent}` (agent null when discarded).
- `POST /agent/v1/locks/check`: the wrapper's `onAgentToolCall` webhook (rendered by render-hive-gating). Body is the wrapper hook envelope (README `## Hooks`); reads the tool name and `tool_input.file_path` or `notebook_path`. When the file is claimed by another live agent: 200 `{decision: "allow", additional_context: "Advisory lock: <path> is claimed by <agent> since <time>. Coordinate with them or the leader before editing."}`; otherwise 200 `{decision: "allow"}`. It never denies and is one indexed query.
- README `## Agent API` locks section; `openapi.json` and `frontend/src/api/schema.d.ts` regenerated.

## Acceptance conditions

- AC1: claim returns claimed and held paths and takes over locks of gone agents [evidence: test:tests/test_api_locks.py::test_claim]
- AC2: release frees only the caller's own locks and list shows live agents' locks [evidence: test:tests/test_api_locks.py::test_release_and_list]
- AC3: reassign and discard work for the leader and give 403 not_leader for members [evidence: test:tests/test_api_locks.py::test_reassign_leader_only]
- AC4: paths outside the workdir are 400 invalid_path and absolute workdir paths are normalised [evidence: test:tests/test_api_locks.py::test_path_normalisation]
- AC5: check returns additional_context naming the holder for another agent's lock and a plain allow otherwise, never deny [evidence: test:tests/test_api_locks.py::test_check_webhook]
- AC6: README, openapi.json and schema.d.ts agree [evidence: command:uv run pytest tests/test_readme_api.py -q]
- AC7: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/db/file_locks.py`
- `src/agent_orchestrator/api/agent.py`
- `tests/test_api_locks.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`

## Interfaces

- `db/file_locks.py` (api writer of `file_locks`); routes `/agent/v1/locks`, `/locks/claim`, `/locks/release`, `/locks/reassign`, `/locks/check`.
- The check route answers the wrapper webhook shape: `decision`, `additional_context`.

## Expected outcome

Agents claim files; a write to another agent's file brings a warning into the writer's context.

## Steps

- Red: write `tests/test_api_locks.py` for AC1-AC5; run `uv run pytest tests/test_api_locks.py -q`: fails.
- Green: repo, routes, README, openapi and schema regeneration; run the verify command: passes.

## Notes

- Wrapper hook envelope and blocking webhook body: wrapper README `## Hooks` and `### Webhook actions`.
