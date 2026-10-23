---
title: clusters repository
status: done
repo: agent-orchestrator
value: "Cluster definitions with a validated spec and a generation counter, the reconcile queue every cluster change flows through."
files: [src/agent_orchestrator/spec.py, src/agent_orchestrator/db/clusters.py, tests/test_clusters_repo.py]
verify: "uv run pytest tests/test_clusters_repo.py -q && mise run lint"
depends_on: [migrations-and-schema, settings-model]
owns: [cluster-spec]
uses: [schema-v1, pg-fixture, settings, any-mcp-config]
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-clusters-repository/agent-orchestrator
branch: agent-orchestrator-clusters-repository
verified_head: a6ea51602db755508750a98c06c4d03ecdb26add
run: agent-orchestrator
provides: [cluster-spec, k8s-quantity-parser, clusters-repo]
acs_for_audit: [AC2]
process_gaps: []
---

# clusters repository

## Requirement

The cluster spec model and the clusters table repository (D3, D6, D15, D24).

- `ClusterSpec` (pydantic, extra forbidden): `replicas` 1-16 (default 1), `image` (optional override of the agent image), `model`, `effort` (optional strings), `peers` bool (default true), `workdir` (DNS-1123 label, default `workdir`), `pvc_size` (optional Kubernetes quantity), `resources` (optional requests and limits maps of cpu and memory quantities), `env` (map of non-secret variables; keys must match `[A-Z_][A-Z0-9_]*` and are rejected when they equal `POD_NAME`, start with `CCW_`, `CLAUDE_` or `ANTHROPIC_`, end with `_PROXY` (so `HTTP_PROXY`, `NO_PROXY`) or end with `_BASE_URL`; D22), `any_mcp_config` (optional mapping), `max_attempts` 1-10 (default 5: automatic bounded retry, D24), `auto_compact_pct` 1-100 (optional), `discard_hook_url` (optional http or https URL of the pre-discard webhook, D15; there is no spec-level command hook).
- `validate_slug(slug)`: DNS-1123 label, at most 40 characters; the reserved slug `orchestrator` and any slug starting `orchestrator-` are rejected (D26: they would collide with the orchestrator's own `agent-orchestrator-*` object names).
- `validate_spec(spec, settings) -> None`, raising `SpecInvalid(errors)` that names every violation (D22): `image` must be in `settings.image_allowlist()`; `discard_hook_url` must be an http or https URL; `replicas <= settings.max_replicas`; `pvc_size` (parsed as a Kubernetes quantity) `<= settings.max_pvc_size`; `any_mcp_config` must validate against `any_mcp.config.AnyMcpConfig` (unknown keys rejected, nothing imported or executed).
- `count_active(conn) -> int`: every cluster row (a discarded cluster has no row any more), used by the api for `settings.max_clusters`.
- Repository (api is the writer): `create(conn, slug, spec)` (generation 1, observed_generation 0, desired active; a duplicate slug raises `ClusterExists`), `get`, `get_by_slug`, `list_clusters` (every row, deleting ones included), `update_spec(conn, id, spec)` (bumps generation; a deleting cluster raises `ClusterDeleting`), `request_delete(conn, id)` (desired deleting, bumps generation; idempotent on a deleting cluster).
- Reconciler-only writers: `set_status(conn, id, status, observed_generation)` and `purge(conn, id)` (deletes the row once a discard has removed every Kubernetes object, cascading messages, events, turns, commands and checks; D15). There is no `mark_deleted`.
- Every mutation NOTIFYs `cluster_changed` with `{cluster_id}`.

## Acceptance conditions

- AC1: create stores generation 1, observed 0, desired active [evidence: test:tests/test_clusters_repo.py::test_create_sets_generation_1]
- AC2: slugs that are not DNS-1123 labels or exceed 40 characters are rejected [evidence: test:tests/test_clusters_repo.py::test_slug_rules]
- AC3: update_spec bumps generation and notifies cluster_changed [evidence: test:tests/test_clusters_repo.py::test_update_bumps_generation_and_notifies]
- AC4: request_delete sets desired deleting and bumps generation [evidence: test:tests/test_clusters_repo.py::test_delete_marks_deleting]
- AC5: purge removes the cluster and its whole history [evidence: test:tests/test_clusters_repo.py::test_purge_cascades_history]
- AC6: secret-looking env keys are rejected by ClusterSpec [evidence: test:tests/test_clusters_repo.py::test_spec_rejects_secret_env]
- AC7: a duplicate slug raises ClusterExists [evidence: test:tests/test_clusters_repo.py::test_duplicate_slug]
- AC8: env keys that are reserved are rejected: POD_NAME, CCW_*, CLAUDE_*, ANTHROPIC_*, *_PROXY and *_BASE_URL [evidence: test:tests/test_clusters_repo.py::test_spec_rejects_reserved_env_keys]
- AC9: the reserved slugs orchestrator and orchestrator-* are rejected [evidence: test:tests/test_clusters_repo.py::test_reserved_slugs_rejected]
- AC10: validate_spec rejects an image outside the allowlist and accepts agent_image [evidence: test:tests/test_clusters_repo.py::test_validate_spec_image_allowlist]
- AC11: validate_spec rejects replicas and pvc_size above the caps [evidence: test:tests/test_clusters_repo.py::test_validate_spec_caps]
- AC12: validate_spec rejects an any_mcp_config that the any-mcp config model rejects [evidence: test:tests/test_clusters_repo.py::test_validate_spec_any_mcp_config_schema]
- AC13: count_active counts every cluster row, deleting ones included, and a purged cluster no longer counts [evidence: test:tests/test_clusters_repo.py::test_count_active_counts_rows]
- AC14: max_attempts defaults to 5 and discard_hook_url accepts http(s) and rejects other schemes [evidence: test:tests/test_clusters_repo.py::test_spec_retry_default_and_discard_hook_url]

## Files

- `src/agent_orchestrator/spec.py`
- `src/agent_orchestrator/db/clusters.py`
- `tests/test_clusters_repo.py`

## Interfaces

- `agent_orchestrator.spec:ClusterSpec`, `validate_slug`, `validate_spec`, `SpecInvalid` (contract `cluster-spec`)
- `agent_orchestrator.db.clusters`: `create`, `get`, `get_by_slug`, `list_clusters`, `update_spec`, `request_delete`, `purge`, `set_status`, `count_active`, `ClusterExists`, `ClusterDeleting`

## Expected outcome

Clusters can be created, edited and marked for discard, each change waking the reconciler; the reconciler deletes the row when the discard completes.

## Steps

- Write tests/test_clusters_repo.py with the fourteen named tests using the `pool` fixture; run it; expect failures.
- Implement spec.py and db/clusters.py.
- Rerun `uv run pytest tests/test_clusters_repo.py -q`; expect `14 passed`; run `mise run lint`.

## Notes

Defaults that come from settings (agent image, model, replicas, auto-compact) are resolved by the renderer and the API meta route, not stored into the spec, so changing a default reaches every cluster on its next reconcile.
