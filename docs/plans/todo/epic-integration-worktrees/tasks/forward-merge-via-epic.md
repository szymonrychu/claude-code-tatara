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

- Uses the `land-step` part from land-in-run; changes `forwardMerge(latest, remediated)` and `mergePrompt(d, impl, branch)` callers.

## Expected outcome

A remediation never leaves the integration branch behind a dependent: the dependency lands again first, and every dependent rebuilds on the updated `<epic>`.

## Steps

- Red: add the four cases to `plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs`; run `cd plugins/workbench && node --test workflows/tests/plan-execute-forward-merge.test.mjs`; expect the three landing cases to fail.
- Green: branch `forwardMerge` on landing mode.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`, then `mise run test && mise run lint` from the root.

## Notes

- Epic runs default to `audit: 'off'`, so forward merges in epic runs happen only when an audit runs; the tests set `audit: 'run'`.
