---
title: Medium only hold
status: escalated
repo: workbench
value: A task with open medium findings never lands before the orchestrator rules on it
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs]
verify: "cd plugins/workbench && node --test workflows/tests/plan-execute-medium-release.test.mjs && bash scripts/run-tests.sh --only workflows"
depends_on: [audit-context-and-models, review-tiering, triage-one-call, flow-docs-update, cache-probe, cache-prefix-change, shell-quote-refs]
owns: []
uses: []
model: sonnet
estimate: 5
actual: 4
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/flow-speed-and-token-optimiz--medium-only-hold
branch: flow-speed-and-token-optimiz--medium-only-hold
verified_head: 6fe6d7ba001735aa25a4bf1aa9d8f55d1b9d9931
run: flow-speed-and-token-optimiz
provides: []
acs_for_audit: [AC1, AC2, AC3]
process_gaps: []
estimate_by: formula
actual_roles: "impl 1, verify 1, review 1, fix 1, false-finding 1"
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

## Ruling

- 2026-10-22 rejected: Fix round (orchestrator, 2026-10-22). The parking flags at plan-execute.js:859,869,2228,2257,2258 are dismissed: they describe current behaviour. One real high finding to fix: mediumHeldDep (plan-execute.js:871-875) checks only the dependency's own mediumOnly flag. In a chain a(held mediumOnly) -> b(clean, released via behindHeld, unlanded) -> c, c is told to merge the epic branch carrying landed b, but neither a nor b is on it, so c builds without b's code. mergedDependencyBranches (:889) has the same gap. Make the hold transitive: a dependency counts as held when it, or any dependency it was released behind, is held and unlanded. A dependent then merges the task branches of every such unlanded ancestor and never relies on the epic branch for them. Add a test for the two-deep chain a -> b -> c, plus a three-deep one if cheap. Keep the existing seven medium-release tests green.

- 2026-10-22 accepted: Accepted 2026-10-22: verified (9/9 medium-release tests incl. transitive chains, workflows 571); open flags are parking-wording false positives on behaviour-describing comments. Landed on main.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
