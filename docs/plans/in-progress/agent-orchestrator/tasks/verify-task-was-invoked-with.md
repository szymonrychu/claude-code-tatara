---
title: "verify-task was invoked with --exclude-ref 'HEAD (worktree agent-orchestrator-cluster-token-derivation, commit dc7d657)', which is a description and not a git ref"
status: todo
repo: agent-orchestrator
value: "The script exits with code 2 before it prints any JSON, so findings 1 and 2 cannot be resolved from the tree"
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

# verify-task was invoked with --exclude-ref 'HEAD (worktree agent-orchestrator-cluster-token-derivation, commit dc7d657)', which is a description and not a git ref

## Requirement

verify-task was invoked with --exclude-ref 'HEAD (worktree agent-orchestrator-cluster-token-derivation, commit dc7d657)', which is a description and not a git ref

Where: workflow harness verify-task invocation

Why: The script exits with code 2 before it prints any JSON, so findings 1 and 2 cannot be resolved from the tree

## Acceptance conditions

- AC1: verify-task was invoked with --exclude-ref 'HEAD (worktree agent-orchestrator-cluster-token-derivation, commit dc7d657)', which is a description and not a git ref at workflow harness verify-task invocation is resolved [evidence: judgement]

## Files



## Interfaces

Keep the interfaces around workflow harness verify-task invocation unchanged unless resolving it requires otherwise: verify-task was invoked with --exclude-ref 'HEAD (worktree agent-orchestrator-cluster-token-derivation, commit dc7d657)', which is a description and not a git ref.

## Expected outcome

verify-task was invoked with --exclude-ref 'HEAD (worktree agent-orchestrator-cluster-token-derivation, commit dc7d657)', which is a description and not a git ref at workflow harness verify-task invocation is resolved, and The script exits with code 2 before it prints any JSON, so findings 1 and 2 cannot be resolved from the tree no longer applies.

## Steps

1. Write a failing test that shows: verify-task was invoked with --exclude-ref 'HEAD (worktree agent-orchestrator-cluster-token-derivation, commit dc7d657)', which is a description and not a git ref.
2. Fix it at workflow harness verify-task invocation.
3. Run the task verify command and confirm it passes.

## Notes

Discovered in task `dispatcher-loop` during run `agent-orchestrator`.

