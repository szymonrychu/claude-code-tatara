---
title: orch render plugin sources
status: in-progress
repo: agents-orchestrator
value: "agent pods install the orchestrator plugin from the plugins repo and each session's extra sources"
files: [src/agents_orchestrator/k8s/on_start.py, tests/test_on_start.py, tests/test_render.py, tests/golden/session_single.yaml, tests/golden/session_two_peers.yaml, tests/e2e/test_e2e_kind.py, README.md, MEMORY.md]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_on_start.py tests/test_render.py && mise run lint"
depends_on: [orch-any-mcp-sources-spec]
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

# orch render plugin sources

## Requirement

Goal G4 (epic README), verbatim: "agents-orchestrator renders the orchestrator plugin from the plugins repo at a pinned ref and accepts a list of extra plugin sources per preset and session, installed in agent pods." Goal G6, verbatim: "Deployed through agents-helmfile; agent sessions still get the orchestrator tools." Design D7, verbatim: "The reserved entry keeps name, namespace, allow and config, and replaces `plugin` with `source: git::<repo>//orchestration/orchestrator?ref=<ref>`. The onStart script, after writing the config, runs `/opt/any-mcp/bin/any-mcp plugins install --config /opt/any-mcp/etc/any-mcp.yaml` before `--help`." Design D8, verbatim: "each source renders as the plugin entry `{name, source}` ... Rendered after the base config's entries and before the reserved entry."

Scope (agents-orchestrator):
- `src/agents_orchestrator/k8s/on_start.py`: `PLUGIN_CLASS` goes; the reserved entry carries `source` built from `settings.any_mcp_plugins_repo` and `settings.any_mcp_plugins_ref`; `any_mcp_config` appends one `{name: source_plugin_name(s), source: s}` per `spec.any_mcp_sources` entry after the base entries and before the reserved entry (also when the reserved entry is omitted); `render_on_start` runs the install line after the heredoc and before `--help`, on every run (not only when `.ref` changes).
- Tests no longer accurate because the reserved entry is now a source (design D7): the tests of `tests/test_on_start.py` that pin the entry's `plugin` value (`test_hive_entry_and_allow`, the alone-session entry test, `test_user_orchestrator_entry_replaced`) assert the `source` instead; `tests/test_render.py` gains the install-line and hash tests.
- `tests/golden/session_single.yaml`, `tests/golden/session_two_peers.yaml`: regenerated (`UPDATE_GOLDEN=1`).
- `tests/e2e/test_e2e_kind.py`: the on-start assertions expect the orchestrator entry's `source` and that `/opt/any-mcp/bin/pip show any-mcp-tatara-orchestrator` succeeds in a session pod.
- `README.md`: the onStart and any-mcp sections describe the source install and `any_mcp_sources` rendering.
- `MEMORY.md`: a dated entry: the reserved plugin comes from the plugins repo at a pinned tag, installed by `any-mcp plugins install` in onStart, with the why.

## Acceptance conditions

- ac1: the reserved entry, for every session that rendered it before, has source git::<plugins repo>//orchestration/orchestrator?ref=<plugins ref> and no plugin key, keeps name, namespace, allow and config, and validates under the installed any-mcp [evidence: test:tests/test_on_start.py::test_reserved_entry_is_plugins_repo_source]
- ac2: each any_mcp_sources entry renders as name and source after the base config's entries and before the reserved entry, also when the reserved entry is omitted [evidence: test:tests/test_on_start.py::test_any_mcp_sources_rendered]
- ac3: the onStart script runs any-mcp plugins install --config with the config path after writing the config and before --help, on every run [evidence: test:tests/test_render.py::test_on_start_installs_plugin_sources]
- ac4: a different ORCH_ANY_MCP_PLUGINS_REF or any_mcp_sources changes the config hash [evidence: test:tests/test_render.py::test_config_hash_follows_plugin_sources]
- ac5: the onStart, render, README and nomenclature tests pass with the regenerated goldens [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_on_start.py tests/test_render.py tests/test_readme_api.py tests/test_nomenclature.py]
- ac6: the kind e2e module still collects with the source assertions (it runs in CI through mise run test:e2e) [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q --collect-only -m e2e tests/e2e/test_e2e_kind.py]
- ac7: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/k8s/on_start.py`
- `tests/test_on_start.py`
- `tests/test_render.py`
- `tests/golden/session_single.yaml`
- `tests/golden/session_two_peers.yaml`
- `tests/e2e/test_e2e_kind.py`
- `README.md`
- `MEMORY.md`

## Interfaces

- `k8s/on_start.py`: reserved entry `{"name": "orchestrator", "namespace": "orchestrator", "source": f"git::{settings.any_mcp_plugins_repo}//orchestration/orchestrator?ref={settings.any_mcp_plugins_ref}", "allow": ..., "config": ...}`; user source entries `{"name": source_plugin_name(s), "source": s}`.
- onStart script order: install any-mcp when `.ref` differs, write the config heredoc, `/opt/any-mcp/bin/any-mcp plugins install --config /opt/any-mcp/etc/any-mcp.yaml`, `/opt/any-mcp/bin/any-mcp --help >/dev/null`.
- Unchanged: `RESERVED_PLUGIN`, `main_agent_only_tools = ["mcp__any-mcp__orchestrator_*"]`, the any-mcp MCP server command, `on_error: deny`.

## Expected outcome

Every agent pod installs the orchestrator plugin from the plugins repo at the pinned tag plus the session's extra sources before claude starts, and its leader sees the same orchestrator tools as before.

## Steps

- Red: write `test_reserved_entry_is_plugins_repo_source`, `test_any_mcp_sources_rendered`, `test_on_start_installs_plugin_sources`, `test_config_hash_follows_plugin_sources`, and update the inaccurate entry assertions named in the Requirement; run `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_on_start.py tests/test_render.py`: fails.
- Green: on_start.py; regenerate goldens with `UPDATE_GOLDEN=1`; update the e2e assertions; run the task's verify: passes. README and MEMORY; run ac5, ac6, ac7: pass.

## Notes

- Rulings and their pin tests: the install line runs on every onStart run, not only on a new any-mcp ref (test_on_start_installs_plugin_sources: the stub `any-mcp` logs `plugins install` on the second run too); source entries sit before the reserved entry (test_any_mcp_sources_rendered); the reserved entry exists for exactly the sessions it did before (test_reserved_entry_is_plugins_repo_source, both alone and hive).
- The `test_render.py` stub `python3 -m venv` writes fake `pip` and `any-mcp` scripts that log their argv: extend the existing pattern.
- An install failure fails the onStart hook, which blocks the session (`on_error: deny`): that is the intended visible failure (design D4).
- The kind e2e runs in CI (`mise run test:e2e`); locally ac6 only proves it collects.
- Orchestrator tests need Docker (testcontainers) and `VIRTUAL_ENV` unset; recreate a stale `.venv` with `uv sync`. Never the word "cluster" in new text.
