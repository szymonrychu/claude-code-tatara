---
title: plugins release 0.5.0
status: todo
repo: any-mcp-tatara-plugins
value: the orchestrator can pin a plugins release whose session_send offers a priority
files: [orchestration/orchestrator/pyproject.toml, uv.lock, orchestration/orchestrator/README.md, tests/test_source_install.py]
verify: "uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint"
depends_on: [plugin-session-send-priority]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 632059
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# plugins release 0.5.0

## Requirement

Design D15, verbatim: "Released as plugins 0.5.0 on top of hive-decoupling's 0.4.0; the orchestrator pins it."

Design D19, verbatim: "claude-code-wrapper 0.5.0, any-mcp-tatara-plugins 0.5.0 and agents-common 0.4.0 are version bumps whose tags the orchestrator session pushes after merge (checked by it, not by the implementer)."

Scope (any-mcp-tatara-plugins): `orchestration/orchestrator/pyproject.toml` (0.4.0 to 0.5.0), `uv.lock`, `orchestration/orchestrator/README.md` (example ref), `tests/test_source_install.py` (the version pin, no longer accurate after the bump).

## Acceptance conditions

- ac1: the plugin's pyproject and installed metadata say 0.5.0 (updated, named) [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac2: the plugin README example pins the new release and no older one [evidence: command:test "$(grep -oE "ref=v[0-9.]+" orchestration/orchestrator/README.md | sort -u)" = "ref=v0.5.0"]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.5.0 exists on origin at the merge commit, on top of v0.4.0 [evidence: command:test -n "$(git ls-remote --tags origin v0.5.0)" && git merge-base --is-ancestor v0.4.0 v0.5.0]
- ac4: the release is built on v0.4.0 [evidence: command:git merge-base --is-ancestor v0.4.0 HEAD]
- ac5: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint]

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
