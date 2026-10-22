---
title: settings model
status: todo
repo: agent-orchestrator
value: "One validated configuration surface for every process, whose env names are the contract the Helm chart sets."
files: [src/agent_orchestrator/settings.py, tests/test_settings.py, README.md]
verify: "uv run pytest tests/test_settings.py -q && mise run lint"
depends_on: [scaffold-repo-and-cli]
owns: [settings, agent-orchestrator-settings-env]
uses: []
model: ""
estimate: 5
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

# settings model

## Requirement

Add `Settings` (pydantic-settings, env prefix `ORCH_`) with these fields and defaults:

- `database_url` (required), `master_key` from `ORCH_MASTER_KEY` or `ORCH_MASTER_KEY_FILE` (the file wins when both are set; at least 32 bytes after stripping; required only by processes that call `require_master_key()`)
- `namespace` = agents, `agent_image` (required by `require_agent_image()`), `check_image` (defaults to agent_image)
- `default_model` = "", `default_effort` = "", `models` (comma-separated list, default empty), `default_replicas` = 1, `default_auto_compact_pct` = 95
- `pvc_storage_class` = rook-ceph-rwx, `pvc_size` = 20Gi, `claude_secret_name` = agent-orchestrator-claude, `image_pull_secret` = regcred
- `any_mcp_config_file` (default empty, meaning `{}`), `wrapper_port` = 8080, `cluster_domain` = cluster.local, `agent_termination_grace_seconds` = 90
- `http_host` = 0.0.0.0, `http_port` = 8000, `static_dir` (default empty: the SPA is not mounted)
- `dispatch_poll_seconds` = 2, `reconcile_poll_seconds` = 10, `ingest_refresh_seconds` = 5, `shutdown_grace_seconds` = 20, `log_level` = INFO

- Hardening and cap fields (D22, D26): `clusters_namespace` = agents-clusters (`ORCH_CLUSTERS_NAMESPACE`; configurable, the gate confirms the default; the namespace that holds every agent cluster object, pod, Job and per-pod DNS name, distinct from `namespace`, the orchestrator's own), `allowed_cidrs` (comma-separated CIDR list, default 192.168.1.0/24, `ORCH_ALLOWED_CIDRS`; an unparsable entry is a validation error naming the variable), `agent_images` (comma-separated allowlist for `ClusterSpec.image`, default empty, `ORCH_AGENT_IMAGES`; the effective allowlist always also contains `agent_image`), `max_replicas` = 16 (`ORCH_MAX_REPLICAS`), `max_pvc_size` = 100Gi (`ORCH_MAX_PVC_SIZE`), `max_clusters` = 20 (`ORCH_MAX_CLUSTERS`, counts non-purged clusters).
- Timing fields (D23, D24, D25): `wrapper_send_timeout_seconds` = 15, `dispatching_stale_seconds` = 60, `dispatching_heartbeat_seconds` = 5, `lock_heartbeat_seconds` = 5, `lock_tcp_user_timeout_seconds` = 15. Validation: `2 * wrapper_send_timeout_seconds <= dispatching_stale_seconds` (the send timeout stays well below the stale cutoff).
- Helpers `Settings.allowed_networks() -> list[ip_network]` and `Settings.image_allowlist() -> frozenset[str]`.

Invalid or missing values raise one error naming every bad `ORCH_*` variable. README.md gains `## Configuration`: a table of every variable, its default and the commands that read it. These names are the cross-epic contract `agent-orchestrator-settings-env` consumed by the deploy epic's chart.

## Acceptance conditions

- AC1: defaults match the documented table [evidence: test:tests/test_settings.py::test_defaults]
- AC2: a missing ORCH_DATABASE_URL raises an error naming it [evidence: test:tests/test_settings.py::test_database_url_required]
- AC3: ORCH_MASTER_KEY_FILE is read and wins over ORCH_MASTER_KEY [evidence: test:tests/test_settings.py::test_master_key_from_file]
- AC4: a master key shorter than 32 bytes is rejected [evidence: test:tests/test_settings.py::test_master_key_too_short_rejected]
- AC5: every settings field's env name appears in the README Configuration table [evidence: test:tests/test_settings.py::test_env_names_documented_in_readme]
- AC6: README documents the configuration [evidence: doc-section:README.md#Configuration]
- AC7: the cluster namespace, cap and timing fields have the documented defaults and ORCH_CLUSTERS_NAMESPACE overrides the namespace [evidence: test:tests/test_settings.py::test_clusters_namespace_cap_and_timing_defaults]
- AC8: ORCH_ALLOWED_CIDRS parses to networks and a bad entry is rejected naming the variable [evidence: test:tests/test_settings.py::test_allowed_cidrs_parsed_and_bad_entry_rejected]
- AC9: the image allowlist always contains agent_image plus ORCH_AGENT_IMAGES [evidence: test:tests/test_settings.py::test_image_allowlist_includes_agent_image]
- AC10: a send timeout above half the dispatching stale cutoff is rejected [evidence: test:tests/test_settings.py::test_send_timeout_must_be_well_below_stale_cutoff]

## Files

- `src/agent_orchestrator/settings.py`
- `tests/test_settings.py`
- `README.md`

## Interfaces

- `agent_orchestrator.settings:Settings` (BaseSettings) with the fields above
- `Settings.allowed_networks()`, `Settings.image_allowlist()`
- `Settings.require_master_key() -> bytes`, `Settings.require_agent_image() -> str`
- `agent_orchestrator.settings:load_settings() -> Settings`

## Expected outcome

Every process loads one Settings object from `ORCH_*` env; README lists every variable.

## Steps

- Write tests/test_settings.py with the nine named tests (monkeypatch env); run `uv run pytest tests/test_settings.py -q`; expect failures.
- Implement settings.py and the README table.
- Rerun; expect `9 passed`; run `mise run lint`.

## Notes

`namespace` is the orchestrator's own namespace (agents); every Kubernetes object the reconciler manages uses `clusters_namespace`. The infrastructure registry records contract `agent-orchestrator-settings-env` (owner this epic, consumer agents-k8s-deploy): renaming a variable later breaks the chart. `default_auto_compact_pct` feeds the gauge tick and the rendered `claude.env.claude_autocompact_pct_override` (D13).
