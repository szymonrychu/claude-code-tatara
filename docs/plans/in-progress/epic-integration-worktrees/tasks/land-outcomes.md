---
title: Land outcomes
status: in-progress
repo: workbench
value: "A task already on the epic branch, a rebase re-conflict and a legacy tree each land or fail with a named cause"
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-land-outcomes.test.mjs]
verify: "mise run test && mise run lint"
depends_on: [land-in-run, merge-contained-check]
owns: []
uses: [land-step, contained-check]
model: sonnet
estimate: 50
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/epic-integration-worktrees--land-outcomes
branch: epic-integration-worktrees--land-outcomes
verified_head: ""
run: epic-integration-worktrees
provides: []
acs_for_audit: []
process_gaps: []
---

# Land outcomes

## Requirement

Handle the three land outcomes that land-in-run's land step leaves open: a task already contained in `<epic>`, a rebase re-conflict, and a legacy tree name (interrogate verdict C, H, F; design D4, D13).

- Contained: when merge.py reports `contained: true` with `verification.passed` true, the land step counts the task as landed. Its head is the task tree HEAD, it is listed under `landed`, and it never ends `land-failed`.
- Re-conflict:
  - The land prompt tells the merger why re-conflicts happen: rebasing a dependent onto `<epic>` drops its merge-of-`<epic>` commit, so conflicts that merge had resolved can come back.
  - The merger resolves a conflicted file only when the resolution is unambiguous: both sides carry the same change, or one side's hunk is exactly the dependency text already on `<epic>`. It then commits in the task tree, reruns the task verify there, and reruns merge.py once.
  - Otherwise it aborts the rebase and returns `landed: false` with `conflict` listing every conflicting file. The task ends `land-failed`, and the escalation names those files.
- Legacy name: the `--name` passed to merge.py is the task's recorded worktree name: the last path component of `t.worktree`, without the `/<repo>` suffix. So a legacy `<epic>--<id>` tree recorded before the upgrade lands through the same step.
- Every new test title is a single kebab token (refRunners `--test-name-pattern {name}`).

## Acceptance conditions

- AC1: a task already contained in the epic branch with a passing verify is landed, never land-failed [evidence: test:plugins/workbench/workflows/tests/plan-execute-land-outcomes.test.mjs::land-contained-task-counts-as-landed]
- AC2: the land prompt tells the merger to resolve unambiguous re-conflicts from a dropped merge commit and otherwise name the files [evidence: test:plugins/workbench/workflows/tests/plan-execute-land-outcomes.test.mjs::land-prompt-resolves-rebase-reconflicts]
- AC3: an unresolved conflict escalates the task as land-failed naming every conflicting file [evidence: test:plugins/workbench/workflows/tests/plan-execute-land-outcomes.test.mjs::land-conflict-escalation-names-files]
- AC4: a legacy double-hyphen tree lands with its recorded name [evidence: test:plugins/workbench/workflows/tests/plan-execute-land-outcomes.test.mjs::land-uses-recorded-legacy-tree-name]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-land-outcomes.test.mjs`

## Interfaces

- Uses the `land-step` part (land-in-run) and merge.py's `contained`, `containedBy` and `verification` return fields (the `contained-check` part).
- Changes the land prompt and the land-result handling in plan-execute.js; no new args.

## Expected outcome

A land never fails merely because the task is already on `<epic>`; a rebase re-conflict is either resolved unambiguously and reverified or escalated with the files named; a task recorded on a legacy `<epic>--<id>` tree lands like any other.

## Steps

- Red: write `plugins/workbench/workflows/tests/plan-execute-land-outcomes.test.mjs` on `workflows/tests/harness.mjs` with the four cases; run `cd plugins/workbench && node --test workflows/tests/plan-execute-land-outcomes.test.mjs`; expect failures.
- Green: handle `contained`, extend the land prompt, take `--name` from the recorded worktree.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`, then `mise run test && mise run lint` from the root.

## Notes

- The recorded worktree is `t.worktree` from the args; strip a trailing `/<repo>` (the same tail rule as plan-execute-epic-names) before taking the last component.
- The merger reruns the task verify in the task tree after a conflict fix before rerunning merge.py, or the commit guard fires once on the stale record (land-in-run Notes).

- 2026-10-21 run epic-integration-worktrees: dependency-failed on land-in-run
