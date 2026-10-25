---
title: anymcp plugin session
status: todo
repo: any-mcp
value: "agents' any-mcp tools address the orchestrator's session, matching the renamed agent API"
files: [src/any_mcp/orchestrator.py, tests/test_orchestrator_plugin.py, tests/test_nomenclature.py, README.md]
verify: "uv run pytest -q tests/test_orchestrator_plugin.py tests/test_nomenclature.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# anymcp plugin session

## Requirement

Rename the orchestrator plugin's unit from cluster to session (design D2, D11, D12; user decision: cluster is renamed session throughout; contract `orch-agent-api-session-header`). Paths are in code/any-mcp.

- `src/any_mcp/orchestrator.py`: the plugin Config field `cluster` becomes `session` (extra keys are already refused, so a config carrying `cluster` now fails validation; no alias); the request header `X-Orch-Session: <session>` replaces `X-Orch-Cluster`; every tool description and docstring says session ("the agents of the session", "Scale this session to a number of agents...", "the init scripts this session was initialised with", "applies to the next session created from the spec"); the docstring names agents-orchestrator.
- Error codes and fields passed through from the orchestrator follow design D2: `static_session` (was `static_cluster`), init scripts `applies: next_session` (was `next_cluster`).
- `tests/test_orchestrator_plugin.py`: the fixture config uses `session`; tests `test_session_header_sent` (the header `x-orch-session` carries the configured session, and no `x-orch-cluster` header is sent), `test_cluster_key_refused` (a config with `cluster` fails), and the existing code and `applies` assertions on the new values.
- `README.md`: the plugin's config fields and the example (`session: s-1`), "The token is scoped to one session", agents-orchestrator as the API's name.
- `tests/test_nomenclature.py` (new, written first): `git ls-files` over `src/any_mcp/orchestrator.py`, `tests/test_orchestrator_plugin.py` and `README.md` finds no line matching `/cluster/i` or `agent[-_]orchestrator`.
- CHANGELOG and the version belong to anymcp-release-v0-3-0.

## Acceptance conditions

- AC1: the plugin sends X-Orch-Session with the configured session and never X-Orch-Cluster [evidence: test:tests/test_orchestrator_plugin.py::test_session_header_sent]
- AC2: a plugin config carrying the old cluster key is refused [evidence: test:tests/test_orchestrator_plugin.py::test_cluster_key_refused]
- AC3: the plugin source, its tests and the README no longer name the unit cluster or the old project name [evidence: command:uv run pytest -q tests/test_nomenclature.py]
- AC4: the plugin tests and lint pass [evidence: command:uv run pytest -q tests/test_orchestrator_plugin.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/any_mcp/orchestrator.py`
- `tests/test_orchestrator_plugin.py`
- `tests/test_nomenclature.py`
- `README.md`

## Interfaces

- `any_mcp.orchestrator.OrchestratorPlugin` Config: `base_url, token, session, agent, slug, max_replicas, static, hive, ...` (extra keys refused); header `X-Orch-Session`. Must agree with orch-agent-api-sessions (contract `orch-agent-api-session-header`).

## Expected outcome

The plugin addresses the orchestrator's session by key `session` and header `X-Orch-Session`; `cluster` is refused.

## Steps

- Red: write `tests/test_nomenclature.py` and the two new plugin tests; `uv run pytest -q tests/test_orchestrator_plugin.py tests/test_nomenclature.py` fails on the old key, header and texts.
- Green: rename in `orchestrator.py` and README; the verify passes, lint clean.

## Notes

- design.md D2 is the vocabulary; error codes come from the orchestrator (`static_session`).
- Do not touch CHANGELOG or the version (anymcp-release-v0-3-0).
