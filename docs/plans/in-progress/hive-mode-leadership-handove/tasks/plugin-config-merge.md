---
title: plugin config merge
status: in-progress
repo: agent-orchestrator
value: "hive agents load the orchestrator tools next to the user's own any-mcp plugins"
files: [src/agent_orchestrator/k8s/on_start.py, tests/test_on_start.py]
verify: "uv run pytest tests/test_on_start.py tests/test_render.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [spec-cap-static, orch-pin-bumps]
owns: [orch-plugin-entry]
uses: [orch-spec-cap-static, orch-hive-pins, any-mcp-orchestrator-plugin]
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/hive-mode-leadership-handove-plugin-config-merge/agent-orchestrator
branch: hive-mode-leadership-handove-plugin-config-merge
verified_head: ""
run: ""
provides: []
---

# plugin config merge

## Requirement

Foundation part F3, plugin entry (X1, D2, Q7). In `k8s/on_start.py`:

- `orchestrator_allow(spec) -> list[str]`: `["me", "leadership_handover", "lock_claim", "lock_release", "lock_list", "lock_reassign"]` when `spec.hive`, else `[]`. This function is the one extension point: cluster-scaling adds `scale` when `spec.scalable`, agent-init-scripts adds `init_scripts_get` and `init_scripts_edit` for every cluster.
- The rendered any-mcp config merges the entry `{name: "orchestrator", plugin: "any_mcp.orchestrator:OrchestratorPlugin", namespace: "orchestrator", allow: orchestrator_allow(spec), config: {base_url: "${ORCH_AGENT_URL}", token: "${ORCH_AGENT_TOKEN}", cluster: "${ORCH_CLUSTER_ID}", agent: "${POD_NAME}", slug, max_replicas, static, hive, auto_compact_pct}}` into `plugins` of `spec.any_mcp_config` when set, else of the settings default; user entries are kept unchanged (no more wholesale replacement). The entry is omitted when the allow list is empty or `settings.agent_api_url` is unset.
- The written `/opt/any-mcp/etc/any-mcp.yaml` holds the literal `${...}` placeholders (any-mcp expands them from its env at load); the token value is never written to disk. The quoted heredoc keeps them literal.
- The output never depends on the live replica count (hash invariant).
- The merged config validates with any-mcp's config model.

## Acceptance conditions

- AC1: an alone cluster gets no orchestrator entry [evidence: test:tests/test_on_start.py::test_alone_has_no_orchestrator_entry]
- AC2: a hive cluster gets the entry with the six hive tools in allow and the Config fields from the spec [evidence: test:tests/test_on_start.py::test_hive_entry_and_allow]
- AC3: a user any_mcp_config keeps its own plugins and gains the entry [evidence: test:tests/test_on_start.py::test_user_config_merged]
- AC4: the written config contains the literal placeholders and no token value [evidence: test:tests/test_on_start.py::test_placeholders_not_secrets]
- AC5: the script is identical for two replica counts within max_replicas [evidence: test:tests/test_on_start.py::test_invariant_to_replicas]
- AC6: render tests and lint pass [evidence: command:uv run pytest tests/test_render.py -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/k8s/on_start.py`
- `tests/test_on_start.py`

## Interfaces

- Owns part `orch-plugin-entry` (cross-epic contract): `k8s/on_start.py` `orchestrator_allow(spec)` and the merged `orchestrator` entry.

## Expected outcome

Hive pods start any-mcp with the orchestrator tools next to the user's plugins; alone pods start it exactly as before.

## Steps

- Red: write `tests/test_on_start.py` for AC1-AC5; run `uv run pytest tests/test_on_start.py -q`: fails.
- Green: merge logic in `on_start.py`; run the verify command: passes.

## Notes

- `any_mcp_config(spec)` returns the user config verbatim today (`on_start.py:17-20`); the heredoc is quoted (`<<'{DELIMITER}'`, `:39`).
- any-mcp treats an empty `allow` as "all tools", hence omitting the entry when nothing is allowed.
