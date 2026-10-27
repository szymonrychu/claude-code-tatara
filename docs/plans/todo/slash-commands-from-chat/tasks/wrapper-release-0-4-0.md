---
title: wrapper release 0.4.0
status: todo
repo: claude-code-wrapper
value: the orchestrator and the agents can run a wrapper that takes any slash command
files: [pyproject.toml, uv.lock, src/claude_code_wrapper/__init__.py, tests/test_packaging.py]
verify: "uv run pytest tests/test_packaging.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-command-docs]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 656326
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper release 0.4.0

## Requirement

Design D14, verbatim: "claude-code-wrapper 0.4.0 (version bump, tag `v0.4.0` on the merge commit after the `main` build, run by the orchestrator session), then agents-orchestrator pins that merge commit (pyproject, uv.lock, `e2e/agent-test.Dockerfile`, README Images) and enables `client: ["*"]` in `e2e/agent-test.config.yaml` for the real contract leg and e2e. No agents-helmfile task (user decision 4). Precedent: in-progress epic leader-auto-handover tasks wrapper-release-0-3-0 and orch-wrapper-pin-0-3-0."

User decision, verbatim: "Release and pin flow like done epic leader-auto-handover (wrapper release, orchestrator pin) if the orchestrator needs a new wrapper API".

Scope:
- Version `0.4.0` in `pyproject.toml` and `src/claude_code_wrapper/__init__.py`; `uv lock`.
- `tests/test_packaging.py::test_version_matches_pyproject` keeps pyproject, `__version__` and the installed metadata in agreement.
- Release steps, run by the orchestrator session (never a subagent) once this epic's wrapper PR is merged to `main`: wait for `build.yaml` to push `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`, push tag `v0.4.0` on the merge commit (`release.yaml` retags `:0.4.0` and `:latest`; irreversible, listed in design.md), then amend `orch-wrapper-pin-0-4-0` with the merge sha.

## Acceptance conditions

- ac1: pyproject, __version__ and the installed metadata agree [evidence: test:tests/test_packaging.py::test_version_matches_pyproject]
- ac2: the version is 0.4.0 in pyproject and the package [evidence: command:grep -q '^version = "0.4.0"' pyproject.toml && grep -q '__version__ = "0.4.0"' src/claude_code_wrapper/__init__.py]
- ac3: after the merge, tag v0.4.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.4.0)"]
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
