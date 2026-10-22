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

Invalid or missing values raise one error naming every bad `ORCH_*` variable. README.md gains `## Configuration`: a table of every variable, its default and the commands that read it. These names are the cross-epic contract `agent-orchestrator-settings-env` consumed by the deploy epic's chart.

## Acceptance conditions

- AC1: defaults match the documented table [evidence: test:tests/test_settings.py::test_defaults]
- AC2: a missing ORCH_DATABASE_URL raises an error naming it [evidence: test:tests/test_settings.py::test_database_url_required]
- AC3: ORCH_MASTER_KEY_FILE is read and wins over ORCH_MASTER_KEY [evidence: test:tests/test_settings.py::test_master_key_from_file]
- AC4: a master key shorter than 32 bytes is rejected [evidence: test:tests/test_settings.py::test_master_key_too_short_rejected]
- AC5: every settings field's env name appears in the README Configuration table [evidence: test:tests/test_settings.py::test_env_names_documented_in_readme]
- AC6: README documents the configuration [evidence: doc-section:README.md#Configuration]

## Files

- `src/agent_orchestrator/settings.py`
- `tests/test_settings.py`
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
