---
title: wrapper release 0.3.0
status: todo
repo: claude-code-wrapper
value: the orchestrator and the live agents can run a wrapper that emits compacting
files: [pyproject.toml, uv.lock, src/claude_code_wrapper/__init__.py, tests/test_packaging.py]
verify: "uv run pytest -q tests/test_packaging.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-compacting-event]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 662742
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper release 0.3.0

## Requirement

Goal G6: "released and deployed: wrapper release, orchestrator pins, agents-helmfile bump, apply and a smoke step covering a scale-down below the leader." Design D12: claude-code-wrapper 0.3.0 (version bump, tag `v0.3.0` on the merge commit after the `main` build). Precedent: done epic hive-mode-leadership-handove task wrapper-release-0-2-0.

Scope:
- Version `0.3.0` in `pyproject.toml` and `src/claude_code_wrapper/__init__.py`; `uv lock`.
- `tests/test_packaging.py::test_version_matches_pyproject` keeps pyproject, `__version__` and the installed metadata in agreement.
- Release steps, run by the orchestrator session (never a subagent) once this epic's wrapper PR is merged to `main`: wait for `build.yaml` to push `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`, push tag `v0.3.0` on the merge commit (`release.yaml` retags `:0.3.0` and `:latest`; irreversible, listed in design.md), then amend `orch-wrapper-pin-0-3-0` and `helmfile-deploy-pin` with the merge sha.

Notes: README `### Release`: `release.yaml` fails when the `:<shortsha>` image is missing, so tag only after the main build is green. Dependency bump with no behaviour change: the TDD exception for a version bump applies; the packaging test is the guard.

## Acceptance conditions

- AC1: pyproject, `__version__` and the installed metadata agree [evidence: test:tests/test_packaging.py::test_version_matches_pyproject]
- AC2: the version is 0.3.0 in pyproject and the package [evidence: command:grep -q '^version = "0.3.0"' pyproject.toml && grep -q '__version__ = "0.3.0"' src/claude_code_wrapper/__init__.py]
- AC3: after the merge, tag v0.3.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.3.0)"]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `src/claude_code_wrapper/__init__.py`
- `tests/test_packaging.py`

## Interfaces

See the Requirement and the acceptance conditions above.

## Expected outcome

See the Requirement and the acceptance conditions above.

## Steps

- Bump the version to 0.3.0 in `pyproject.toml` and `src/claude_code_wrapper/__init__.py`, run `uv lock` (dependency-bump exception; the packaging test is the guard); run the task's verify command: passes.
- After the merge (orchestrator session): wait for `build.yaml` green on the merge commit, `git tag v0.3.0 <merge sha> && git push origin v0.3.0`, watch `release.yaml` green, then amend orch-wrapper-pin-0-3-0 and helmfile-deploy-pin with the merge sha.

## Notes

See the Requirement and the acceptance conditions above.
