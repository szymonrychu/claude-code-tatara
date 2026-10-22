---
title: Flow speed and token optimization
blockers: [Epic integration worktrees]
stage: review
owner: Szymon Richert
repos: [workbench]
created: 2026-10-21
---

# Flow speed and token optimization

## Project brief

What: Faster, cheaper plan-execute delivery with the review loop and completeness checks kept; realistic agent-time task and epic estimates
How: measure the session's runs, rank optimizations by saving, implement the top ones, calibrate the estimator
Why: multi-harne cost millions of subagent tokens and many relaunch rounds; estimates are human-days style and unrealistic

## Description

Make the workbench development flow (start-development plus the plan-execute workflow, its verifier, reviewer and merger roles) deliver faster and spend fewer tokens. Keep the review loop and the task-completeness checks (independent verification, scope audit, approval ledger).

The analysis base is the epics delivered in the session of 2026-10-20/21:
- project-agnostic-multi-harne: 86 tasks over about 13 plan-execute runs.
- epic-integration-worktrees: 21 tasks, in progress.
Their per-agent journals, transcripts and run returns are on disk.

Sidequest requested by the user: fix task delivery estimates. Estimate in agent wall-clock time only, make the numbers realistic (calibrated on the measured runs), and add an epic-level delivery estimate.

## Goals

- A measured baseline from the session's runs: tokens and wall-clock per task, per role (implementer, verifier, reviewer, fixer, triage, merger, audit), per round; where the spend and the waiting went.
- Ranked optimizations with expected savings, each keeping the review loop, independent verification and the scope/completeness checks.
- Task estimates in agent minutes, calibrated on the measured actuals, plus an epic delivery estimate (critical path and parallelism aware) shown at the gate and in the epic README.

## Non-goals

- Dropping independent verification, the review loop, the scope audit or the approval ledger.
- Changes to the personal plugin at ~/Documents/claude-infra-plugin (template only, unless the user asks).

## Time

Estimate: 119 agent-min | Critical path: 61 min | Expected wall at P=1.5: 2.6 h (k=2.0) | Actual: 152 min | Remaining estimate: 0 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-22)

Epic review, phase 5, over 6845a91..main (docs/plans and docs/research excluded).
- Epic review (reviewer, sonnet): 4 findings, all fixed by remediation tasks: verify-task timeout per command instead of one shared deadline (verify-shared-deadline); continue --launch landed tasks without a verify with `true` (launch-land-verify); full-suite splitting differed between estimator.py and validate-tasks.mjs (full-suite-split-shared, shared fullSuiteExamples); a mediumOnly task landed before its ruling, contradicting the builder check answer (ruling: the answer wins, D8 amended; medium-only-hold, then one fix round for a transitive hold through chains a -> b -> c).
- Security review (security-researcher, sonnet): MEDIUM unquoted forkPoint/baseRef in verifier shell commands and LOW repoDir double quotes, fixed in shell-quote-refs; other LOWs (SHA_RE trailing newline, task-file verify trusted, triage fail-open) noted, not actionable.
- Scope audit (scope-auditor, sonnet): Goals 1-2 lived only in the gitignored brief: copied into design.md "Measured baseline and ranked optimizations". README Time line regenerated with the new estimator (119 agent-min, critical path 61 min, expected wall 2.6 h) and actuals stamped from the run transcripts with apply-run --run-dir (152 agent-min). Renamed AC refs retargeted (cache-probe, continue-launch AC3); cascade-release AC5 rewritten to amended D8.
- Cache probe: CACHE none; cache-prefix-change recorded the no-op.
- Landing fixes: personal-term fixture rename, E501 wrap, --return emitted for non-Claude harnesses, private suite lock in continue-launch tests, ticket tests updated for estimate_by/actual_roles and the targeted helper verify.
- Full suite: mise run test and mise run lint green on main 6b4b660 (plugin 2817 assertions, scripts 467 passed).
- Rulings: cache-prefix-change accepted (TDD-skipped, no behaviour change); medium-only-hold accepted after its fix round (only parking-wording false positives left).
