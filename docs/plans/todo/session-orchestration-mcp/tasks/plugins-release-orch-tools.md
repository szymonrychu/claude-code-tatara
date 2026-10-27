---
title: plugins release orch tools
status: todo
repo: any-mcp-tatara-plugins
value: the orchestration tools ship as a plugins release tag the orchestrator can pin
files: [orchestration/orchestrator/pyproject.toml, uv.lock, orchestration/orchestrator/README.md, tests/test_source_install.py]
verify: "uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint"
depends_on: [plugin-orchestration-tools]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# plugins release orch tools

## Requirement

README Goal G7, verbatim: "The plugin release, orchestrator pin, agents-helmfile values and live applies ship it, and a live smoke from a flagged throwaway session proves create, edit and delete of a preset, a session and a schedule, the refusals and the audit rows, leaving nothing behind."

Design D11, verbatim: "The release is the next minor after the version hive-decoupling leaves pinned."

Design Constraints, verbatim: "plugins release: the next minor after the plugins version hive-decoupling leaves pinned in the orchestrator (`ORCH_ANY_MCP_PLUGINS_REF`) at build time;"

Repo README `## Releases`, verbatim: "Releases are `vX.Y.Z` tags on `main`; pin `?ref=` to a release tag. Nothing is published beyond the tag."

Scope (any-mcp-tatara-plugins):
- Read the pinned version: `ORCH_ANY_MCP_PLUGINS_REF` default in agents-orchestrator main `src/agents_orchestrator/settings.py` (vX.Y.0 after hive-decoupling); the release is vX.(Y+1).0. Never guess it; stop and report if the latest tag on origin is not that pin.
- `orchestration/orchestrator/pyproject.toml`: the new version; `uv lock` updates `uv.lock`.
- `orchestration/orchestrator/README.md`: the example source pins `?ref=` the new tag.
- `tests/test_source_install.py::test_orchestrator_distribution_metadata` is no longer accurate (named): it pins the previous version; it asserts the new one.
- Release step, run by the orchestrator session (never a subagent) once this repo's PR is merged to `main` with green CI: `git tag <tag> <merge sha> && git push origin <tag>` (irreversible, listed in design.md). ac3 is checked by the orchestrator after that push.

## Acceptance conditions

- ac1: the plugin's pyproject and installed metadata say the next minor after the version hive-decoupling pinned (updated) [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac2: the plugin README example pins the new release tag and no older one [evidence: judgement:reviewer checks the ?ref= tag in orchestration/orchestrator/README.md equals v<new version> and no earlier tag remains]
- ac3: (checked by the orchestrator session after it pushed the tag) the new tag exists on origin at the merge commit [evidence: command:git ls-remote --tags origin | grep -q "refs/tags/v$(sed -n 's/^version = .\([0-9.]*\)./\1/p' orchestration/orchestrator/pyproject.toml)$"]
- ac4: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint]

## Files

- `orchestration/orchestrator/pyproject.toml`
- `uv.lock`
- `orchestration/orchestrator/README.md`
- `tests/test_source_install.py`

## Interfaces

- Distribution `any-mcp-tatara-orchestrator` version X.(Y+1).0; git tag `vX.(Y+1).0` on the `main` merge commit.

## Expected outcome

The plugin with the orchestration tools is released as a tag the orchestrator can pin.

## Steps

- Read the orchestrator's pinned plugins ref and the latest tag on origin (`git ls-remote --tags origin`); compute the next minor; stop and report on a mismatch.
- Red: change `test_orchestrator_distribution_metadata` to the new version; run it: fails.
- Green: bump pyproject, `uv lock`, README example; run the task's verify. Quote the summary line.
- After the merge (orchestrator session): wait for CI green on the merge commit, push the tag, check ac3.

## Notes

- Dependency-bump TDD exception for the version values; the metadata test is the guard.
- `tests/test_source_install.py::test_orchestrator_plugin_installs_from_sources` fails in this pod with git 2.39 (`--end-of-options`, environmental per Matrix); CI is its gate.
