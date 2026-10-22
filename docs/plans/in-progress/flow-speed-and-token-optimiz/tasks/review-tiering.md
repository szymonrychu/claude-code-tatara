---
title: Review tiering
status: done
repo: workbench
value: "Reviews run where they can find something: settled doc and test diffs skip, light fixes get re-read"
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-tier-scope.test.mjs, plugins/workbench/workflows/tests/plan-execute-tier.test.mjs, plugins/workbench/workflows/tests/plan-execute-gate-only-rounds.test.mjs]
verify: "cd plugins/workbench && bash scripts/run-tests.sh --only workflows"
depends_on: [gate-provenance]
owns: []
uses: []
model: sonnet
estimate: 6
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/flow-speed-and-token-optimiz--review-tiering
branch: flow-speed-and-token-optimiz--review-tiering
verified_head: e621a7d184cfee12ee4dd472fb3d83eb299fd325
run: flow-speed-and-token-optimiz
provides: []
acs_for_audit: []
process_gaps: ["The independent 'TDD skipped' finding is answered by a red/green run I did on a scratch copy outside the tree. With plan-execute.js at 2050fa1^ (before the feature), plan-execute-tier-scope.test.mjs gave 'ℹ pass 5, ℹ fail 5'. The five failures were first-verify-passes-the-requirement, doc-only-diff-with-acs-met-skips-review, test-only-diff-with-acs-met-skips-review, light-fix-to-reviewer-findings-gets-scoped-re-review, and the light-tier scoped-re-review findings test. With plan-execute.js at HEAD the same file gave 'ℹ pass 10, ℹ fail 0'. This output belongs in tests.red and verification.evidence. The feature and its tests landed in one commit (2050fa1), so git history alone does not show the red step.", "TDD skipped without a listed exception; prove the tests catch the change - commit first, then for each changed non-test file: git show <merge-base>:<path> > <path>; run the test (must fail); git show HEAD:<path> > <path>; run again (must pass); paste both tails into tests.red and verification.evidence"]
estimate_by: formula
---

# Review tiering

## Requirement

Make review tiers see the task and skip reviews that add nothing (design D9). `plugins/workbench/workflows/plan-execute.js`.

- verifyPrompt passes `--requirement <shq(t.requirement)>` on every verify that runs the tier call (the first verify of a task), so the tier hint sees the requirement instead of an empty string.
- `reviewTier`: `skip` also applies when every changed file is a doc (`*.md`) or every changed file is a test file (`TEST_FILE_RE`), every AC is met with test, symbol, command or doc-section evidence, the verifier reported no findings, and no changed path matches `RISK_PATH`, whatever the diff size. An explicit `review` value still wins; the verifier's tierHint can still raise the tier.
- Light tier: when a light-tier fixer changed files to fix reviewer findings (the files named by reviewer findings, not gate findings), the loop runs one scoped re-review (effort medium) of the diff `prev..head` over only those files before the task settles. Its findings follow the light rule: one fixer and its verifier, no further review.
- A changed path matching RISK_PATH keeps tier `full`, including doc-only and test-only diffs.

## Acceptance conditions

- AC1: the first verify passes the task requirement to verify-task [evidence: test:plugins/workbench/workflows/tests/plan-execute-tier-scope.test.mjs::first-verify-passes-the-requirement]
- AC2: a doc-only diff with every AC met skips review [evidence: test:plugins/workbench/workflows/tests/plan-execute-tier-scope.test.mjs::doc-only-diff-with-acs-met-skips-review]
- AC3: a test-only diff with every AC met skips review [evidence: test:plugins/workbench/workflows/tests/plan-execute-tier-scope.test.mjs::test-only-diff-with-acs-met-skips-review]
- AC4: a doc-only diff on a RISK_PATH stays full [evidence: test:plugins/workbench/workflows/tests/plan-execute-tier-scope.test.mjs::risk-path-doc-diff-stays-full]
- AC5: a light-tier fix to reviewer findings gets one scoped re-review of those files [evidence: test:plugins/workbench/workflows/tests/plan-execute-tier-scope.test.mjs::light-fix-to-reviewer-findings-gets-scoped-re-review]
- AC6: the existing tier and gate-only round tests still pass [evidence: command:cd plugins/workbench && node --test workflows/tests/plan-execute-tier.test.mjs workflows/tests/plan-execute-gate-only-rounds.test.mjs]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-tier-scope.test.mjs`
- `plugins/workbench/workflows/tests/plan-execute-tier.test.mjs`
- `plugins/workbench/workflows/tests/plan-execute-gate-only-rounds.test.mjs`

## Interfaces

- `reviewTier(t, impl, v, pre)` and the light branch of `reviewUntilClean` in plan-execute.js; verify-task's existing `--requirement` flag.

## Expected outcome

About a third of first reviews are skipped where the evidence already settles the task, and a light-tier fix is never left unreviewed.

## Steps

- Red: write `workflows/tests/plan-execute-tier-scope.test.mjs` with AC1-AC5; run `cd plugins/workbench && node --test workflows/tests/plan-execute-tier-scope.test.mjs`; expect failures.
- Green: the flag, the skip rule, the scoped re-review; update `plan-execute-tier.test.mjs` and `plan-execute-gate-only-rounds.test.mjs` where they pinned the old rule.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`; expect all green.

## Notes

- Today `changedOutside` (plan-execute.js) counts reviewer-finding files as named, so a light-tier fix to them is never re-reviewed (brief flow map section 1).
- `--requirement` is never passed today, so the tier classifier sees "" (verify-task.py `--requirement`).
