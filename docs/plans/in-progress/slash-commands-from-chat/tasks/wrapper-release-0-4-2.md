---
title: wrapper release 0.4.2
status: todo
repo: claude-code-wrapper
value: "the deploy can ship a wrapper whose deny list closes account, cloud and settings commands"
files: [pyproject.toml, uv.lock, src/claude_code_wrapper/__init__.py, tests/test_packaging.py]
verify: "uv run pytest tests/test_packaging.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-deny-list-extend-0-4]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 624640
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper release 0.4.2

## Requirement

User decision PENDING (mx-34 #471 Q1-3, recommended yes to all; tatara #473 confirmed the version v0.4.2). The leader amends this paragraph with the user verbatim answer before the merge; nothing merges or is tagged before it. Questions, verbatim: "1) Deny the account or cloud group too? That means wrapper v0.4.2 (patch, after v0.4.1) before the slash deploy, about 1 h of agent time. Recommended: yes. 2) Also deny mcp, permissions, config and hooks in v0.4.2? Recommended: yes, so that chat cannot rewrite the session's tool and permission settings. 3) Bump the version to wrapper v0.4.2? Live is 0.3.3, v0.4.1 is tagged but not deployed, and v0.4.2 would replace it in the same deploy. Recommended: yes, pending tatara's confirmation."

Scope (mirrors wrapper-release-0-4-1): version `0.4.2` in `pyproject.toml` and `src/claude_code_wrapper/__init__.py`; `uv lock`; `tests/test_packaging.py::test_version_matches_pyproject` keeps them in agreement. The wrapper PR (wrapper-deny-list-extend-0-4 and this task) merges to `main` only after the user answer. Release steps, by the leader session (never a subagent): wait for `build.yaml` to push `claude-code-wrapper:<sha7>`, push tag `v0.4.2` on the merge commit (irreversible; version confirmed by tatara #473, tag only after the user answer), watch `release.yaml`, then amend orch-wrapper-pin-0-4-2 with the merge sha. ac3 is checked by the leader after the tag; the implementer and reviewer check ac1, ac2, ac4.

## Acceptance conditions

- ac1: pyproject, __version__ and the installed metadata agree [evidence: test:tests/test_packaging.py::test_version_matches_pyproject]
- ac2: the version is 0.4.2 in pyproject and the package [evidence: command:grep -q '^version = "0.4.2"' pyproject.toml && grep -q '__version__ = "0.4.2"' src/claude_code_wrapper/__init__.py]
- ac3: (checked by the leader after it pushed the tag) tag v0.4.2 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.4.2)"]
- ac4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

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
