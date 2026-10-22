---
title: Medium only hold
status: todo
repo: workbench
value: A task with open medium findings never lands before the orchestrator rules on it
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs]
verify: "cd plugins/workbench && node --test workflows/tests/plan-execute-medium-release.test.mjs && bash scripts/run-tests.sh --only workflows"
depends_on: [audit-context-and-models, review-tiering, triage-one-call, flow-docs-update, cache-probe, cache-prefix-change, shell-quote-refs]
owns: []
uses: []
model: sonnet
estimate: ""
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Medium only hold

## Requirement

Epic review finding (2026-10-22): the design's builder check answer says a task released as mediumOnly releases its dependents but does not land on the epic branch until the orchestrator rules; D8's text and the code (plan-execute.js:2249-2252 releasable includes mediumOnly, the landing queue lands every releasable task; :2824-2826) land it. Ruling (orchestrator, 2026-10-22): the builder check answer wins; D8 is amended to match.

Deliver: a mediumOnly task releases its dependents (they merge its task branch, as today) and is NOT landed in-run: it is not queued for landing, the return keeps `mediumOnly: true` and escalates it for a ruling, and it is not reported as landed. A mediumOnly task that is in RULED_ACCEPT lands like any released task.

## Acceptance conditions

- AC1: a mediumOnly task in a landing run starts its dependents and is not landed [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs]
- AC2: a mediumOnly task listed in ruled-accept lands [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs]
- AC3: the return marks the unlanded mediumOnly task escalated with mediumOnly true [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs`

## Interfaces

- `releasable(d)` keeps releasing dependents for mediumOnly; landing eligibility excludes mediumOnly unless RULED_ACCEPT has it.

## Expected outcome

Medium findings never reach the epic branch unruled, while the run still continues past them.

## Steps

1. Add the AC tests and see AC1 fail.
2. Split release from landing eligibility for mediumOnly.
3. Run the verify command.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
