---
title: plugins orchestration plugin
status: in-progress
repo: any-mcp-tatara-plugins
value: "the orchestrator tools live in the plugins bucket, installable as a source"
files: [orchestration/orchestrator/pyproject.toml, orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py, orchestration/orchestrator/tests/test_orchestrator_plugin.py, orchestration/orchestrator/README.md, pyproject.toml, uv.lock, tests/test_nomenclature.py, tests/test_source_install.py]
verify: "mise run install && mise run test && mise run lint"
depends_on: [plugins-repo-bootstrap, anymcp-release-0-5-0]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1694306
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# plugins orchestration plugin

## Requirement

Goal G1 (epic README), verbatim: "any-mcp contains no platform-specific plugin; the orchestrator plugin lives in any-mcp-tatara-plugins under a topic subdirectory, with the same tools and behaviour." Goal G3, verbatim: "any-mcp-tatara-plugins is a working repo: topic subdirectories, per-plugin packages, tests and lint in CI, documented source notation." User request, verbatim: "Group them into topics in subdirs." Orchestrator design call, verbatim: "first topic `orchestration/` with the orchestrator plugin moved out of any-mcp (OrchestratorPlugin and its tests, same tool names and behaviour incl. the v0.4.0 session tools)". Design D6: distribution `any-mcp-tatara-orchestrator`, module `any_mcp_tatara_orchestrator`, entry point `orchestrator`; plugin packages declare `any-mcp` unversioned as a dependency.

Needs a merged upstream: any-mcp v0.5.0 released (design Rollout R1). Do not start before `git ls-remote https://github.com/szymonrychu/any-mcp refs/tags/v0.5.0` prints a sha.

Scope (any-mcp-tatara-plugins):
- `orchestration/orchestrator/pyproject.toml`: name `any-mcp-tatara-orchestrator`, version `0.1.0`, `requires-python = ">=3.12"`, `dependencies = ["any-mcp"]`, hatchling, `[project.entry-points."any_mcp.plugins"] orchestrator = "any_mcp_tatara_orchestrator:OrchestratorPlugin"`.
- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`: any-mcp v0.4.0's `src/any_mcp/orchestrator.py`, unchanged except the module docstring (no longer "built-in").
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`: any-mcp v0.4.0's `tests/test_orchestrator_plugin.py`, unchanged except its import of the plugin.
- `orchestration/orchestrator/README.md`: the plugin's documentation moved from any-mcp v0.4.0 README "Orchestrator plugin" (config fields, the eleven tools and routes, allow-list note), with the config example using `source: github.com/szymonrychu/any-mcp-tatara-plugins//orchestration/orchestrator?ref=v0.1.0` instead of `plugin: any_mcp.orchestrator:OrchestratorPlugin`.
- Root `pyproject.toml` and `uv.lock`: the dev group gains `any-mcp` pinned to the `v0.5.0` tag through `[tool.uv.sources]`; the plugin is a workspace member.
- `tests/test_nomenclature.py`: any-mcp v0.4.0's guard, its `FILES` the moved plugin source, test and README, `PINNED_NAME` kept.
- `tests/test_source_install.py`: the end-to-end and metadata tests in the acceptance conditions.

## Acceptance conditions

- ac1: the moved plugin tests pass against the package, including the eleven tools and the session tools [evidence: command:uv run --frozen pytest -q orchestration/orchestrator/tests]
- ac2: the moved test file differs from any-mcp v0.4.0 tests/test_orchestrator_plugin.py only in import lines [evidence: command:test "$(curl -fsSL https://raw.githubusercontent.com/szymonrychu/any-mcp/v0.4.0/tests/test_orchestrator_plugin.py | diff - orchestration/orchestrator/tests/test_orchestrator_plugin.py | grep '^[<>]' | grep -cv 'import')" -eq 0]
- ac3: the plugin module differs from any-mcp v0.4.0 src/any_mcp/orchestrator.py only in its module docstring and import lines [evidence: command:test "$(curl -fsSL https://raw.githubusercontent.com/szymonrychu/any-mcp/v0.4.0/src/any_mcp/orchestrator.py | diff - orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py | grep '^[<>]' | grep -v 'import' | grep -cv '^[<>] """')" -eq 0]
- ac4: any-mcp v0.5.0 in a fresh venv installs the plugin through any-mcp plugins install from ./orchestration/orchestrator and from a git::file:// URL of this repository with //orchestration/orchestrator and ?ref=<HEAD sha>, and --list-tools with an orchestrator config lists the eleven orchestrator_ tools [evidence: test:tests/test_source_install.py::test_orchestrator_plugin_installs_from_sources]
- ac5: the distribution is any-mcp-tatara-orchestrator with the single entry point orchestrator = any_mcp_tatara_orchestrator:OrchestratorPlugin and an unversioned any-mcp dependency [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac6: the plugin's files carry no old nomenclature and the guard's file list is exactly tracked [evidence: test:tests/test_nomenclature.py::test_no_old_nomenclature]
- ac7: the plugin README lists the eleven tools with their routes [evidence: command:test "$(grep -c '^| `orchestrator_' orchestration/orchestrator/README.md)" -eq 11]
- ac8: the whole repo's tests and lint pass [evidence: command:mise run test && mise run lint]

## Files

- `orchestration/orchestrator/pyproject.toml`
- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`
- `orchestration/orchestrator/README.md`
- `pyproject.toml`
- `uv.lock`
- `tests/test_nomenclature.py`
- `tests/test_source_install.py`

## Interfaces

- Distribution `any-mcp-tatara-orchestrator` 0.1.0, module `any_mcp_tatara_orchestrator`, `__all__ = ["OrchestratorPlugin"]`, entry point `orchestrator` in group `any_mcp.plugins`.
- The plugin's contract is any-mcp v0.4.0's unchanged: plugin name `orchestrator`, config `OrchestratorConfig` (`base_url`, `token`, `session`, `agent`, `slug`, `max_replicas`, `static`, `hive`, `auto_compact_pct`), eleven `orchestrator_*` tools and their `/agent/v1` routes.
- Source string the orchestrator renders (task orch-render-plugin-sources): `git::https://github.com/szymonrychu/any-mcp-tatara-plugins//orchestration/orchestrator?ref=v0.1.0`.

## Expected outcome

The orchestrator plugin installs from this repo through any-mcp v0.5.0's plugin sources and behaves exactly as it did inside any-mcp v0.4.0.

## Steps

- Red: copy the v0.4.0 test file with the new import, write `tests/test_source_install.py` and `tests/test_nomenclature.py`; run `uv run --frozen pytest -q`: fails on the missing package.
- Green: package files, root dev group and `uv lock`; run the task's verify: passes. Run the ac2 and ac3 diff commands: print nothing beyond import and docstring lines.

## Notes

- Copy from the any-mcp tag, not a working tree: `git -C <any-mcp> show v0.4.0:src/any_mcp/orchestrator.py` and `v0.4.0:tests/test_orchestrator_plugin.py`, and README lines 74-111 for the plugin README.
- Rulings and their pin tests: the plugin declares `any-mcp` unversioned (test_orchestrator_distribution_metadata), so it installs beside any-mcp v0.4.0 in the orchestrator dev env before its pin moves; the nomenclature guard keeps `PINNED_NAME = "test_cluster_key_refused"` (test_no_old_nomenclature).
- The end-to-end test builds a fresh venv (`uv venv --seed`), installs any-mcp v0.5.0 from `git+https://github.com/szymonrychu/any-mcp@v0.5.0`, runs `any-mcp plugins install` for both source forms with `ANY_MCP_CACHE_DIR` in `tmp_path`, then `--list-tools` with an orchestrator entry whose config uses literal values (no network I/O at load: `test_no_io_at_load`). The git form needs the work committed (`git+file`-style HEAD sha, as in any-mcp's release tests).
- Never the word "cluster" outside the pinned test name.
