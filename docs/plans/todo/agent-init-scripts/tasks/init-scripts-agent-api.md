---
title: init scripts agent api
status: todo
repo: agent-orchestrator
value: an agent can see how its cluster was initialised and improve the scripts for the next cluster
files: [src/agent_orchestrator/api/agent.py, tests/test_agent_init_scripts.py, README.md]
verify: "uv run pytest tests/test_agent_init_scripts.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [init-scripts-public-api]
owns: [orch-agent-init-scripts-api]
uses: [orch-cluster-init-scripts-api]
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# init scripts agent api

## Requirement

Agent-facing init scripts routes, so an agent knows how its cluster was initialised and can edit the scripts for the next cluster (user decisions C2, C3, X1; design D3, D4, D6). Paths are in code/agent-orchestrator. Builds on hive F4 (`src/agent_orchestrator/api/agent.py`, dependency `require_agent()` returning the caller's Agent row from the cluster bearer token, `X-Orch-Cluster` and caller IP = `agents.pod_ip`; contracts of hive-mode-leadership-handove) and on task init-scripts-public-api.

- In `src/agent_orchestrator/api/agent.py` add `GET /agent/v1/init-scripts` -> 200 InitScriptsView of the caller's cluster, and `PUT /agent/v1/init-scripts` body InitScriptsIn -> 200 InitScriptsView with `preset_updated`. Both use `require_agent()` and the shared helpers `init_scripts_view` / `edit_init_scripts` from `api/clusters.py`; no other logic, no new auth. The cluster is always the token's cluster (the agent cannot name another). Errors as the public routes (422 `invalid_request`, 409 `conflict` when deleting) plus the F4 auth errors (401, 403 `forbidden`).
- Any agent of the cluster may call both (subagents are already refused by the wrapper `claude.main_agent_only_tools` gate rendered by hive F3).
- These are the routes the hive F1 plugin tools `orchestrator_init_scripts_get` and `orchestrator_init_scripts_edit` call (contract orch-agent-init-scripts-api, request and response shape fixed there). Add a parity test that runs the real `any_mcp.orchestrator:OrchestratorPlugin` (the any-mcp version the orchestrator pins after F3) through `any_mcp.testing` against this app: `init_scripts_get` returns the scripts and status, `init_scripts_edit` writes cluster and preset, and the `init_scripts_get` description names `.agent-init/init.sh` and that edits apply to the next cluster. If the harness cannot route the plugin's HTTP client to the ASGI app, serve the agent app with uvicorn on 127.0.0.1 and an ephemeral port, with an agents row whose `pod_ip` is 127.0.0.1. If the plugin's description or payload disagrees with the contract, record a `discovered` entry naming hive F1 and the mismatch; do not change any-mcp in this task.
- Document both routes the way F4 documents `/agent/v1/me` (README `## Agent API`, and the agent OpenAPI document if F4 publishes one), so `tests/test_readme_api.py` passes.

Interfaces: `api/agent.py` routes `GET|PUT /agent/v1/init-scripts`.

Steps: write `tests/test_agent_init_scripts.py` (auth reuse: no token 401, other cluster's token 403, IP not an agent 403; GET; PUT writes cluster and preset; plugin parity) first, see it fail, implement.

## Acceptance conditions

- AC1: an agent of the cluster reads its cluster's scripts, status and file paths through GET /agent/v1/init-scripts [evidence: test:tests/test_agent_init_scripts.py::test_agent_get_init_scripts]
- AC2: PUT /agent/v1/init-scripts writes the cluster spec and its source preset and returns preset_updated, with no generation bump [evidence: test:tests/test_agent_init_scripts.py::test_agent_put_writes_cluster_and_preset]
- AC3: no token is 401, another cluster's token or a caller IP that is not a live agent of the cluster is 403 forbidden, and nothing is written [evidence: test:tests/test_agent_init_scripts.py::test_agent_init_scripts_auth]
- AC4: the pinned OrchestratorPlugin init_scripts_get and init_scripts_edit tools work against these routes and the get description names .agent-init/init.sh and next-cluster semantics [evidence: test:tests/test_agent_init_scripts.py::test_plugin_parity]
- AC5: both routes are documented and the README contract test passes [evidence: command:uv run pytest tests/test_readme_api.py -q]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/api/agent.py`
- `tests/test_agent_init_scripts.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
