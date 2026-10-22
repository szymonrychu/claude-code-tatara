---
title: settings model
status: todo
repo: agent-orchestrator
value: "One validated configuration surface for every process, whose env names are the contract the Helm chart sets."
files: [src/agent_orchestrator/settings.py, tests/test_settings.py, README.md]
verify: "uv run pytest tests/test_settings.py -q && mise run lint"
depends_on: [scaffold-repo-and-cli]
owns: [settings, agent-orchestrator-settings-env]
uses: [any-mcp-release]
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

Add `Settings` (pydantic-settings, env prefix `ORCH_`) with the fields and defaults below.

Core fields:
- `database_url` (required).
- `master_key`, from `ORCH_MASTER_KEY` or `ORCH_MASTER_KEY_FILE`. The file wins when both are set. It must be at least 32 bytes after stripping, and is required only by processes that call `require_master_key()`.
- `namespace` = agents. This is the one namespace of the orchestrator and of every agent cluster (D26); the chart sets it to the release namespace. There is no `clusters_namespace` field and no `ORCH_CLUSTERS_NAMESPACE`.
- `agent_image` (required by `require_agent_image()`; the claude-code-wrapper image the agent pods run, D16) and `check_image` (defaults to agent_image).

Session and Kubernetes defaults:
- `default_model` = "", `default_effort` = "", `models` (comma-separated list, default empty), `default_replicas` = 1, `default_auto_compact_pct` = 95
- `pvc_storage_class` = rook-ceph-rwx, `pvc_size` = 20Gi, `claude_secret_name` = agent-orchestrator-claude, `image_pull_secret` = regcred (an empty value means no imagePullSecrets)
- `any_mcp_config_file` (default empty, meaning `{}`), `wrapper_port` = 8080, `cluster_domain` = cluster.local, `agent_termination_grace_seconds` = 90

Process fields:
- `http_host` = 0.0.0.0, `http_port` = 8000, `static_dir` (default empty: the SPA is not mounted)
- `dispatch_poll_seconds` = 2, `reconcile_poll_seconds` = 10, `ingest_refresh_seconds` = 5, `shutdown_grace_seconds` = 20, `log_level` = INFO

Hardening and cap fields (D22):
- `allowed_cidrs`: a comma-separated CIDR list, default 192.168.1.0/24 (`ORCH_ALLOWED_CIDRS`). An unparsable entry is a validation error naming the variable.
- `agent_images`: a comma-separated allowlist for `ClusterSpec.image`, default empty (`ORCH_AGENT_IMAGES`). The effective allowlist always also contains `agent_image`.
- `max_replicas` = 16 (`ORCH_MAX_REPLICAS`), `max_pvc_size` = 100Gi (`ORCH_MAX_PVC_SIZE`), and `max_clusters` = 20 (`ORCH_MAX_CLUSTERS`, counting existing cluster rows).

Timing fields (D23, D24, D25):
- `wrapper_send_timeout_seconds` = 15, `dispatching_stale_seconds` = 60, `dispatching_heartbeat_seconds` = 5, `lock_heartbeat_seconds` = 5, `lock_tcp_user_timeout_seconds` = 15.
- Validation: `2 * wrapper_send_timeout_seconds <= dispatching_stale_seconds`, so the send timeout stays well below the stale cutoff.

Retry and ambiguity fields (D24):
- `retry_backoff_base_seconds` = 2, `retry_backoff_max_seconds` = 60, `ambiguous_settle_seconds` = 60, `ambiguous_deadline_seconds` = 600.
- Validation: `ambiguous_settle_seconds >= 2 * wrapper_send_timeout_seconds`, `ambiguous_deadline_seconds > ambiguous_settle_seconds`, and `retry_backoff_max_seconds >= retry_backoff_base_seconds > 0`.
- Helper `Settings.retry_delay_seconds(attempts) -> float`: `min(base * 2 ** (attempts - 1), max)`.

Discard hook fields (D15):
- `discard_hook_command` (default empty) and `discard_hook_url` (default empty), with at most one of them set. The URL must be http or https. A violation is a validation error naming the variable.
- `discard_hook_timeout_seconds` = 120.

any-mcp install fields (D16):
- `any_mcp_repo` = https://github.com/szymonrychu/any-mcp.
- `any_mcp_ref`, defaulting to the any-mcp release tag of contract any-mcp-release (v0.1.0). It must match `^v\d+\.\d+\.\d+$`, so a pinned tag and never a branch.
- `on_start_timeout_seconds` = 600.

Helpers:
- `Settings.allowed_networks() -> list[ip_network]`
- `Settings.image_allowlist() -> frozenset[str]`
- `Settings.discard_hook() -> DiscardHook | None` (`kind` command or url, and `target`)

Invalid or missing values raise one error naming every bad `ORCH_*` variable. README.md gains `## Configuration`: a table of every variable, its default and the commands that read it. These names are the cross-epic contract `agent-orchestrator-settings-env`, consumed by this repo's Helm chart and by epic agents-helmfile.

## Acceptance conditions

- AC1: defaults match the documented table [evidence: test:tests/test_settings.py::test_defaults]
- AC2: a missing ORCH_DATABASE_URL raises an error naming it [evidence: test:tests/test_settings.py::test_database_url_required]
- AC3: ORCH_MASTER_KEY_FILE is read and wins over ORCH_MASTER_KEY [evidence: test:tests/test_settings.py::test_master_key_from_file]
- AC4: a master key shorter than 32 bytes is rejected [evidence: test:tests/test_settings.py::test_master_key_too_short_rejected]
- AC5: every settings field's env name appears in the README Configuration table [evidence: test:tests/test_settings.py::test_env_names_documented_in_readme]
- AC6: README documents the configuration [evidence: doc-section:README.md#Configuration]
- AC7: the single namespace, cap and timing fields have the documented defaults and Settings has no clusters_namespace field [evidence: test:tests/test_settings.py::test_single_namespace_cap_and_timing_defaults]
- AC8: ORCH_ALLOWED_CIDRS parses to networks and a bad entry is rejected naming the variable [evidence: test:tests/test_settings.py::test_allowed_cidrs_parsed_and_bad_entry_rejected]
- AC9: the image allowlist always contains agent_image plus ORCH_AGENT_IMAGES [evidence: test:tests/test_settings.py::test_image_allowlist_includes_agent_image]
- AC10: a send timeout above half the dispatching stale cutoff is rejected [evidence: test:tests/test_settings.py::test_send_timeout_must_be_well_below_stale_cutoff]
- AC11: retry_delay_seconds doubles from the base and is capped, and an ambiguous settle below twice the send timeout or a deadline not above the settle is rejected [evidence: test:tests/test_settings.py::test_retry_backoff_and_ambiguity_windows]
- AC12: setting both discard hook variables, or a non-http URL, is rejected naming the variable, and discard_hook() reports the configured one [evidence: test:tests/test_settings.py::test_discard_hook_command_or_url]
- AC13: ORCH_ANY_MCP_REF accepts a vX.Y.Z tag and rejects a branch name [evidence: test:tests/test_settings.py::test_any_mcp_ref_must_be_release_tag]

## Files

- `src/agent_orchestrator/settings.py`
- `tests/test_settings.py`
- `README.md`

## Interfaces

- `agent_orchestrator.settings:Settings` (BaseSettings) with the fields above
- `Settings.allowed_networks()`, `Settings.image_allowlist()`, `Settings.retry_delay_seconds(attempts)`, `Settings.discard_hook()`
- `Settings.require_master_key() -> bytes`, `Settings.require_agent_image() -> str`
- `agent_orchestrator.settings:load_settings() -> Settings`, `DiscardHook`

## Expected outcome

Every process loads one Settings object from `ORCH_*` env; README lists every variable.

## Steps

- Write tests/test_settings.py with the twelve named tests (monkeypatch env). Run `uv run pytest tests/test_settings.py -q` and expect failures.
- Implement settings.py and the README table.
- Rerun and expect `12 passed`, then run `mise run lint`.

## Notes

`namespace` holds both the orchestrator and every agent cluster (D26, the user's answer to Q14). The reconciler keeps off the orchestrator's own objects through the reserved name prefix and the label guard, not through a second namespace.

Contract `agent-orchestrator-settings-env` (owner this epic, consumers this repo's chart and agents-helmfile): renaming a variable later breaks both.

`default_auto_compact_pct` feeds the gauge tick and the rendered `claude.env.claude_autocompact_pct_override` (D13). `any_mcp_ref` must equal the any-mcp pin in pyproject.toml; container-images-ci asserts it. `ORCH_ANY_MCP_REF` is the one place the any-mcp version is pinned for agent pods.
