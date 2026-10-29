---
title: wrapper release 0.4.1
status: todo
repo: claude-code-wrapper
value: "the orchestrator and the agents can run a wrapper whose slash rule matches claude's and whose deny list holds the extension"
files: [pyproject.toml, uv.lock, src/claude_code_wrapper/__init__.py, tests/test_packaging.py]
verify: "uv run pytest tests/test_packaging.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-slash-js-whitespace, wrapper-deny-list-extend]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 629191
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper release 0.4.1

## Requirement

User decision F1 (2026-10-29), verbatim: "F1 (security): both slash parsers adopt claude's JS whitespace set and skip invisible Cc/Cf characters as the architect specifies, including the ESC hole and the Session.probe guard; wrapper release v0.4.1 (tag approved by the user and mx-34 #432; the orchestrator session pushes it after merge) and an orchestrator pin to it; amend D2."

Architect brief, verbatim: "wrapper v0.4.0 is already tagged on origin (e946288), so any wrapper fix needs a new release." and "3. `wrapper-release-0-4-1`: then `orch-wrapper-pin-0-4-1`, touching the same files as `orch-wrapper-pin-0-4-0`."

Design D14 (amended 2026-10-29), verbatim: "wrapper v0.4.0 is already tagged on origin (e946288), so the F1 parser fix and the D5 deny extension ship as wrapper 0.4.1 (task wrapper-release-0-4-1; tag approved by the user and mx-34 #432; the orchestrator session pushes it after merge)".

Scope (mirrors wrapper-release-0-4-0):
- Version `0.4.1` in `pyproject.toml` and `src/claude_code_wrapper/__init__.py`; `uv lock`.
- `tests/test_packaging.py::test_version_matches_pyproject` keeps pyproject, `__version__` and the installed metadata in agreement.
- The wrapper PR of this fix round (wrapper-slash-js-whitespace, wrapper-deny-list-extend, this task) merges to `main` through the normal PR flow before orch-wrapper-pin-0-4-1 starts.
- Release steps, run by the orchestrator session (never a subagent) once that PR is merged to `main`: wait for `build.yaml` to push `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`, push tag `v0.4.1` on the merge commit (`release.yaml` retags `:0.4.1` and `:latest`; irreversible, listed in design.md, approved by the user and mx-34 #432), then amend `orch-wrapper-pin-0-4-1` with the merge sha.
- ac3 ("tag exists on origin") is checked by the orchestrator session after it pushed the tag; the implementer and the reviewer check ac1, ac2 and ac4 only.

## Acceptance conditions

- ac1: pyproject, __version__ and the installed metadata agree [evidence: test:tests/test_packaging.py::test_version_matches_pyproject]
- ac2: the version is 0.4.1 in pyproject and the package [evidence: command:grep -q '^version = "0.4.1"' pyproject.toml && grep -q '__version__ = "0.4.1"' src/claude_code_wrapper/__init__.py]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.4.1 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.4.1)"]
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
