---
title: Lean development flow
blockers: []
stage: build
owner: Szymon Richert
repos: [workbench]
created: 2026-10-24
---

# Lean development flow

## Project brief

What: Replace the plan-execute Workflow and its verifier, tiers, ledger and per-task worktrees with an instruction-driven implement, review, fix, audit loop run by the orchestrator over the existing epic and task files
How: Delete the workflows directory, verifier scripts and run-loop ticket.py commands; slim the task model; rewrite implementer, reviewer, scope-auditor and planner agents; rewrite start-development and add an epic-run skill; update every doc and rule
Why: Each epic cost 4-7 workflow runs and about six agent sessions per task; scope protection should come from precise tasks and one independent reviewer per task, not orchestration machinery

## Description

The flow protects scope (agents silently narrowing the agreed deliverable) with a 2952-line Workflow state machine, an independent verifier, split spec and quality reviewers, review tiers, triage and false-finding classifiers, an approval ledger, per-task worktrees with in-run landing and forward merges, a heartbeat watcher and a 25-field return contract. The three recorded epics each took 4-7 plan-execute runs and roughly six agent sessions per task. This epic keeps what works (epics and tasks as files, planning decoupled from execution, one integration worktree per epic, the hooks, the scope audit) and replaces the orchestration machinery with instructions: one implementer per task, one reviewer per task that verifies on HEAD and checks every acceptance condition, fix rounds that continue the same agents, one scope audit per epic.

## Goals

- An epic of N tasks costs about 2N+3 agent sessions (implementer and reviewer per task, planner, scope auditor, record writer) instead of roughly 6N+10, with no Workflow run.
- Scope protection stays structural: every task has acceptance conditions, a reviewer who did not write the code checks each one against the files and runs the verify command on HEAD, and one scope auditor per epic reads README goals and every AC against the integrated diff.
- Planning stays decoupled from execution: epics and tasks are files under docs/plans, created with ticket.py, and a planned epic can be executed from any session with one skill while another epic is being planned.
- One integration worktree per epic; tasks run in dependency order inside it; no per-task worktrees, landing, forward merges or rulings files.
- Every removed mechanism is pinned removed by a retirement test, every remaining doc describes the lean flow, and mise run test and mise run lint are green on main after the epic.

## Non-goals

- Changing the hooks (guard-bash, protect_files, format-file, verify-recorder, subagent-commit-guard, bash-output-filter): they are cheap and hold the line.
- Changing init, template-update, component-add/remove, the git-*/pullrequests-* skills, start-debugging, start-research, start-discovery, interrogate or the research agents beyond wording.
- A nested "epic runner" agent that dispatches its own subagents: the loop runs in the orchestrator session with background dispatches.
- Cutting a release or editing CHANGELOG (the release skill does that later).
- Rewriting the user's global rules outside this repository.

## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
