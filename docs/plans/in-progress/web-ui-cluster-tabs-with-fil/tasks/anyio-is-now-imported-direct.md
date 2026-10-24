---
title: "anyio is now imported directly by src/claude_code_wrapper/api/terminals.py but is only a transitive dependency (via starlette/fastapi) in pyproject.toml."
status: todo
repo: claude-code-wrapper
value: "Declaring it directly would make the dependency explicit; pyproject.toml is not in this task's file list."
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

# anyio is now imported directly by src/claude_code_wrapper/api/terminals.py but is only a transitive dependency (via starlette/fastapi) in pyproject.toml.

## Requirement

anyio is now imported directly by src/claude_code_wrapper/api/terminals.py but is only a transitive dependency (via starlette/fastapi) in pyproject.toml.

Where: code/claude-code-wrapper/pyproject.toml dependencies

Why: Declaring it directly would make the dependency explicit; pyproject.toml is not in this task's file list.

## Acceptance conditions

- AC1: anyio is now imported directly by src/claude_code_wrapper/api/terminals.py but is only a transitive dependency (via starlette/fastapi) in pyproject.toml. at code/claude-code-wrapper/pyproject.toml dependencies is resolved [evidence: judgement]

## Files



## Interfaces

Keep the interfaces around code/claude-code-wrapper/pyproject.toml dependencies unchanged unless resolving it requires otherwise: anyio is now imported directly by src/claude_code_wrapper/api/terminals.py but is only a transitive dependency (via starlette/fastapi) in pyproject.toml..

## Expected outcome

anyio is now imported directly by src/claude_code_wrapper/api/terminals.py but is only a transitive dependency (via starlette/fastapi) in pyproject.toml. at code/claude-code-wrapper/pyproject.toml dependencies is resolved, and Declaring it directly would make the dependency explicit; pyproject.toml is not in this task's file list. no longer applies.

## Steps

1. Write a failing test that shows: anyio is now imported directly by src/claude_code_wrapper/api/terminals.py but is only a transitive dependency (via starlette/fastapi) in pyproject.toml..
2. Fix it at code/claude-code-wrapper/pyproject.toml dependencies.
3. Run the task verify command and confirm it passes.

## Notes

Discovered in task `terminal-websocket-api` during run `web-ui-cluster-tabs-with-fil`.

