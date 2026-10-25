# Flow speed and token optimization retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| Cache probe | 1 | not recorded | 6 | 2 | 750000 | not recorded |
| Estimator model | 1 | not recorded | 6 | 3 | 750000 | not recorded |
| Heartbeat quiet | 1 | not recorded | 6 | 6 | 750000 | not recorded |
| Continue launch | 1 | not recorded | 5 | 11 | 750000 | not recorded |
| Verify task bounded runs | 1 | not recorded | 6 | 12 | 750000 | not recorded |
| Estimate and actuals | 1 | not recorded | 6 | 10 | 750000 | not recorded |
| Planner sizing rule | 1 | not recorded | 6 | 8 | 750000 | not recorded |
| Verify scope wiring | 1 | not recorded | 5 | 8 | 750000 | not recorded |
| AC evidence map | 1 | not recorded | 6 | 11 | 750000 | not recorded |
| Gate provenance | 1 | not recorded | 6 | 9 | 750000 | not recorded |
| Review tiering | 1 | not recorded | 6 | 7 | 750000 | not recorded |
| Triage one call | 1 | not recorded | 6 | 11 | 750000 | not recorded |
| Cascade release | 1 | not recorded | 5 | 6 | 750000 | not recorded |
| Flow docs update | 1 | not recorded | 6 | 6 | 750000 | not recorded |
| Audit context and models | 1 | not recorded | 6 | 6 | 750000 | not recorded |
| Cache prefix change | 1 | not recorded | 5 | 3 | 750000 | 1925135 |
| Full suite split shared | 1 | not recorded | 6 | 3 | 750000 | 537834 |
| Launch land verify | 1 | not recorded | 5 | 7 | 750000 | 790346 |
| Verify shared deadline | 1 | not recorded | 6 | 12 | 750000 | 1628788 |
| Shell quote refs | 1 | not recorded | 5 | 7 | 750000 | 494446 |
| Medium only hold | 1 | not recorded | 5 | 4 | 750000 | 2308247 |
| Total | 21 | not recorded | 119 | 152 | 15750000 | 7684796 (6 of 21 tasks) |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| Cache probe | not recorded | 0.33 | not recorded |
| Estimator model | not recorded | 0.50 | not recorded |
| Heartbeat quiet | not recorded | 1.00 | not recorded |
| Continue launch | not recorded | 2.20 | not recorded |
| Verify task bounded runs | not recorded | 2.00 | not recorded |
| Estimate and actuals | not recorded | 1.67 | not recorded |
| Planner sizing rule | not recorded | 1.33 | not recorded |
| Verify scope wiring | not recorded | 1.60 | not recorded |
| AC evidence map | not recorded | 1.83 | not recorded |
| Gate provenance | not recorded | 1.50 | not recorded |
| Review tiering | not recorded | 1.17 | not recorded |
| Triage one call | not recorded | 1.83 | not recorded |
| Cascade release | not recorded | 1.20 | not recorded |
| Flow docs update | not recorded | 1.00 | not recorded |
| Audit context and models | not recorded | 1.00 | not recorded |
| Cache prefix change | not recorded | 0.60 | 2.57 |
| Full suite split shared | not recorded | 0.50 | 0.72 |
| Launch land verify | not recorded | 1.40 | 1.05 |
| Verify shared deadline | not recorded | 2.00 | 2.17 |
| Shell quote refs | not recorded | 1.40 | 0.66 |
| Medium only hold | not recorded | 0.80 | 3.08 |

- MdAPE points: not recorded
- MdAPE minutes: 37.5%
- MdAPE tokens: 52.8%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| 2 of 21 tasks passed in one review round (cache-probe, verify-scope-wiring); 16 of 21 ended at 2 rounds with a quoted tail (e.g. estimate-and-actuals: 65 passed; ruff clean). | heartbeat-quiet and review-tiering took 3 rounds; review-tiering stopped at the round cap (still verified true), so the cap was reached on 2 of 21 tasks. |
| Phase 5 findings were turned into remediation tasks, not dropped: verify-shared-deadline, launch-land-verify, full-suite-split-shared, shell-quote-refs (all 2 rounds, verified clean in run 3). | Phase 5 had to add 5 tasks after the plan: the estimate rose from 92 to 119 agent-min and the original plan missed a duplicated full-suite predicate (estimator.py vs validate-tasks.mjs) despite D13. |
| Explicit rulings with cost-if-wrong: cache-prefix-change accepted as a recorded no-op (probe `CACHE none`), D8 amended so a mediumOnly task does not land before its ruling. | medium-only-hold was rejected once: the hold was not transitive (chain a -> b -> c built c without b's code); fixed in 62d3ec5, then accepted after 2 + 2 rounds. |
| Cache probe was cheap (cache-probe 2 min vs 6, ratio 0.33) and saved a speculative prompt reorder. | Verify tasks ran 2.0-2.2x over formula (verify-task-bounded-runs 12 vs 6, verify-shared-deadline 12 vs 6, continue-launch 11 vs 5); MdAPE minutes 37.5%, overall 152 vs 119 (1.28). |
| Estimator and actuals landed, so this is the first epic with minutes and tokens deltas: MdAPE tokens 52.8% over 6 tasks. | Tokens actual recorded for only 6 of 21 tasks, points post-delivery for 0 of 21 (MdAPE points not recorded); medium-only-hold used 2308247 tokens vs 750000 (3.08x). |
| Final main 6b4b660 green: plugin 2817 assertions, scripts 467 passed, lint green. | gate-repeat stops on parking wording (medium-only-hold, runs 3 and 4) and the verifier reported AC2-AC6 not met for audit-context-and-models although files and tests were fine (false findings). |
|  | `uv sync --frozen` exited 1 in the verifier install step on cache-probe, continue-launch, verify-task-bounded-runs (cause unknown); cache-probe tail unclear; disk full mid-run failed a medium-only-hold verify. |
|  | Red evidence (`tests.red`) present for 7 of 21 tasks; the other 14 have none, not verifiable from git. |

## Improvements

- Code:
  - plugins/workbench/skills/start-development/scripts/verify-task.py and plan-execute.js: the `parking` wording gate flags comments that describe behaviour (plan-execute.js:859,869,2228,2257,2258); scan diff-added lines only or add an allow-list.
  - estimator.json and validate-tasks.mjs: shared `fullSuiteExamples` now, but keep a test that both readers agree (full-suite-split-shared).
  - verify step for `uv sync --frozen`: fails with exit 1 and is ignored as non-blocking; cause unknown.
- Delivered differently:
  - cache-prefix-change planned as a prompt reorder, delivered as a pinning test plus a MEMORY.md note, because the probe gave `CACHE none`.
  - cascade-release: D8 amended, a mediumOnly task releases dependents but does not land until a ruling; AC5 rewritten (epic review found an in-run landing).
  - 21 tasks delivered against 15 planned: 5 remediation tasks from phase 5 plus cache-probe.
- Tech debt:
  - Unverified live behaviour (`cannotVerify`): real verifier writing `$ACE`, haiku land/merge on real conflicts, `continue` and `apply-run` consuming `mediumOnly`, a clean dependent held by `behindHeld` never reported for landing; remove with one observed real plan-execute run.
  - Security LOWs left: SHA_RE trailing newline, task-file verify trusted, triage fail-open.
  - `declined` items (0-5 per task, sibling-owned) settled by no ruling; remove by triaging the run returns.
- Workflow:
  - `recurring` (housekeeping-rules-estimates): points and expected tokens/minutes are not recorded; here points post-delivery are missing for all 21 tasks and tokens for 15. Make `ticket.py migrate` and `apply-run` stamp post-delivery points and tokens, and make `ticket.py close` refuse an epic with none.
  - `recurring` (housekeeping-rules-estimates): reports taken from tails or run before staging gave false greens there; here the verifier gave false AC-not-met (audit-context-and-models) and a gate-repeat on comments. Require a verifier AC-not-met claim to cite the missing file or test, and have the reviewer rerun the cited command.
  - Add a `run-tests.sh` preflight on free disk (the medium-only-hold verify died with "No space left on device").
  - Recalibrate estimator.json for tasks touching verify-task.py and plan-execute.js (1.8-2.2x over formula) once a second epic has data; add a note to phases-1-3.md planner sizing.
  - Copy the Goals and analysis of a gitignored research brief into design.md before the phase 5 scope audit (Goals 1-2 were found only there).
