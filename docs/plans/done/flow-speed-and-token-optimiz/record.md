# Flow speed and token optimization record

## Summary

Asked: make the workbench flow (start-development, plan-execute and its verifier, reviewer, merger roles) faster and cheaper while keeping the review loop, independent verification, scope audit and approval ledger; plus the estimate sidequest (agent minutes only, calibrated, epic-level delivery estimate).
Shipped: 21 task files, all `done`: 15 planned tasks (14 plus cache-probe in run 1), cache-prefix-change (run 2, recorded no-op), and 5 phase-5 remediation tasks (run 3 plus one fix round for medium-only-hold in run 4). Measured baseline and ranked optimizations are in design.md; estimator, actuals recording, heartbeat quiet mode, bounded verify, triage in one call, review tiering, cascade release and docs landed on main.
Verdict: pass (phase 5, 2026-10-22). Meta mode: no MR, nothing pushed. Main 6b4b660: plugin "components with tests: 27   assertions passed: 2817", scripts 467 passed, lint green.

## Planned vs built

Review rounds = `rounds` in the task's latest run return. Verifier head = `tasks[].verification.head` (independent verifier SHA, 9 chars). All 21 tasks carry a verifier head; none is `unverified`. Planned file counts are from the task files; the run returns list only files changed in the last round, which differ for several tasks (for example ac-evidence-map: 6 planned, 2 in the return), so the task file wins.

| Task | Status | Run | Review rounds | Files (planned) | Verifier head | Verification tail |
|---|---|---|---|---|---|---|
| ac-evidence-map | done | 1 | 2 | 6 | 1f6bbfba6 | 88 passed; ruff clean; workflows 531 passed |
| audit-context-and-models | done | 1 | 2 | 6 | f26be9233 | 7 passed; workflows 535 passed |
| cache-probe | done | 1 | 1 | 4 | 0a7b69478 | tail unclear: "named tests not found in the listed files; AC6 met=true"; `uv sync --frozen` exit 1 |
| cascade-release | done | 1 | 2 | 2 | bae1f364c | workflows 525 passed |
| continue-launch | done | 1 | 2 | 2 | e5ec85e53 | 20 passed; ruff clean; `uv sync --frozen` exit 1 (non-blocking) |
| estimate-and-actuals | done | 1 | 2 | 7 | 65c5cb826 | 65 passed; ruff clean |
| estimator-model | done | 1 | 2 | 4 | 3a1ea0402 | 16 passed; ruff clean |
| flow-docs-update | done | 1 | 2 | 8 | cdc932494 | 39 passed (task test); AC6 20 passed; tdd failedOnBase true |
| gate-provenance | done | 1 | 2 | 4 | 5af4a66c1 | 76 passed; workflows 533 passed |
| heartbeat-quiet | done | 1 | 3 | 5 | b28fd1767 | heartbeat 35 passed; ruff clean |
| planner-sizing-rule | done | 1 | 2 | 6 | b90c434c1 | 30 passed; workflows 525 passed |
| review-tiering | done | 1 | 3 (stopped round-cap, still verified true) | 4 | e621a7d18 | workflows 543 passed; AC6 tests 40 pass 40 |
| triage-one-call | done | 1 | 2 | 4 | 4e33d73c2 | 121 passed; ruff clean |
| verify-scope-wiring | done | 1 | 1 | 3 | 3653ea884 | workflows 527 passed |
| verify-task-bounded-runs | done | 1 | 2 | 5 | d7962ed84 | AC1-AC7 met; ruff clean; `uv sync --frozen` exit 1 (non-fatal) |
| cache-prefix-change | done (no-op, TDD-skipped, accepted) | 2 | 2 (stopped gate-repeat on tdd-skipped, ruled accept) | 3 | 0894fff7e | workflows 568 passed |
| verify-shared-deadline | done | 3 | 2 | 4 | cc58bb40a | 24 passed; ruff clean |
| launch-land-verify | done | 3 | 2 | 2 | 560074c99 | script exit 0, passed true, tdd failedOnBase true |
| full-suite-split-shared | done | 3 | 2 | 5 | 7937ba8d9 | 17 passed; node tests 7 pass 7; ruff clean |
| shell-quote-refs | done | 3 | 2 | 2 | 4409cc7a7 | workflows 571 passed |
| medium-only-hold | done (accepted after fix round) | 3, 4 | 2 + 2 | 2 | 6fe6d7ba0 (run 3: 71cf1523f) | medium-release 9/9 incl. transitive chains; workflows 571 passed |

Red evidence (implementer's own `tests.red`, never a tdd-revert result): present for cache-probe (pytest test_hook_evidence FAILED), cascade-release, continue-launch (pytest -k process_only), verify-scope-wiring, verify-task-bounded-runs (pytest test_verify_bounded FAILED), shell-quote-refs (shqRef removed), verify-shared-deadline (TypeError on run()). Absent (`wroteTestFirst` false, no `tests.red`) for the other 14. Of those, cache-prefix-change, full-suite-split-shared and ac-evidence-map state the tests pin already-working behaviour or are renames; review-tiering reported a red/green on a scratch copy outside the tree (5 fail at 2050fa1^, 10 pass at HEAD) as a processGap, not in `tests.red`. Not verifiable from git.

Approvals (`<epic dir>/approvals.json` against the run 1 return; runs 2-4 returned no extra entries beyond Db for run 2):

| Id | Text | Decisions | Tasks | Status |
|---|---|---|---|---|
| U1 | Launch an epic for token usage optimization of the flow; keep review loop and completeness checks | D1 D2 D3 D7 D9 D11 D12 | verify-task-bounded-runs, verify-scope-wiring, ac-evidence-map, gate-provenance, triage-one-call, review-tiering, audit-context-and-models, heartbeat-quiet, continue-launch, planner-sizing-rule, flow-docs-update | delivered |
| U2 | Fix task estimates: agent time only, realistic, epic delivery estimate | D4 D5 D10 D13 | estimator-model, estimate-and-actuals, planner-sizing-rule, flow-docs-update | delivered |
| Da | Deliver the 11 brief inputs; cascade containment only beyond epic integration worktrees | D8 | cascade-release, continue-launch, flow-docs-update | delivered (D8 amended, see rulings) |
| Db | Cache prefix change gated by probe; no saving -> recorded no-op | D6 | cache-probe, cache-prefix-change | delivered (CACHE none, no-op) |
| Dc | Estimator replaces planner-guessed estimates; epic wall formula; actuals recorded | D4 D5 | estimator-model, estimate-and-actuals, flow-docs-update | delivered |
| Dd | Apply sizing lesson to this plan | D10 | planner-sizing-rule | delivered |
| Q1 | Quiet heartbeat, 30-minute progress, END/STALL at once | D14 | heartbeat-quiet, flow-docs-update | delivered |

## Deviations and rulings

- cache-prefix-change recorded as a no-op (ruling: accept). What: no prompt changed; the task adds a test pinning task-first order and records the probe in MEMORY.md. Why: probe verdict `CACHE none`. TDD skipped (no behaviour change); run 2 stopped gate-repeat on tdd-skipped. Cost if wrong: a possible cache-creation saving is forgone; the probe shows 14855 created / 6975 read on every agent regardless of order.
- D8 amended: a mediumOnly task releases dependents but does not land on the epic branch until a ruling (the builder check answer wins over the earlier in-run landing). Why: epic review found a mediumOnly task landed before its ruling. Cost if wrong: dependents wait for a ruling; extra orchestrator turn. cascade-release AC5 rewritten to match.
- medium-only-hold rejected once, accepted after a fix round. What: the hold checked only the dependency's own flag; in chain a(held) -> b -> c, c built without b's code. Fix made the hold transitive (commit 62d3ec5) with two- and three-deep chain tests. Final acceptance: 9/9 medium-release tests, workflows 571; the open parking flags at plan-execute.js:859,869,2228,2257,2258 dismissed as false positives on behaviour-describing comments. Cost if wrong: a literal parking-wording lint hit could reappear.
- Q1: yes. Heartbeat stays quiet, progress at most every 30 minutes, STALL after 30 minutes without journal change; AGENTS.md rule 4 names it as the exception to the 10-minute bound. Cost if wrong: a stuck run is reported up to 30 minutes late.
- Landing: tasks landed by plain `--no-ff` merges in landing trees (c2-land, c3-land, cp-land, us-land) with the full suite before each fast-forward of main. Landing fixes: personal-term fixture rename, E501 wrap, `--return` emitted for non-Claude harnesses, private suite lock in continue-launch tests, ticket tests updated for estimate_by/actual_roles and the targeted helper verify, rename of init_engine helpers (d87b383). Cost if wrong: merge history is noisier than a squash.
- `forwardMerged`: empty in all four runs.

## Duplicates reconciled

Full-suite predicate semantics were duplicated between estimator.py and validate-tasks.mjs despite D13 (epic review finding 3); reconciled by full-suite-split-shared, which keeps one `fullSuiteExamples` list in estimator.json used by both. The run returns report no other duplicates.

## Discovered and blocked

- Disk full mid-run ("No space left on device", 264Mi free) failed `run-tests.sh --only workflows` in the medium-only-hold verify; cleared by a docker prune (orchestrator). The verifier re-ran with `node --test` directly (569 pass).
- Phase 5 findings, all fixed by remediation tasks: verify-task timeout per command (verify-shared-deadline); `continue --launch` landed with `true` as the verify (launch-land-verify); duplicated full-suite split (full-suite-split-shared); MEDIUM unquoted forkPoint/baseRef and LOW repoDir double quotes in verifier shell commands (shell-quote-refs).
- Security LOWs noted, not actionable: SHA_RE trailing newline, task-file verify trusted, triage fail-open.
- `cannotVerify` (not settled by a ruling): live behaviour of a real verifier writing `$ACE`; live haiku land/merge agents on real conflicts; whether `continue` and `apply-run` consume `mediumOnly` correctly end to end; that a live run return populates `tasks[].verification.command`; merge.py rebase carrying held commits (inferred from landPrompt); the transitive tests failing before the fix (not re-run against pre-change code); whether a clean dependent held back by `behindHeld` is landed on a later run once the ruling accepts the held task (no code path reports it). Who can clear: the next real plan-execute run, observed by the orchestrator.
- `declined` entries: every task carries 0-5 declined items (sibling-owned diffs, e.g. mergeVerifySteps not passing `--ac-evidence`); no ruling settled them; full text is in the run returns under `/private/tmp/claude-501/-Users-szymonri-Documents-workbench/24dd7e5c-62ee-4970-92ad-0076f6552463/scratchpad/epic-c/run{1..4}-return.json`.
- `uv sync --frozen` exited 1 in the verifier install step on cache-probe, continue-launch and verify-task-bounded-runs (non-blocking). Cause unknown; the orchestrator can clear.
- Files vs summaries: audit-context-and-models: the verifier reported AC2-AC6 not met, but the tree has the code and tests and they pass; the row says verified because the files win. medium-only-hold run 3 and 4 each stopped `gate-repeat` on parking wording that the files show is behaviour description.

## Research that changed the plan

- Measured baseline (design.md "Measured baseline and ranked optimizations", 592 workflow agents over 27.3 h): verify is 55% of agent-minutes (1072 of 1942); rounds beyond the first are 38% of agent-minutes; full-suite verify is the strongest predictor of task time (r = 0.74); 19 root escalations caused 183 dependency-failed task runs. These ranked the 11 plan inputs and the cascade-release scope.
- Cache probe (design.md "Cache probe result", run wf_c93a609a-e42): `CACHE none static=14855,14855 task=14855,14855`; changed cache-prefix-change from a prompt reorder to a recorded no-op.
- Epic integration worktrees landing in the same period changed D8: only the beyond-in-run-landing cascade parts were built (Da).

## Cost

Agents: run 1 83 agents, 61 min wall (15 tasks); run 3 29 agents (5 remediation tasks); runs 2 and 4 agent counts unknown (one task each). Continuations: 3 relaunches (runs 2, 3, 4). Audit: `off` in all four plan-execute runs; the scope audit ran at phase 5 outside plan-execute (sonnet scope-auditor) plus the epic reviewer and security researcher (sonnet).
Role totals from `actual_roles` (agent-min counts as recorded): impl 59, verify 48, review 30, fix 26, false-finding 1 (sum 164 role units against the 152 task total below).

Estimate vs actual (README Time: Estimate 119 agent-min, critical path 61 min, expected wall 2.6 h at k=2.0 and P=1.5; Actual 152 agent-min summed agent spans; remaining 0). The original plan stated 92 min with the formula before the remediation tasks were added.

| Task | Estimate | Actual | Roles (impl/verify/review/fix) |
|---|---|---|---|
| ac-evidence-map | 6 | 11 | 4/3/2/2 |
| audit-context-and-models | 6 | 6 | 2/2/1/1 |
| cache-prefix-change | 5 | 3 | 1/2/1/1 |
| cache-probe | 6 | 2 | 1/1/1/0 |
| cascade-release | 5 | 6 | 3/1/1/2 |
| continue-launch | 5 | 11 | 3/3/2/4 |
| estimate-and-actuals | 6 | 10 | 4/4/1/1 |
| estimator-model | 6 | 3 | 1/1/1/1 |
| flow-docs-update | 6 | 6 | 4/1/1/1 |
| full-suite-split-shared | 6 | 3 | 1/1/1/1 |
| gate-provenance | 6 | 9 | 3/3/2/1 |
| heartbeat-quiet | 6 | 6 | 2/3/1/1 |
| launch-land-verify | 5 | 7 | 2/3/1/2 |
| medium-only-hold | 5 | 4 | 1/1/1/1 (+1 false-finding) |
| planner-sizing-rule | 6 | 8 | 6/1/1/1 |
| review-tiering | 6 | 7 | 2/2/2/1 |
| shell-quote-refs | 5 | 7 | 4/1/1/1 |
| triage-one-call | 6 | 11 | 2/6/2/1 |
| verify-scope-wiring | 5 | 8 | 6/1/1/0 |
| verify-shared-deadline | 6 | 12 | 3/3/4/2 |
| verify-task-bounded-runs | 6 | 12 | 4/5/2/1 |
| Total | 119 | 152 | |

Overall ratio actual/estimate = 152/119 = 1.28 (1.65 against the original 92). Over: verify-task-bounded-runs, verify-shared-deadline (2.0x), ac-evidence-map, continue-launch, triage-one-call (about 1.8-2.2x); under: cache-probe, estimator-model, full-suite-split-shared, cache-prefix-change. The actual wall-clock of the epic is unknown (run 1 was 61 min; other runs and orchestrator gaps not read). This is the estimator's first measurement; report only, not a budget.

## MRs and deploy

None. Meta mode in the workbench template repo: no MR or PR, nothing pushed. Deploy: not applicable. Landed on main locally, last verified at 6b4b660 (plugin 2817 assertions in 27 components, scripts 467 passed, lint green).

## Lessons routed to

- Mechanical, add a check: a test or lint that fails when a task's `verification.head` is missing from the run return (so `unverified` cannot read as done).
- Mechanical, add a check: the parking-wording gate (`parking` in verify-task.py) flags comments that describe behaviour (plan-execute.js:859-2258); add an allow-list or a diff-added-lines-only scan test so it stops causing gate-repeat stops (medium-only-hold, runs 3 and 4).
- Mechanical, add a check: a test that a verifier reporting "AC not met" must cite the missing file or test, since audit-context-and-models got five false AC-not-met claims.
- Mechanical, add a check: a `run-tests.sh` preflight that fails fast on low free disk, instead of the verify failing mid-run with "No space left on device".
- Judgement call, edit the skill: phases-1-3.md planner sizing guidance should note that tasks touching verify-task.py and plan-execute.js ran 1.8-2.2x over formula (verify-task-bounded-runs, verify-shared-deadline, triage-one-call); recalibrate estimator.json from this run's per-task table after a second epic's data exists.
- Judgement call, edit the skill: start-development phase 5 should require the Goals/analysis from a gitignored research brief to be copied into design.md before the scope audit (Goals 1-2 were found only there).
