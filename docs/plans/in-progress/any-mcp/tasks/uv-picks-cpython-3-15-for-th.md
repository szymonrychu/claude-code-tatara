---
title: "uv picks CPython 3.15 for the .venv even though mise.toml pins python 3.12. There is no .python-version file and requires-python is >=3.12, so tests run on 3.15 rather than the 3.12 the agent image ships."
status: todo
repo: any-mcp
value: A test environment that differs from the target image can hide 3.12-only failures.
files: []
verify: ""
depends_on: []
owns: []
uses: []
model: ""
estimate: ""
estimate_by: ""
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# uv picks CPython 3.15 for the .venv even though mise.toml pins python 3.12. There is no .python-version file and requires-python is >=3.12, so tests run on 3.15 rather than the 3.12 the agent image ships.

## Requirement

uv picks CPython 3.15 for the .venv even though mise.toml pins python 3.12. There is no .python-version file and requires-python is >=3.12, so tests run on 3.15 rather than the 3.12 the agent image ships.

Where: pyproject.toml / mise.toml (scaffold-owned)

Why: A test environment that differs from the target image can hide 3.12-only failures.

## Acceptance conditions

- AC1: uv picks CPython 3.15 for the .venv even though mise.toml pins python 3.12. There is no .python-version file and requires-python is >=3.12, so tests run on 3.15 rather than the 3.12 the agent image ships. at pyproject.toml / mise.toml (scaffold-owned) is resolved [evidence: judgement]

## Files



## Interfaces

Keep the interfaces around pyproject.toml / mise.toml (scaffold-owned) unchanged unless resolving it requires otherwise: uv picks CPython 3.15 for the .venv even though mise.toml pins python 3.12. There is no .python-version file and requires-python is >=3.12, so tests run on 3.15 rather than the 3.12 the agent image ships..

## Expected outcome

uv picks CPython 3.15 for the .venv even though mise.toml pins python 3.12. There is no .python-version file and requires-python is >=3.12, so tests run on 3.15 rather than the 3.12 the agent image ships. at pyproject.toml / mise.toml (scaffold-owned) is resolved, and A test environment that differs from the target image can hide 3.12-only failures. no longer applies.

## Steps

1. Write a failing test that shows: uv picks CPython 3.15 for the .venv even though mise.toml pins python 3.12. There is no .python-version file and requires-python is >=3.12, so tests run on 3.15 rather than the 3.12 the agent image ships..
2. Fix it at pyproject.toml / mise.toml (scaffold-owned).
3. Run the task verify command and confirm it passes.

## Notes

Discovered in task `fastmcp-adapter` during run `any-mcp`.

