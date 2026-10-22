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
