---
title: plugins release 0.4.0
status: in-progress
repo: any-mcp-tatara-plugins
value: the activity tool and new handover texts ship as a plugins release the orchestrator can pin
files: [orchestration/orchestrator/pyproject.toml, uv.lock, orchestration/orchestrator/README.md, tests/test_source_install.py]
verify: "uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint"
depends_on: [plugin-activity-tool]
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

# plugins release 0.4.0

## Requirement

README Goal G5, verbatim: "Released and deployed: any-mcp-tatara-plugins next minor tag, orchestrator pins, agents-helmfile bump, apply, a smoke covering the activity route and tool, and a live handoff proof."

Constraint, verbatim: "Plugin release rule: the next minor after the plugins pin the Matrix epic leaves (slash-commands releases v0.2.0, Matrix v0.3.0, so v0.4.0 if nothing else lands). If another release landed first, the release and pin tasks are amended to the next free minor before they start."

Repo README `## Releases`, verbatim: "Releases are `vX.Y.Z` tags on `main`; pin `?ref=` to a release tag. Nothing is published beyond the tag."

Scope (any-mcp-tatara-plugins):
- `orchestration/orchestrator/pyproject.toml`: version `0.4.0`; `uv lock` updates `uv.lock`.
- `orchestration/orchestrator/README.md`: the example source pins `?ref=v0.4.0`.
- `tests/test_source_install.py::test_orchestrator_distribution_metadata` is no longer accurate (named): it pins the previous release version; it asserts `0.4.0`.
- Release step, run by the orchestrator session (never a subagent) once this repo's PR is merged to `main` with green CI: `git tag v0.4.0 <merge sha> && git push origin v0.4.0` (irreversible, listed in design.md). ac3 is checked by the orchestrator after that push.

Builder check settlement 1 (2026-10-27, my call): the build starts only after slash-commands-from-chat and matrix-connector-agent-initi have merged. `v0.4.0` (the plugins release tag, `vX.Y.Z`), `0.4.0` (the same without the `v`) and `0011` (the orchestrator migration number, four digits) in this task are placeholders: orch-activity-route reads the real values from main and replaces them here with `ticket.py amend` before this task starts. No number in this task is assumed; `0.4.0` and `0009` in design.md are only the expectation.

## Acceptance conditions

- ac1: the plugin's pyproject and installed metadata say 0.4.0 (updated, named) [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac2: the plugin README example pins the new release and no older one [evidence: command:test "$(grep -oE "ref=v[0-9.]+" orchestration/orchestrator/README.md | sort -u)" = "ref=v0.4.0"]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.4.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.4.0)"]
- ac4: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint]

## Files

- `orchestration/orchestrator/pyproject.toml`
- `uv.lock`
- `orchestration/orchestrator/README.md`
- `tests/test_source_install.py`

## Interfaces

- Distribution `any-mcp-tatara-orchestrator` version `0.4.0`; git tag `v0.4.0` on the `main` merge commit.

## Expected outcome

The orchestrator plugin with the activity tool is released as tag v0.4.0, so the orchestrator can pin it.

## Steps

- Confirm the newest release tag on origin (`git ls-remote --tags origin 'v*'`) is the one `main` carries and that `v0.4.0` does not exist yet; stop and report otherwise (the task is amended to the next free minor).
- Red: change `test_orchestrator_distribution_metadata` to 0.4.0; run `uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata`: fails.
- Green: bump the plugin pyproject, `uv lock`, the plugin README example; run the task's verify: passes. Quote the summary line.
- After the merge (orchestrator session): wait for CI green on the merge commit, `git tag v0.4.0 <merge sha> && git push origin v0.4.0`, then check ac3.

## Notes

- Dependency-bump TDD exception for the version values; the metadata test is the guard.
- `tests/test_source_install.py::test_orchestrator_plugin_installs_from_sources` fails in agent pods with git 2.39 (`--end-of-options`); CI is the gate for it.

- 2026-10-27 amended: builder check settlement 1: migration number and plugins tag are placeholders until orch-activity-route amends them from main
