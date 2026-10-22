---
title: "The design's 'Left to the builder' section says the FastMCP probe results go into docs/transports.md, but this task's requirement puts them in the adapter module docstring. docs/transports.md was not written here."
status: todo
repo: any-mcp
value: "The docs-reference task should copy the probe results (Tool API, validation bypass, per-era notification paths) from the _fastmcp_adapter.py docstring into docs/transports.md."
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

# The design's 'Left to the builder' section says the FastMCP probe results go into docs/transports.md, but this task's requirement puts them in the adapter module docstring. docs/transports.md was not written here.

## Requirement

The design's 'Left to the builder' section says the FastMCP probe results go into docs/transports.md, but this task's requirement puts them in the adapter module docstring. docs/transports.md was not written here.

Where: docs/transports.md (owned by a docs task)

Why: The docs-reference task should copy the probe results (Tool API, validation bypass, per-era notification paths) from the _fastmcp_adapter.py docstring into docs/transports.md.

## Acceptance conditions

- AC1: The design's 'Left to the builder' section says the FastMCP probe results go into docs/transports.md, but this task's requirement puts them in the adapter module docstring. docs/transports.md was not written here. at docs/transports.md (owned by a docs task) is resolved [evidence: judgement]

## Files



## Interfaces

Keep the interfaces around docs/transports.md (owned by a docs task) unchanged unless resolving it requires otherwise: The design's 'Left to the builder' section says the FastMCP probe results go into docs/transports.md, but this task's requirement puts them in the adapter module docstring. docs/transports.md was not written here..

## Expected outcome

The design's 'Left to the builder' section says the FastMCP probe results go into docs/transports.md, but this task's requirement puts them in the adapter module docstring. docs/transports.md was not written here. at docs/transports.md (owned by a docs task) is resolved, and The docs-reference task should copy the probe results (Tool API, validation bypass, per-era notification paths) from the _fastmcp_adapter.py docstring into docs/transports.md. no longer applies.

## Steps

1. Write a failing test that shows: The design's 'Left to the builder' section says the FastMCP probe results go into docs/transports.md, but this task's requirement puts them in the adapter module docstring. docs/transports.md was not written here..
2. Fix it at docs/transports.md (owned by a docs task).
3. Run the task verify command and confirm it passes.

## Notes

Discovered in task `fastmcp-adapter` during run `any-mcp`.

