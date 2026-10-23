---
title: deploy pin d5a7738
status: todo
repo: agents-helmfile
value: the live agents namespace runs the merged form fix
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_versions.py]
verify: "uv run pytest -q -p no:cacheprovider && mise run lint"
depends_on: []
owns: []
uses: []
model: sonnet
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

# deploy pin d5a7738

## Requirement

Deploy agent-orchestrator main d5a7738 (PR #3 merge): set helmfile.yaml.gotmpl release agent-orchestrator chart version to 0.1.0-main.d5a7738 and values/agent-orchestrator/common.yaml image tag to d5a7738. Nothing else changes. Pin the new version in a test so a stale pin is caught (the test asserts the chart version and image tag agree on the same sha7).

## Acceptance conditions

- AC1: chart version and image tag both point at d5a7738 and agree [evidence: command:uv run pytest -q -p no:cacheprovider && mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_versions.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
