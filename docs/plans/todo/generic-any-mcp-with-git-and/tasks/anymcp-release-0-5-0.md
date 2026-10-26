---
title: anymcp release 0.5.0
status: todo
repo: any-mcp
value: a tagged generic any-mcp release the plugins repo and the orchestrator can pin
files: [pyproject.toml, uv.lock, CHANGELOG.md, README.md, MEMORY.md, tests/test_release.py, tests/test_package.py, tests/test_docs_links.py]
verify: "uv run --frozen pytest -q tests/test_release.py tests/test_package.py tests/test_docs_links.py && mise run lint"
depends_on: [anymcp-source-plugin-loading, anymcp-remove-orchestrator]
model: opus
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# anymcp release 0.5.0

## Requirement

Design D5, verbatim: "Release v0.5.0 (breaking, user's design call) with CHANGELOG, README pins and the version-pinned tests updated as no longer accurate; MEMORY records the reversal of the 2026-10-24 decision." Orchestrator design call, verbatim: "any-mcp: remove orchestrator.py and its tests (no backward compatibility shim), nomenclature/package/docs tests updated as inaccurate, release as a new minor version (0.5.0) with CHANGELOG."

Scope (any-mcp):
- `pyproject.toml` version `0.5.0`; `uv.lock` refreshed.
- `CHANGELOG.md`: `## v0.5.0` on top, a "Breaking:" line naming the removed `any_mcp.orchestrator` and where the plugin now lives (any-mcp-tatara-plugins, `orchestration/orchestrator`), then bullets: plugin sources (`plugins[].source`, the notation forms), `any-mcp plugins install`, `ANY_MCP_CACHE_DIR`, `plugins[].plugin` optional with a source.
- `README.md`: the pinned install lines name `v0.5.0`.
- `MEMORY.md`: a dated entry titled "any-mcp is generic, plugins come from sources" that reverses the 2026-10-24 entry and says why (user request: any-mcp reusable outside this platform; platform plugins live in any-mcp-tatara-plugins).
- Tests no longer accurate because the version moves to 0.5.0: `tests/test_release.py` (`PINNED_LINE`, `test_versions_agree`, `test_wheel_installs_and_reports_version`, `test_uv_tool_install`), `tests/test_package.py::test_version_from_metadata`, `tests/test_docs_links.py::test_readme_install_forms`: each asserts `0.5.0`.
- The tag push is the orchestrator's (design Rollout R1), not this task's.

## Acceptance conditions

- ac1: pyproject, installed metadata, the CHANGELOG top heading and README agree on 0.5.0 [evidence: test:tests/test_release.py::test_versions_agree]
- ac2: any_mcp.__version__ is 0.5.0 [evidence: test:tests/test_package.py::test_version_from_metadata]
- ac3: README install forms name v0.5.0 [evidence: test:tests/test_docs_links.py::test_readme_install_forms]
- ac4: the v0.5.0 CHANGELOG section has a Breaking: line and names any-mcp-tatara-plugins, plugins install and ANY_MCP_CACHE_DIR [evidence: command:s=$(sed -n '/^## v0.5.0/,/^## v0.4.0/p' CHANGELOG.md) && echo "$s" | grep -q '^Breaking:' && echo "$s" | grep -q 'any-mcp-tatara-plugins' && echo "$s" | grep -q 'plugins install' && echo "$s" | grep -q 'ANY_MCP_CACHE_DIR']
- ac5: MEMORY.md records the reversal of the built-in plugin decision [evidence: command:grep -q '^## 20[0-9-]* - any-mcp is generic, plugins come from sources' MEMORY.md]
- ac6: the whole suite passes, including the install-from-committed-HEAD tests [evidence: command:mise run test]
- ac7: lint passes [evidence: command:mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`
- `MEMORY.md`
- `tests/test_release.py`
- `tests/test_package.py`
- `tests/test_docs_links.py`

## Interfaces

- Version `0.5.0` everywhere the release tests pin it; CHANGELOG section `## v0.5.0` (the release workflow extracts it verbatim).

## Expected outcome

The any-mcp tree is ready for the orchestrator to tag `v0.5.0` (Rollout R1): versions agree, CHANGELOG and MEMORY explain the breaking change.

## Steps

- Red: change the pinned versions in the three test files; run `uv run --frozen pytest -q tests/test_release.py tests/test_package.py tests/test_docs_links.py`: fails.
- Green: bump pyproject, `uv lock`, README pins, CHANGELOG, MEMORY; commit, then run `mise run test` (the install tests read the committed HEAD): passes.

## Notes

- `tests/test_release.py` installs from `git+file://ROOT@<HEAD sha>`: commit before running the full suite or those tests see the old tree.
- CHANGELOG style: one or two summary lines with the "Breaking:" prefix, then `- ` bullets wrapped near 100 columns (see v0.3.0).
- MEMORY entries are `## YYYY-MM-DD - title`, newest first.
- The tag push is Rollout R1, not this task.
