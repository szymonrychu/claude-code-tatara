# Epic integration worktrees retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| Common worktree path sh | 3 | not recorded | 45 | not recorded | 2250000 | not recorded |
| Plan execute epic names | 3 | not recorded | 40 | not recorded | 2250000 | not recorded |
| Common worktree path py | 3 | not recorded | 40 | not recorded | 2250000 | not recorded |
| Merge target worktree | 8 | not recorded | 90 | not recorded | 6000000 | not recorded |
| Single hyphen names | 5 | not recorded | 70 | not recorded | 3750000 | not recorded |
| Merge contained check | 3 | not recorded | 45 | not recorded | 2250000 | not recorded |
| Name lookup parsers | 3 | not recorded | 45 | 12 | 2250000 | 221162 |
| Integration tree create | 8 | not recorded | 75 | 33 | 6000000 | 689331 |
| Epic base wiring | 8 | not recorded | 85 | 47 | 6000000 | 869403 |
| Land in run | 8 | not recorded | 90 | 9 | 6000000 | 581793 |
| Epic close sweep | 8 | not recorded | 90 | 23 | 6000000 | 1097360 |
| Epic close command | 8 | not recorded | 85 | 48 | 6000000 | 3239047 |
| Land outcomes | 5 | not recorded | 50 | 133 | 3750000 | 2388965 |
| Fork point diffs | 5 | not recorded | 60 | 6 | 3750000 | 1348080 |
| Slug collision guard | 5 | not recorded | 50 | 145 | 3750000 | 2544733 |
| Forward merge via epic | 5 | not recorded | 65 | 8 | 3750000 | 1362954 |
| Fork point record | 3 | not recorded | 35 | 24 | 2250000 | 1320815 |
| Docs worktree refs | 5 | not recorded | 55 | 37 | 3750000 | 1151664 |
| Docs readmes fallback | 5 | not recorded | 55 | 41 | 3750000 | 740257 |
| Docs flow phases | 5 | not recorded | 70 | 74 | 3750000 | 1997602 |
| Builtin worktree guard | 5 | not recorded | 60 | 43 | 3750000 | 698275 |
| Sweep guard | 3 | not recorded | 45 | 64 | 2250000 | 2409145 |
| Close entry docs | 2 | not recorded | 25 | 39 | 1500000 | 767823 |
| Total | 116 | not recorded | 1370 | 786 (17 of 23 tasks) | 87000000 | 23428409 (17 of 23 tasks) |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| Common worktree path sh | not recorded | not recorded | not recorded |
| Plan execute epic names | not recorded | not recorded | not recorded |
| Common worktree path py | not recorded | not recorded | not recorded |
| Merge target worktree | not recorded | not recorded | not recorded |
| Single hyphen names | not recorded | not recorded | not recorded |
| Merge contained check | not recorded | not recorded | not recorded |
| Name lookup parsers | not recorded | 0.27 | 0.10 |
| Integration tree create | not recorded | 0.44 | 0.11 |
| Epic base wiring | not recorded | 0.55 | 0.14 |
| Land in run | not recorded | 0.10 | 0.10 |
| Epic close sweep | not recorded | 0.26 | 0.18 |
| Epic close command | not recorded | 0.56 | 0.54 |
| Land outcomes | not recorded | 2.66 | 0.64 |
| Fork point diffs | not recorded | 0.10 | 0.36 |
| Slug collision guard | not recorded | 2.90 | 0.68 |
| Forward merge via epic | not recorded | 0.12 | 0.36 |
| Fork point record | not recorded | 0.69 | 0.59 |
| Docs worktree refs | not recorded | 0.67 | 0.31 |
| Docs readmes fallback | not recorded | 0.75 | 0.20 |
| Docs flow phases | not recorded | 1.06 | 0.53 |
| Builtin worktree guard | not recorded | 0.72 | 0.19 |
| Sweep guard | not recorded | 1.42 | 1.07 |
| Close entry docs | not recorded | 1.56 | 0.51 |

- MdAPE points: not recorded
- MdAPE minutes: 65.5%
- MdAPE tokens: 178.2%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| 2 of 23 tasks passed in 1 review round (common-worktree-path-sh, land-in-run); 16 more converged in 2 (record). | 3 tasks needed 3 rounds or a re-run: name-lookup-parsers (run1 round-cap), slug-collision-guard (gate-repeat then run3), land-outcomes (3+3); slug-collision-guard 145 min vs 50 (2.90), land-outcomes 133 vs 50 (2.66). |
| Time and tokens came in far under estimate on most tasks: land-in-run 9 vs 90 min (0.10), fork-point-diffs 6 vs 60 (0.10), forward-merge-via-epic 8 vs 65 (0.12). | Estimates are unreliable in both directions: MdAPE minutes 65.5%, tokens 178.2%; tokens ran 0.10-0.68 of expected on 16 of 17 measured tasks, only sweep-guard went over (1.07). |
| Interrogate verdicts V-A..V-I amended the design after the gate and all A1-A4, Q1, Q2, V-A..V-I were delivered; scope audit found AC evidence for all. | 6 of 23 tasks have no expected-vs-actual data (not recorded) and no task has post-delivery points, so MdAPE points is unmeasured. |
| Phase-5 review added two real tasks: sweep-guard (security: sweep trusted frontmatter branch, could delete main) and close-entry-docs (merge.py bypassed `ticket.py close` gates). | sweep-guard round-cap and the fork-point-diffs / forward-merge-via-epic gate-repeats were verifier or flag false positives (`--prev-head unknown` crash; plan-execute.js:2115 state-describing comment), each needing an accepted ruling (rulings.json). |
| Red evidence was real on many tasks (slug-collision-guard `-k clashing`, epic-close-sweep `-k dry_run`, merge-target-worktree `'ep-t2' == ''`). | No red evidence for epic-base-wiring, docs-worktree-refs, builtin-worktree-guard, sweep-guard in the task file; builtin-worktree-guard tests were never seen red. |
| Cleanup was safe: 16 pre-rebase trees and 29 branches removed only after a cherry and subject check showed every commit on main. | Full-suite verify hit the 600 s Bash cap (exit 144) in land-outcomes run 2; verifies were narrowed to component suites (5b82386), trading per-task cross-component coverage. |
| | Rebase landings left duplicates (`ticket_names` in slug-collision-guard-2, `LEGACY_SEP` found by scope audit) and landing runs failed twice (epic-close-command lock deadlock, builtin-worktree-guard 1 failed 423 passed). |

## Improvements

- Code:
  - plugins/workbench/skills/start-development/scripts/ticket.py: `branch` frontmatter is not validated; docs-flow-phases.md carries `branch: HEAD` while the other 22 tasks name a ref. A lint rejecting non-ref values would catch it.
  - plugins/workbench/workflows/plan-execute.js:2115 (and run-handback.md:112): the parking-flag scan matches state-describing text ("Blocked from release"); needs an allowlist case plus test.
  - verify-task.py: crashes with exit 2 on `--prev-head unknown` and `--tdd-revert` can leave files reverted; needs a test in its suite.
  - epic-close-command: `close` passes `suites=False` to merge_back, which the spec's call omitted (implementer judgement, never ruled).
- Delivered differently:
  - Task `branch` frontmatter points at `-landed` or `-2` marker refs, not the original task branches (commit 0a93b10), because the installed ticket.py checks ancestry only.
  - Verifies were narrowed from full suite to component suites (5b82386) after the 600 s cap; the plan assumed the full suite per task.
  - 2 tasks (sweep-guard, close-entry-docs) were added after phase 5 instead of being in the 21 planned.
  - forwardMerged was empty in all seven returns: no forward-merge fix reached a dependent through the workflow.
- Tech debt:
  - Unverified live paths (cannotVerify): land agent relaying `baseBefore` as `base`, merger resolving real re-conflicts, close against a real multi-repo component workbench (one component-mode test only); clear by a live run on the next epic.
  - Installed ticket.py predates merge-contained-check, so move done relies on ancestry only until a version bump is checked.
  - Nothing pushed; publishing docs/plans undecided (user call).
- Workflow:
  - recurring (housekeeping-rules-estimates): points, expected and actual figures are missing again, here for post-delivery points on all 23 tasks and for 6 tasks' actuals; migrated epics should backfill them (`actuals --backfill`) and phase 7 should record post-delivery points so MdAPE points is not "not recorded".
  - recurring (housekeeping-rules-estimates: implementer reports and verification claims not trusted, false greens): tasks again shipped with no red evidence or hand-substituted verification (sweep-guard, builtin-worktree-guard); gate task completion in plan-execute on a non-empty `tests.red` or a named exception, and have the reviewer rerun the check.
  - Estimates ran far high on tokens (MdAPE 178.2%) and minutes (65.5%) for infrastructure tasks that reuse existing helpers; calibrate the estimate table against the Deltas of this and the prior epic. One-off, retro table only otherwise.
  - Gate-repeat and round-cap escalations from tool false positives cost accepted rulings thrice; make the verifier tolerate `--prev-head unknown` before the next epic.
