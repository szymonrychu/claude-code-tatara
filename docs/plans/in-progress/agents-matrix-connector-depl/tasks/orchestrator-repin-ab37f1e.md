---
title: orchestrator repin ab37f1e
status: todo
repo: agents-helmfile
value: the orchestrator cache self-repair ships with the connector apply
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k \"not helmfile_build\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [smoke-matrix-check]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 669602
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orchestrator repin ab37f1e

## Requirement

Re-pin agents-orchestrator to ab37f1e (the cache self-repair, agents-orchestrator PR #20) so it ships with this epic's apply. Request from the main orchestrator session 2026-10-26: it cannot take the task itself because this epic holds helmfile.yaml.gotmpl. Paths are in code/agents-helmfile. Same 3-line shape as helmfile commit 98faa23:

- `helmfile.yaml.gotmpl`: the agents-orchestrator chart version `0.1.0-main.ea1fac7` becomes `0.1.0-main.ab37f1e`.
- `values/agents-orchestrator/common.yaml`: image tag `ea1fac7` becomes `ab37f1e`.
- `tests/test_orchestrator_release.py`: the expected pin is updated first (red), then the two files (green).

One separate commit: `chore(deploy): re-pin orchestrator to ab37f1e (cache self-repair)`. The main session checks the chart is published before it applies.

## Acceptance conditions

- AC1: the orchestrator chart and image are pinned to ab37f1e and the release test expects it [evidence: command:grep -q '0.1.0-main.ab37f1e' helmfile.yaml.gotmpl && grep -q 'ab37f1e' values/agents-orchestrator/common.yaml && uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k "not helmfile_build"]
- AC2: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
