---
title: orch sessions sweep
status: todo
repo: agents-orchestrator
value: "the orchestrator's database, code, public API and labels call the unit a session"
files: [src/agents_orchestrator/db/migrations/0005_sessions.sql, src/agents_orchestrator/, tests/, openapi.json, README.md]
verify: "uv run pytest -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-wrapper-session-id]
model: opus
review: ""
verified_head: ""
points: 8
expected_minutes: 18
expected_tokens: 2172985
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch sessions sweep

## Requirement

Rename the orchestrator's unit from cluster to session in the database, the Python code, the public HTTP API and the Kubernetes label, in one atomic sweep (design D2, D4, D8, D15; user decision: cluster is renamed session throughout (API, UI, docs); gate Q1; contract `orch-sessions-api`). Paths are in code/agents-orchestrator. Apply the design D2 table exactly; no alias, no old route, no compatibility view.

- Database: new `src/agents_orchestrator/db/migrations/0005_sessions.sql`: table `clusters` to `sessions`, `cluster_leaders` to `session_leaders`; column `cluster_id` to `session_id` in every table that has it (agents, messages, events, checks, leadership_requests, session_leaders, file_locks and any other `\d` shows); every index, primary key, unique, foreign-key and check constraint whose name contains `cluster` renamed to the matching `session` name (for example `messages_cluster_status_id` to `messages_session_status_id`, `events_cluster_id_desc` to `events_session_id_desc`). `ALTER ... RENAME` only. 0001-0004 stay byte-identical. NOTIFY channel `cluster_changed` becomes `session_changed`.
- Python: every identifier, module, docstring, comment and log line naming the unit: `db/clusters.py` to `db/sessions.py` (`git mv`; `Cluster`, `ClusterExists`, `ClusterNotFound`, `ClusterBeingDeleted` to `Session...`), `spec.ClusterSpec` to `SessionSpec`, `tokens.ClusterTokens` to `SessionTokens`, `render_cluster` to `render_session`, `list_clusters`, `cluster_max_attempts`, `cluster_aggregates`, `export_cluster_history`, `hive_clusters` and every other `*cluster*` name to its `session` form; `api/clusters.py` to `api/sessions.py`.
- Settings: `max_clusters` to `max_sessions` (`ORCH_MAX_SESSIONS`); any other setting naming the unit likewise; `cluster_domain` (`ORCH_CLUSTER_DOMAIN`, Kubernetes DNS) stays.
- Public API: `/api/v1/clusters...` to `/api/v1/sessions...` (every sub-route, path parameter `session_id`); schemas `SessionSpec`, `SessionSummary`, `SessionView`, `CreateSession`; every `cluster_id` field to `session_id`; `MetaCaps.max_clusters` to `max_sessions`; error codes `session_deleting`, `static_session`, `session_limit`; init scripts `applies: next_session`; SSE event types `session_status`, `session_removed`; `api/service_auth.py` allowlist routes; `openapi.json` regenerated (`uv run python -m agents_orchestrator.api.openapi > openapi.json`); README.md API reference sections (routes, schemas, codes, SSE types) rewritten to match (`tests/test_readme_api.py` pins them).
- Kubernetes label: `k8s/labels.py` `SESSION_LABEL = "agents.szymonrichert.pl/session"` (constant renamed), used by `session_labels`, selectors and `kube.owns`; `tests/golden/cluster_*.yaml` to `tests/golden/session_*.yaml` with the new label. The `agent-<slug>` object prefix stays (D10). No relabel code (D8).
- Not in this task (orch-agent-api-sessions): the agent API header `X-Orch-Cluster`, the pod env `ORCH_CLUSTER_ID`, the rendered any-mcp plugin key `cluster` and `api/agent.py`'s `Me.cluster_id`; they stay until any-mcp v0.3.0 exists. Not in this task (orch-docs-e2e-sessions): README prose outside the API reference, AGENTS.md, MEMORY.md, chart comments, e2e scripts and examples.
- tests/: every test follows the rename; files named after the unit are renamed with `git mv` (`test_clusters_repo.py` to `test_sessions_repo.py`, `test_api_clusters.py` to `test_api_sessions.py`).
- Tests first: `tests/test_migrations.py::test_0005_renames_clusters_to_sessions` (apply 0001-0004 from a tmp dir, seed a cluster with an agent, message, event, check, leader, lock and preset link, run all migrations, read every row back under the new names; `information_schema` and `pg_indexes`/`pg_constraint` show no name containing `cluster`); `tests/test_api_sessions.py::test_old_cluster_routes_gone` (`/api/v1/clusters` answers 404); `tests/test_nomenclature.py` (new, D12): `git ls-files src/agents_orchestrator tests openapi.json` lines matching `/cluster/i`, minus the D12 Kubernetes/CNPG/kind allowlist, are none, except in `api/agent.py`, `k8s/render.py` and `k8s/on_start.py` and their tests (`tests/test_api_agent.py`, `tests/test_agent_*.py`, `tests/test_on_start.py`, `tests/test_render.py`), which orch-agent-api-sessions adds to the guard.

## Acceptance conditions

- AC1: migration 0005 keeps every row and leaves no table, column, index or constraint named cluster [evidence: test:tests/test_migrations.py::test_0005_renames_clusters_to_sessions]
- AC2: the public API serves /api/v1/sessions and the old routes answer 404 [evidence: test:tests/test_api_sessions.py::test_old_cluster_routes_gone]
- AC3: src, tests and openapi.json name the unit session only, outside the agent-API files left to orch-agent-api-sessions [evidence: command:uv run pytest -q tests/test_nomenclature.py]
- AC4: README API reference and openapi.json match the app [evidence: command:uv run pytest -q tests/test_readme_api.py]
- AC5: objects carry the agents.szymonrichert.pl/session label and ownership checks use it [evidence: command:uv run pytest -q tests/test_render.py tests/test_reconciler.py]
- AC6: the component suite and lint pass [evidence: command:uv run pytest -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/db/migrations/0005_sessions.sql`
- `src/agents_orchestrator/`
- `tests/`
- `openapi.json`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
