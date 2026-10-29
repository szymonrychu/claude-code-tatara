---
title: wrapper release 0.5.0
status: todo
repo: claude-code-wrapper
value: the orchestrator can pin a wrapper release that delivers messages mid-turn
files: [pyproject.toml, uv.lock, src/claude_code_wrapper/__init__.py, tests/test_packaging.py]
verify: "uv run pytest tests/test_packaging.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-peer-priority, wrapper-paste-hygiene]
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

# wrapper release 0.5.0

## Requirement

Design D19, verbatim: "claude-code-wrapper 0.5.0, any-mcp-tatara-plugins 0.5.0 and agents-common 0.4.0 are version bumps whose tags the orchestrator session pushes after merge (checked by it, not by the implementer). [...] The wrapper is pinned by its release tag, cut before the orchestrator task (retro file-editor-with-tabs-and-hi: Harbor prunes sha7 tags)."

Design Constraints, verbatim: "This epic therefore takes migration 0012, wrapper 0.5.0, plugins 0.5.0; when a number is taken at build time the task takes the next free one and the orchestrator amends its `files`."

Scope (claude-code-wrapper): `pyproject.toml` and `src/claude_code_wrapper/__init__.py` (0.4.0 from the slash epic to 0.5.0), `uv.lock`, `tests/test_packaging.py` (the version pin, if it names the version).

## Acceptance conditions

- ac1: the version is 0.5.0 in pyproject and the package, and the branch contains the v0.4.0 tag commit [evidence: command:grep -q '^version = "0.5.0"' pyproject.toml && grep -q '__version__ = "0.5.0"' src/claude_code_wrapper/__init__.py && git merge-base --is-ancestor v0.4.0 HEAD]
- ac2: the built wheel installs and reports its version [evidence: test:tests/test_packaging.py::test_wheel_installs_and_ccw_version]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.5.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.5.0)"]
- ac4: packaging tests and lint pass [evidence: command:uv run pytest tests/test_packaging.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `src/claude_code_wrapper/__init__.py`
- `tests/test_packaging.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
