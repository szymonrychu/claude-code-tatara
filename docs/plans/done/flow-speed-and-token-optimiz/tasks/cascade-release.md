---
title: Cascade release
status: done
repo: workbench
value: "A medium finding no longer fails every dependent; the run continues and the ruling comes after"
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs]
verify: "cd plugins/workbench && bash scripts/run-tests.sh --only workflows"
depends_on: [review-tiering]
model: opus
review: full
verified_head: bae1f364c7672d48a9c8d4e2826d3431f0902c83
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 6
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
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
- AC5: in an epic run a medium-only task releases its dependents and is not landed until a ruling accepts it (D8 as amended 2026-10-22, delivered by medium-only-hold) [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs::medium-only-task-releases-but-does-not-land-in-epic-run]
- AC6: the existing release tests still pass [evidence: command:cd plugins/workbench && node --test workflows/tests/plan-execute-triage-release.test.mjs workflows/tests/plan-execute-process-only.test.mjs]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs`

## Interfaces

- Uses `land-step` (epic integration worktrees): a released task is landed before its dependents begin.
- Return task field `mediumOnly` (boolean), next to `processOnly` and `triageRejected`.

## Expected outcome

One medium finding at the top of the DAG no longer fails every dependent: the run continues and the orchestrator rules on the finding afterwards.

## Steps

- Red: write `workflows/tests/plan-execute-medium-release.test.mjs` with AC1-AC5; run `cd plugins/workbench && node --test workflows/tests/plan-execute-medium-release.test.mjs`; expect failures.
- Green: `mediumOnly`, the `released` rule, the return field.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`; expect all green.

## Notes

- Measured: 19 root escalations caused 183 dependency-failed task-runs; runs 2 and 3 each ran one task and blocked 61 and 60 (brief failure mode 2).
- Severity enum is `critical`, `high`, `medium` (the review schema in plan-execute.js); every script-made gate finding is `high` and carries `gate`.
- A dependent built on a later-fixed dependency is handled by the blocker's forward-merge via the epic branch and its re-verify.
