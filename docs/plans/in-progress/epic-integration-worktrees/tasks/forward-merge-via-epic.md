---
title: Forward merge via epic
status: done
repo: workbench
value: "A remediated dependency reaches its dependents through the epic branch, never around it"
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs]
verify: "cd plugins/workbench && bash scripts/run-tests.sh --only workflows && cd ../.. && mise run lint"
depends_on: [fork-point-diffs]
owns: []
uses: [land-step, fork-point]
model: sonnet
estimate: 65
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/epic-integration-worktrees--forward-merge-via-epic
branch: epic-integration-worktrees--forward-merge-via-epic
verified_head: 7624d1d036f51b01d9c806215f24a9169fd1738c
run: epic-integration-worktrees
provides: []
acs_for_audit: [AC3]
process_gaps: []
---

# Forward merge via epic

## Requirement

Route forward merges of a remediated dependency through the epic branch (design D4, D14; interrogate verdict C, G).

- In landing mode (`args.epic` and `args.mainCheckout` set), `forwardMerge` first lands a remediated dependency R again through the land step: R is rebased onto `<epic>`, `<epic>` is fast-forwarded, and R's verify runs in the integration tree. Each live same-repo dependent D then merges `<epic>` (`mergeCommand(d, <baseRef>)`) instead of R's branch, re-verifies, and is landed again through the land step.
- `forwardMerged` entries record `branch: <epic>`.
- If R's landing fails, R ends `land-failed` and no dependent is merged. If a dependent's merge or verify fails, it ends `forward-merge-failed` as today.
- A dependent whose tip is already contained in `<epic>` after the merge, with nothing new to land, is landed again through the contained path: merge.py runs its verify in the integration tree and the dependent counts as landed. It never ends `land-failed` (verdict C).
- The re-verify, and any re-review, of a relanded dependency or dependent diffs from its fork point (`diffBase(t)` from fork-point-diffs), never from `merge-base(HEAD, <epic>)`, which is empty once landed (verdict G).
- Outside landing mode `forwardMerge` is unchanged.
- Tests: added cases in `plan-execute-forward-merge.test.mjs`; the existing cases stay unchanged and green.

## Acceptance conditions

- AC1: a remediated dependency is landed again before its dependents merge the epic branch [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-relands-then-merges-epic]
- AC2: a dependent merges the epic branch, not the dependency branch, and is landed again [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-dependent-merges-epic-and-relands]
- AC3: a failed landing of the remediated dependency merges no dependent [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-land-failure-stops-dependents]
- AC4: outside landing mode forward merges use the dependency branch as today [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-unchanged-without-landing]
- AC5: a dependent whose tip is already in the epic branch is relanded as contained, never land-failed [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-dependent-already-in-epic-not-land-failed]
- AC6: the forward-merge re-verify of a landed task diffs from its fork point [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-reverify-diffs-from-fork-point]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs`

## Interfaces

- Uses the `land-step` part from land-in-run and the `fork-point` part from fork-point-diffs; changes `forwardMerge(latest, remediated)` and `mergePrompt(d, impl, branch)` callers.

## Expected outcome

A remediation never leaves the integration branch behind a dependent: the dependency lands again first, and every dependent rebuilds on the updated `<epic>`.

## Steps

- Red: add the six cases to `plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs`; run `cd plugins/workbench && node --test workflows/tests/plan-execute-forward-merge.test.mjs`; expect the five landing-mode cases to fail.
- Green: branch `forwardMerge` on landing mode.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`, then `mise run test && mise run lint` from the root.

## Ruling

- 2026-10-21 accepted: run 4: fork-point-record, docs-worktree-refs clean; forward-merge-via-epic accepted (gate-repeat on the same false-positive parking flag at plan-execute.js:2115, verified 7624d1d); run 3 tasks landed on main f2e2131

## Notes

- Epic runs default to `audit: 'off'`, so forward merges in epic runs happen only when an audit runs; the tests set `audit: 'run'`.

- 2026-10-21 run epic-integration-worktrees: dependency-failed on fork-point-diffs
