---
title: anymcp remove orchestrator
status: todo
repo: any-mcp
value: any-mcp ships no platform-specific plugin
files: [src/any_mcp/orchestrator.py, tests/test_orchestrator_plugin.py, tests/test_nomenclature.py, tests/test_generic.py, README.md]
verify: "uv run --frozen pytest -q tests/test_generic.py tests/test_docs_links.py && mise run lint"
depends_on: [anymcp-source-plugin-loading]
model: sonnet
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

# anymcp remove orchestrator

## Requirement

Goal G1 (epic README), verbatim: "any-mcp contains no platform-specific plugin; the orchestrator plugin lives in any-mcp-tatara-plugins under a topic subdirectory, with the same tools and behaviour." User request, verbatim: "Make anyMcp generic." Non-goal, verbatim: "No backward-compatibility alias for the removed any_mcp.orchestrator module." Design D5, verbatim: "`src/any_mcp/orchestrator.py` and `tests/test_orchestrator_plugin.py` are deleted with no shim; a retirement test pins their absence through `git ls-files` and that src, examples and docs carry no `/agent/v1`. `tests/test_nomenclature.py` is deleted: it guards exactly those files, and the guard moves with them to the plugins repo. README's "Orchestrator plugin" section is replaced by a "Plugin sources" section pointing at any-mcp-tatara-plugins."

Scope (any-mcp):
- Delete `src/any_mcp/orchestrator.py` and `tests/test_orchestrator_plugin.py` (the plugin and its tests move to any-mcp-tatara-plugins in task plugins-orchestration-plugin).
- Delete `tests/test_nomenclature.py`: no longer accurate, it asserts `git ls-files` returns exactly the two deleted files plus README.md and guards their wording; the guard moves with the files.
- New `tests/test_generic.py`: the retirement and genericity tests in the acceptance conditions.
- `README.md`: remove the "Orchestrator plugin" section; add a "Plugin sources" section with the notation forms (local `./`, `../`, `/`; `git::https://...//subdir?ref=`; `github.com/owner/repo//subdir?ref=`), a `source:` config example, `any-mcp plugins install`, and a pointer to https://github.com/szymonrychu/any-mcp-tatara-plugins for the platform plugins.

## Acceptance conditions

- ac1: src/any_mcp/orchestrator.py, tests/test_orchestrator_plugin.py and tests/test_nomenclature.py are no longer tracked [evidence: test:tests/test_generic.py::test_orchestrator_plugin_retired]
- ac2: no tracked file under src, examples or docs contains /agent/v1, orchestrator or hive [evidence: test:tests/test_generic.py::test_no_platform_names]
- ac3: importing any_mcp.orchestrator raises ModuleNotFoundError (no alias) [evidence: test:tests/test_generic.py::test_no_orchestrator_alias]
- ac4: README has no Orchestrator plugin section and has a Plugin sources section naming the git::, github.com/ and local forms, plugins install and any-mcp-tatara-plugins [evidence: test:tests/test_generic.py::test_readme_plugin_sources_section]
- ac5: the whole any-mcp suite passes without the removed module [evidence: command:mise run test]
- ac6: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/orchestrator.py`
- `tests/test_orchestrator_plugin.py`
- `tests/test_nomenclature.py`
- `tests/test_generic.py`
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
