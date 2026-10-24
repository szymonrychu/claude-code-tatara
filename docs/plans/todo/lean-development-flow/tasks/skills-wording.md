---
title: Skills wording
status: todo
repo: workbench
value: A skill that still tells the agent to arm a heartbeat or run plan-execute reintroduces the cost
files: [plugins/workbench/skills/, plugins/workbench/hooks/, plugins/workbench/rules/concise-orchestrator.md, plugins/workbench/agents/]
verify: "bash plugins/workbench/scripts/run-tests.sh && mise run lint"
depends_on: [start-development-rewrite, epic-run-skill]
owns: []
uses: []
model: sonnet
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Skills wording

## Requirement

Remove every remaining reference to the retired machinery from the plugin outside start-development: in `plugins/workbench/skills/` (interrogate, start-review, start-discovery, worktree-create, worktree-merge, epic-create, epic-move, epic-task-create, epic-worktrees-remove, handoff, release, pullrequests-*, research-*, init, template-update and any other), `plugins/workbench/hooks/` (the bash-output-filter docstring) and `plugins/workbench/rules/concise-orchestrator.md` ("heartbeat reply"). The words that must be gone, as the proof: plan-execute, heartbeat, hook-probe, verify-task, approvals ledger, approvals.json, apply-run, `ticket.py continue`, `ticket.py rule`, forward-merge, per-task worktree, named copy, Workflow tool. Where a sentence described a plan-execute behaviour (interrogate "a task plan-execute escalated", start-review "a plan-execute run on the full path", worktree-create/merge per-task trees, epic-move and epic-worktrees-remove task trees), rewrite it for the lean loop (an escalated task of epic-run; the implementer in the epic's integration tree; one integration tree per epic). Each skill's own tests keep passing; where a test pinned the old wording, update it. Nothing else changes in those skills.

## Acceptance conditions

- AC1: `grep -rniE "plan-execute|heartbeat|hook-probe|verify-task|approvals ledger|approvals\.json|apply-run|ticket\.py continue|ticket\.py rule|forward-merge|per-task worktree|named copy|Workflow tool" plugins/workbench/skills plugins/workbench/hooks plugins/workbench/rules plugins/workbench/agents` prints nothing [evidence: command:grep -rniEc "plan-execute|heartbeat|hook-probe|verify-task|approvals ledger|approvals\.json|apply-run|ticket\.py continue|ticket\.py rule|forward-merge|per-task worktree|named copy|Workflow tool" plugins/workbench/skills plugins/workbench/hooks plugins/workbench/rules plugins/workbench/agents]
- AC2: a test pins AC1 over those four directories [evidence: test:plugins/workbench/hooks/tests/test_no_retired_words.py::test_plugin_has_no_retired_words]
- AC3: `bash plugins/workbench/scripts/run-tests.sh` ends with `all green` [evidence: command:bash plugins/workbench/scripts/run-tests.sh]

## Files

- `plugins/workbench/skills/`
- `plugins/workbench/hooks/`
- `plugins/workbench/rules/concise-orchestrator.md`
- `plugins/workbench/agents/`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
