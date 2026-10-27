---
title: plugins release 0.4.0
status: todo
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
- `tests/test_source_install.py::test_orchestrator_distribution_metadata` is no longer accurate (named): after the Matrix epic it pins `0.3.0`; it asserts `0.4.0`.
- Release step, run by the orchestrator session (never a subagent) once this repo's PR is merged to `main` with green CI: `git tag v0.4.0 <merge sha> && git push origin v0.4.0` (irreversible, listed in design.md). ac3 is checked by the orchestrator after that push.

## Acceptance conditions

- ac1: the plugin's pyproject and installed metadata say 0.4.0 (updated, named) [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac2: the plugin README example pins the new release and no older one [evidence: command:grep -q "ref=v0.4.0" orchestration/orchestrator/README.md && ! grep -qE "ref=v0\.[123]\.0" orchestration/orchestrator/README.md]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.4.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.4.0)"]
- ac4: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint]

## Files

- `orchestration/orchestrator/pyproject.toml`
- `uv.lock`
- `orchestration/orchestrator/README.md`
- `tests/test_source_install.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
