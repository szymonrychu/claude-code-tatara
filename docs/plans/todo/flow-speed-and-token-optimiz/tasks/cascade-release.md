---
title: Cascade release
status: todo
repo: workbench
value: "A medium finding no longer fails every dependent; the run continues and the ruling comes after"
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs]
verify: "cd plugins/workbench && bash scripts/run-tests.sh --only workflows"
depends_on: [review-tiering]
owns: []
uses: [land-step]
model: opus
estimate: 5
actual: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Cascade release

## Requirement

Release dependents of a task whose only open findings are medium (design D8). `plugins/workbench/workflows/plan-execute.js`.

- `mediumOnly(impl, findings)`: verified, not blocked, at least one open finding, and every open finding has severity `medium` and no `gate`.
- `released(d)` in `runTasks` is also true for a mediumOnly result, so its dependents start in this run. In an epic run the task lands on the epic branch like any released task (the land step).
- The mediumOnly task still escalates: it is listed in `escalated` with its reason and findings, its return entry carries `mediumOnly: true`, and its approval status stays `escalated` until a ruling; `finished` is unchanged.
- A high or critical finding, any gate finding, a blocked task or an unverified task never releases dependents through this rule.

## Acceptance conditions

- AC1: a dependency verified with only medium findings releases its dependents in the same run [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs::medium-only-dependency-releases-dependents]
- AC2: the medium-only task still escalates and its return entry carries mediumOnly true [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs::medium-only-task-still-escalates-with-flag]
- AC3: a high or gate finding never releases dependents [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs::high-or-gate-finding-never-releases]
- AC4: an unverified or blocked task with medium findings never releases [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs::unverified-medium-only-never-releases]
- AC5: in an epic run a medium-only task is landed before its dependents start [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs::medium-only-task-lands-in-epic-run]
- AC6: the existing release tests still pass [evidence: command:cd plugins/workbench && node --test workflows/tests/plan-execute-triage-release.test.mjs workflows/tests/plan-execute-process-only.test.mjs]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
