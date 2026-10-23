---
title: AC3 cannot pass until db-release and orchestrator-release are merged into the epic branch
status: todo
repo: agents-helmfile
value: "`releases: []` on the epic branch makes `helmfile build` exit 3. Re-verify AC3 on the integrated branch."
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

# AC3 cannot pass until db-release and orchestrator-release are merged into the epic branch

## Requirement

AC3 cannot pass until db-release and orchestrator-release are merged into the epic branch

Where: 

Why: `releases: []` on the epic branch makes `helmfile build` exit 3. Re-verify AC3 on the integrated branch.

## Acceptance conditions

- AC1: AC3 cannot pass until db-release and orchestrator-release are merged into the epic branch at the place the run named is resolved [evidence: judgement]

## Files



## Interfaces

Keep the interfaces around the finding unchanged unless resolving it requires otherwise: AC3 cannot pass until db-release and orchestrator-release are merged into the epic branch.

## Expected outcome

AC3 cannot pass until db-release and orchestrator-release are merged into the epic branch at the place the run named is resolved, and `releases: []` on the epic branch makes `helmfile build` exit 3. Re-verify AC3 on the integrated branch. no longer applies.

## Steps

1. Write a failing test that shows: AC3 cannot pass until db-release and orchestrator-release are merged into the epic branch.
2. Fix it at the place named above.
3. Run the task verify command and confirm it passes.

## Notes

Discovered in task `hook-missing-namespace` during run `agents-helmfile`.

