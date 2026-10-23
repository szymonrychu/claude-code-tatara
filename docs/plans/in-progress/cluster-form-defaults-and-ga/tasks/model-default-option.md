---
title: model default option
status: todo
repo: agent-orchestrator
value: editing a cluster with no model shows its real value
files: [frontend/src/clusters/ClusterForm.tsx, frontend/src/clusters/ClusterForm.test.tsx]
verify: "cd frontend && npx vitest run src/clusters && npm run lint"
depends_on: []
owns: []
uses: []
model: sonnet
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# model default option

## Requirement

ClusterForm.tsx: the Model select gets an empty "default" option like Effort, so an edited cluster with a null model shows that option instead of a blank select; the create form still preselects meta.defaults.model.

## Acceptance conditions

- AC1: Model select offers an empty default option and an edited cluster with a null model shows it [evidence: command:cd frontend && npx vitest run src/clusters/ClusterForm.test.tsx]

## Files

- `frontend/src/clusters/ClusterForm.tsx`
- `frontend/src/clusters/ClusterForm.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
