---
title: Land outcomes
status: todo
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
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
