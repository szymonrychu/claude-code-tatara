# Epic integration worktrees record

## Summary

Asked: plain `git worktree` only (no harness built-in feature); per-epic integration worktree `<epic>`; task branches `<epic>-<task>` forking from and landing on it; epic merged to main and every tree swept at close.
Shipped: all 21 planned tasks built and landed on main, plus 2 phase-5 remediation tasks (sweep-guard, close-entry-docs): 23 task files, all done. Seven plan-execute runs. All approvals A1-A4, Q1, Q2, V-A..V-I delivered.
Verdict: pass (epic review 2026-10-22). mise run test and mise run lint green on main after every landing; last 2647 assertions.
Not pushed: nothing pushed yet; pushing waits on the user's call on publishing docs/plans.

## Planned vs built

Rounds = review rounds in the run that produced the verified head. Verifier head = `verification.head` from the plan-execute return (pre-landing SHA; landing rebased the branches, so these SHAs are not on main). Red = implementer's own `tests.red`; "none" = no `tests.red` in the return (not a claim that no TDD ran). No `tdd-revert` output is quoted as red evidence.

| Task | Status | Rounds | Files | Verifier head | Verification tail / red |
|---|---|---|---|---|---|
| single-hyphen-names | done | 2 | 3 | 29d1c794f | AC1-AC5 met; red none |
| name-lookup-parsers | done | 3 (run1 round-cap, unknown head) then 1 (run2) | 5 | 97192abc1 | verified in run2; red none |
| slug-collision-guard | done | 3 (run2 gate-repeat, unknown head) then 2 (run3) | 2 | 72b58a399 | 417 passed, lint clean; red: `-k clashing` with fix reverted fails |
| integration-tree-create | done | 2 | 3 | 49daf3ed2 | AC1-AC10 met; red none |
| common-worktree-path-py | done | 2 | 4 | 36c3e7277 | 227 passed targeted; red none (wroteTestFirst false) |
| common-worktree-path-sh | done | 1 | 7 | 4d8582ea7 | AC3, AC4 exit 0; red: test_common.sh 28 passed 1 failed (worktree_path builds expected path) |
| epic-base-wiring | done | 2 | 5 | 7f26e0844 | AC met, tdd failedOnBase/passedOnHead; red: implementer revert-and-pytest on 5 files |
| merge-target-worktree | done | 2 | 2 | 1387f6b2d | green, 379.68 s; red: test_merge_target.py `'ep-t2' == ''` |
| merge-contained-check | done | 2 | 1 | f0bf47ba2 | 7 ACs met; red none |
| plan-execute-epic-names | done | 2 | 2 | 772697036 | green, 399.50 s; red none |
| land-in-run | done | 1 | 5 | 307ed018d | 10 ACs met; red: node --test plan-execute-land etc. |
| land-outcomes | done | 3 (run2 gate-repeat, head "not captured") then 3 (run3) | 2 | c5a069a2c | lint clean; red: 307ed01 plan-execute.js restored, node --test fails |
| forward-merge-via-epic | done (accepted ruling) | 2, stopped gate-repeat, clean=false | 2 | 7624d1d03 | lint clean; red none |
| fork-point-diffs | done (accepted ruling) | 2, stopped gate-repeat, clean=false | 3 | 739bb6544 | 507 passed workflows; red none |
| fork-point-record | done | 2 | 1 | 7fcb7c5ee | 458 passed; red: test_ticket_fork_point KeyError 't-a' |
| epic-close-sweep | done | 2 | 2 | fe94d96b8 | lint clean; red: `-k dry_run` 'big-epic' != 'big-epic-alpha' |
| epic-close-command | done | 3 | 2 | e0debe5f1 | AC1-AC9 met, 471.54 s; red: `-k fresh` assertion mismatch |
| docs-worktree-refs | done | 2 | 2 | cdc965c3d | AC1-AC7 met; red none (no pytest summary captured) |
| docs-flow-phases | done | 3 | 3 | e5270eb16 | exit 0; red none |
| docs-readmes-fallback | done | 2 | 3 | 609061190 | passed true; red none |
| builtin-worktree-guard | done | 2 | 1 | 61bcaef2c | all green, 487.91 s; red none (implementer: tests written with the code, no exception claimed) |
| sweep-guard | done (accepted ruling) | 3, round-cap | 6 | 0c2404510 | hand-run verify-task.py, no --prev-head: exit 0, clean, AC1-AC5 met; red: implementer revert of 3ba5a38 files |
| close-entry-docs | done | 2 | 1 | c6f82cd12 | 518 passed, lint no leaks; red none |

No task is `unverified`: every final row has a `verification.head`. Run 1/2 heads of name-lookup-parsers, slug-collision-guard and land-outcomes were "unknown" / "not captured" and those tasks were re-run until a head was captured. sweep-guard's head comes from the orchestrator's hand-run, not from a clean in-workflow verify (the in-workflow result was head "unknown").
Every verification evidence includes `Installed step "uv sync --frozen" exit 1`, recorded by the script as non-gating.
Process gaps stated by the runs: epic-base-wiring, docs-worktree-refs, builtin-worktree-guard, sweep-guard had no red evidence recorded in the task file; builtin-worktree-guard's implementer states the tests were never seen red.

Approvals (ledger status `approved`; return status from the last run that carried the entry):

| Id | Text | Decisions | Tasks | Status |
|---|---|---|---|---|
| A1 | Skills use git worktree commands, not the harness built-in worktree feature | D1 | builtin-worktree-guard, docs-worktree-refs, docs-readmes-fallback | delivered (run 5) |
| A2 | Epic integration worktree `<epic>`; task branches `<epic>-<task>` fork from and merge back into it; one worktree per task | D2 D3 D4 D8 D10 D13 D14 | 14 tasks (single-hyphen-names ... fork-point-record) | delivered (last carried by run 4; run 5-7 returns omit it, so per-run return says unknown; epic review scope audit found evidence) |
| A3 | Epic worktree merges to main, then all trees cleaned | D5 D6 D9 | merge-target-worktree, epic-close-sweep, land-in-run, docs-flow-phases, merge-contained-check, epic-close-command | delivered (run 5 for docs-flow-phases; scope audit for the rest) |
| A4 | Docs and off-Claude fallback describe the same lifecycle | D7 | docs-flow-phases, docs-worktree-refs, docs-readmes-fallback | delivered (run 5) |
| Q1 | Plan-execute lands each verified task on the epic branch in-run | D11 | land-in-run, forward-merge-via-epic, epic-base-wiring | delivered (scope audit) |
| Q2 | Meta-mode close rebases epic onto main, ff main, suite on main, move done sweeps | D12 | epic-close-sweep, docs-flow-phases | delivered (scope audit) |
| V-A | Merged checks fall back to patch equivalence after rebase | D9 | merge-contained-check, epic-base-wiring, epic-close-sweep, epic-close-command | delivered (scope audit) |
| V-B | merge.py verifies in the rebased task tree before ff; failed verify never advances epic | D6 | merge-target-worktree | delivered (scope audit) |
| V-C | Nothing-to-merge path still verifies; no land-failed for contained dependents | D6 D4 | merge-contained-check, land-outcomes, forward-merge-via-epic | delivered (scope audit) |
| V-D | Close order: land, rebase, suite+lint, ff main, suite on main; record pre-ff SHA | D5 | merge-target-worktree, epic-close-command, docs-flow-phases, docs-readmes-fallback | delivered (scope audit) |
| V-E | MERGE line per done task not in epic; close refuses otherwise | D4 D5 | epic-close-command, docs-flow-phases | delivered (scope audit) |
| V-F | Legacy `<epic>--<task>` epics upgrade via worktrees --integration | D13 | 8 tasks | delivered (scope audit) |
| V-G | Post-landing diffs from the recorded fork point | D14 | fork-point-diffs, fork-point-record, forward-merge-via-epic, docs-worktree-refs | delivered (scope audit) |
| V-H | Land step resolves re-conflicts or fails land-failed naming files | D4 | land-outcomes, merge-target-worktree | delivered (scope audit) |
| V-I | slug-collision-guard acceptance for legacy trees and branches | D3 | slug-collision-guard | delivered (scope audit) |

Run-level approvals returns showed `escalated` for A1/A2 in runs 1-4 (dependency-failed chains, 0 rounds) and `[]` in runs 6-7; the table uses the final state confirmed by the scope audit.

## Deviations and rulings

- fork-point-diffs and forward-merge-via-epic accepted (rulings.json, runs 3 and 4). What: both stopped `gate-repeat`, clean=false, on a parking flag at plan-execute.js:2115 (and run-handback.md:112) from the land-outcomes commit c5a069a. Why: the flagged text "Blocked from release" describes a state; it is not a deferral (verified 739bb65, 7624d1d). Cost if wrong: a real deferral phrase ships in the workflow without a task owning it.
- sweep-guard accepted (run 6). What: round-cap escalation. Why: the verifier crashed on `--prev-head unknown` (verify-task.py exit 2 before JSON); orchestrator hand-ran verify-task.py on 0c24045 (no --prev-head): clean, TDD revert red then green, AC1-AC5 met. Cost if wrong: the independent verify was substituted by the orchestrator's own run.
- Verifies narrowed to component suites after verifier timeouts (full-suite verify killed at 600 s Bash cap, exit 144, in land-outcomes run 2). Commit 5b82386 set a component-suite verify for plan-execute.js and ticket.py tasks. Cost if wrong: cross-component regressions are not caught per task; mitigated by the full suite on main after each landing.
- Task frontmatter `branch` pointed at the `-landed` or `-2` refs at move done (commit 0a93b10), because the installed ticket.py checks ancestry only. Cost if wrong: the field names a marker branch, not the original task branch. Contradiction: docs-flow-phases.md still carries `branch: HEAD`; the other 22 name a ref.
- 16 leftover pre-rebase trees and 29 branches removed after a cherry and subject check showed every commit is on main. Cost if wrong: a commit that differs in patch and subject from main would be lost; the check found none.
- epic-close-command (judged by the implementer, not ruled): `close` passes `suites=False` to merge_back, which the spec's call omitted, to avoid a duplicate suite run. The orchestrator did not overrule it.
- Verifier claims declined by implementers and not reproduced: epic-base-wiring AC2/3/4/6/8/9/10 "not met" (119 tests pass); builtin-worktree-guard AC1-AC3 (16 passed). Cost if wrong: unproven gaps; the scope audit later found AC evidence for all.
- forwardMerged: empty in all seven returns. No forward-merge fix was delivered to a dependent through the workflow.
- Landing: epic-close-command stopped in landing run 2 (deadlock between its test's internal suite-lock and the outer lock), fixed at 02a202b and landed separately (4f0a59c). builtin-worktree-guard failed the suite in landing run 5 (1 failed, 423 passed), needle fix 6e40270, landed ba81b5e.

## Duplicates reconciled

- Two discovered tasks about verifier timeouts dropped (commit 62cc648): epic flow-speed-and-token-optimiz, task verify-task-bounded-runs, covers them.
- Rebases skipped commits already on main: land-outcomes-2 (1e34277, 29d1c79 = 08c26f1, c0ebe65 on main); builtin-worktree-guard-2 (4 duplicate readmes commits).
- slug-collision-guard-2 rebase left a duplicate `ticket_names`; removed in 5b68491. Duplicate `LEGACY_SEP` in ticket.py found by scope audit, removed in 85da43f (close-entry-docs).

## Discovered and blocked

- Collision guard documented in tickets.md before ticket.py had it (run 4, docs-worktree-refs): resolved by slug-collision-guard landing.
- Stale `<epic>--<task>` in plugins/workbench/README.md lines 202, 217 (docs-worktree-refs declined it): covered by docs-readmes-fallback.
- common.sh `worktree_path` / git-worktrees-push still on `.worktrees/` (common-worktree-path-py declined): owned by common-worktree-path-sh, landed.
- Verifier `--prev-head unknown` crash (verify-task.py exit 2) and `--tdd-revert` leaving files reverted: worked around by hand-run; fix not done in this epic. Clearable by the owner of verify-task.py (epic flow-speed-and-token-optimiz).
- Unverified by any agent (cannotVerify): live land agent relaying merge.py `baseBefore` as `base`; merger agent resolving real re-conflicts; close against a real multi-repo component workbench (one component-mode test only). Clearable by a live run on the next epic.
- Security review: MEDIUM Sweep trusted frontmatter branch/worktree (could delete main), LOW unvalidated merge `--name`, LOW unquoted land prompt flags: all fixed in sweep-guard.
- Epic review: direct `merge.py` epic close in worktree-merger.md and worktree-merge SKILL.md bypassed `ticket.py close` gates: fixed in close-entry-docs.
- Pending, user: push; publishing docs/plans undecided.

## Research that changed the plan

Interrogate verdicts V-A..V-I (approvals.json) amended the design after the gate: patch-equivalence fallback, verify-before-ff, close order, MERGE-line landing mode, legacy upgrade path, fork-point diffs, re-conflict handling, legacy-tree acceptance. Phase 5 security review added sweep-guard; epic review and scope audit added close-entry-docs.

## Cost

Agent counts, continuations and wall-clock: unknown (not in the returns given). Audits: scope audit, epic review and security review, one sonnet agent each. Seven plan-execute runs; rounds per task in the table.

README Time: Estimate 1370 min | Actual 0 min | Remaining 0 min. Task files carry `actual: ""` for every task, so actual is unknown.

| Task | Estimate (min) | Actual |
|---|---|---|
| builtin-worktree-guard | 60 | unknown |
| close-entry-docs | 25 | unknown |
| common-worktree-path-py | 40 | unknown |
| common-worktree-path-sh | 45 | unknown |
| docs-flow-phases | 70 | unknown |
| docs-readmes-fallback | 55 | unknown |
| docs-worktree-refs | 55 | unknown |
| epic-base-wiring | 85 | unknown |
| epic-close-command | 85 | unknown |
| epic-close-sweep | 90 | unknown |
| fork-point-diffs | 60 | unknown |
| fork-point-record | 35 | unknown |
| forward-merge-via-epic | 65 | unknown |
| integration-tree-create | 75 | unknown |
| land-in-run | 90 | unknown |
| land-outcomes | 50 | unknown |
| merge-contained-check | 45 | unknown |
| merge-target-worktree | 90 | unknown |
| name-lookup-parsers | 45 | unknown |
| plan-execute-epic-names | 40 | unknown |
| single-hyphen-names | 70 | unknown |
| slug-collision-guard | 50 | unknown |
| sweep-guard | 45 | unknown |

## MRs and deploy

No MR or PR (meta mode, local rebase and fast-forward). Final main HEAD at record time: 400165c. Nothing pushed; push pending the user's call on publishing docs/plans. No deploy.

## Lessons routed to

- Verifier must not crash on `--prev-head unknown` and `--tdd-revert` must not leave the tree dirty: add a test in verify-task.py's suite (mechanical).
- Parking-flag scan matched a state-describing comment twice (plan-execute.js:2115): add a lint/test allowlist case for "Blocked from release" style wording (mechanical).
- Full-suite verify exceeded the 600 s cap: per-task verify must be a component suite; enforce with a check in `ticket.py` task validation that `verify` is not `mise run test` (mechanical; tracked by flow-speed-and-token-optimiz).
- Move done must not rely on ancestry alone after a rebase landing: covered by merge-contained-check; the installed ticket.py predates it, so a version-bump check is the follow-up (mechanical).
- Tests written after code (builtin-worktree-guard, docs tasks) with no red evidence: gate task completion on a non-empty `tests.red` or a named exception in plan-execute (mechanical).
- `branch: HEAD` in docs-flow-phases.md: add a ticket.py lint rejecting `branch` values that are not a real ref (mechanical).
