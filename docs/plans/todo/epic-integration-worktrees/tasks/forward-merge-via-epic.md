---
title: Forward merge via epic
status: todo
repo: workbench
value: "A remediated dependency reaches its dependents through the epic branch, never around it"
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs]
verify: "mise run test && mise run lint"
depends_on: [land-in-run]
owns: []
uses: [land-step]
model: sonnet
estimate: 50
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Forward merge via epic

## Requirement

Route forward merges of a remediated dependency through the epic branch (design D4).

- In landing mode (`args.epic` and `args.mainCheckout` set), `forwardMerge` first lands a remediated dependency R again through the land step: R is rebased onto `<epic>`, `<epic>` is fast-forwarded, and R's verify runs in the integration tree. Each live same-repo dependent D then merges `<epic>` (`mergeCommand(d, <baseRef>)`) instead of R's branch, re-verifies, and is landed again through the land step.
- `forwardMerged` entries record `branch: <epic>`.
- If R's landing fails, R ends `land-failed` and no dependent is merged. If a dependent's merge or verify fails, it ends `forward-merge-failed` as today.
- Outside landing mode `forwardMerge` is unchanged.
- Tests: added cases in `plan-execute-forward-merge.test.mjs`; the existing cases stay unchanged and green.

## Acceptance conditions

- AC1: a remediated dependency is landed again before its dependents merge the epic branch [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-relands-then-merges-epic]
- AC2: a dependent merges the epic branch, not the dependency branch, and is landed again [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-dependent-merges-epic-and-relands]
- AC3: a failed landing of the remediated dependency merges no dependent [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-land-failure-stops-dependents]
- AC4: outside landing mode forward merges use the dependency branch as today [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-unchanged-without-landing]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
