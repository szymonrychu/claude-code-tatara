---
title: "verify-task passes a descriptive string \"HEAD (worktree agent-orchestrator-cluster-token-derivation, commit dc7d657)\" to git merge-base as an exclude ref, so verification fails before running any test."
status: todo
repo: agent-orchestrator
value: "This caused review findings 1 and 2 on a clean, committed tree. The exclude ref should be the bare sha (dc7d657) or a branch name."
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

# verify-task passes a descriptive string "HEAD (worktree agent-orchestrator-cluster-token-derivation, commit dc7d657)" to git merge-base as an exclude ref, so verification fails before running any test.

## Requirement

verify-task passes a descriptive string "HEAD (worktree agent-orchestrator-cluster-token-derivation, commit dc7d657)" to git merge-base as an exclude ref, so verification fails before running any test.

Where: workbench plan-execute verify-task (exclude-ref computation for merged dependency commits)

Why: This caused review findings 1 and 2 on a clean, committed tree. The exclude ref should be the bare sha (dc7d657) or a branch name.

## Acceptance conditions

- AC1: verify-task passes a descriptive string "HEAD (worktree agent-orchestrator-cluster-token-derivation, commit dc7d657)" to git merge-base as an exclude ref, so verification fails before running any test. at workbench plan-execute verify-task (exclude-ref computation for merged dependency commits) is resolved [evidence: judgement]

## Files



## Interfaces

Keep the interfaces around workbench plan-execute verify-task (exclude-ref computation for merged dependency commits) unchanged unless resolving it requires otherwise: verify-task passes a descriptive string "HEAD (worktree agent-orchestrator-cluster-token-derivation, commit dc7d657)" to git merge-base as an exclude ref, so verification fails before running any test..

## Expected outcome

verify-task passes a descriptive string "HEAD (worktree agent-orchestrator-cluster-token-derivation, commit dc7d657)" to git merge-base as an exclude ref, so verification fails before running any test. at workbench plan-execute verify-task (exclude-ref computation for merged dependency commits) is resolved, and This caused review findings 1 and 2 on a clean, committed tree. The exclude ref should be the bare sha (dc7d657) or a branch name. no longer applies.

## Steps

1. Write a failing test that shows: verify-task passes a descriptive string "HEAD (worktree agent-orchestrator-cluster-token-derivation, commit dc7d657)" to git merge-base as an exclude ref, so verification fails before running any test..
2. Fix it at workbench plan-execute verify-task (exclude-ref computation for merged dependency commits).
3. Run the task verify command and confirm it passes.

## Notes

Discovered in task `ingester` during run `agent-orchestrator`.

