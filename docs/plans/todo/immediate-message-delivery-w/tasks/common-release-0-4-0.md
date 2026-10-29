---
title: common release 0.4.0
status: todo
repo: agents-common
value: "the Matrix connector can pin an agents-common release that exposes the message's turn"
files: [pyproject.toml, uv.lock, tests/test_release.py, README.md]
verify: "uv run pytest tests/test_release.py tests/test_package.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [common-message-turn-id]
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

# common release 0.4.0

## Requirement

Design D19, verbatim: "claude-code-wrapper 0.5.0, any-mcp-tatara-plugins 0.5.0 and agents-common 0.4.0 are version bumps whose tags the orchestrator session pushes after merge (checked by it, not by the implementer). [...] the connector pins agents-common v0.4.0."

Scope (agents-common): `pyproject.toml` (0.3.0 to 0.4.0), `uv.lock`, `tests/test_release.py` (the version and install pins), `README.md` (install line).

## Acceptance conditions

- ac1: pyproject, installed metadata and __version__ agree on 0.4.0 (updated, named) [evidence: test:tests/test_release.py::test_versions_agree]
- ac2: the README install line and the release test pin v0.4.0 and no older tag [evidence: command:grep -q 'agents-common@v0.4.0' README.md && ! grep -q 'agents-common@v0.3.0' README.md && grep -q 'agents-common@v0.4.0' tests/test_release.py]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.4.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.4.0)"]
- ac4: release and package tests and lint pass [evidence: command:uv run pytest tests/test_release.py tests/test_package.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `tests/test_release.py`
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
