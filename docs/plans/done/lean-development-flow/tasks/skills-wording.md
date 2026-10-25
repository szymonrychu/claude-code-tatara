---
title: Skills wording
status: done
repo: workbench
value: A skill that still tells the agent to arm a heartbeat or run plan-execute reintroduces the cost
files: [plugins/workbench/skills/, plugins/workbench/hooks/, plugins/workbench/rules/concise-orchestrator.md, plugins/workbench/agents/]
verify: "bash plugins/workbench/scripts/run-tests.sh && mise run lint"
depends_on: [start-development-rewrite, epic-run-skill]
model: sonnet
review: ""
verified_head: 606b059
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 31
actual_tokens: 860510
actual_roles: "impl 31, review 20"
actual_role_tokens: "impl 480638, review 379872"
---

# Skills wording

## Requirement

Remove every remaining reference to the retired machinery from the plugin outside start-development: in `plugins/workbench/skills/` (interrogate, start-review, start-discovery, worktree-create, worktree-merge, epic-create, epic-move, epic-task-create, epic-worktrees-remove, handoff, release, pullrequests-*, research-*, init, template-update and any other), `plugins/workbench/hooks/` (the bash-output-filter docstring) and `plugins/workbench/rules/concise-orchestrator.md` ("heartbeat reply"). The words that must be gone from every file outside a `tests/` directory (the retirement tests name them on purpose), as the proof: plan-execute, heartbeat, hook-probe, verify-task, approvals ledger, approvals.json, apply-run, `ticket.py continue`, `ticket.py rule`, forward-merge, per-task worktree, named copy, Workflow tool. Where a sentence described a plan-execute behaviour (interrogate "a task plan-execute escalated", start-review "a plan-execute run on the full path", worktree-create/merge per-task trees, epic-move and epic-worktrees-remove task trees), rewrite it for the lean loop (an escalated task of epic-run; the implementer in the epic's integration tree; one integration tree per epic). Each skill's own tests keep passing; where a test pinned the old wording, update it. Nothing else changes in those skills.

## Acceptance conditions

- AC1: outside `tests/` directories, `grep -rniE --exclude-dir=tests "plan-execute|heartbeat|hook-probe|verify-task|approvals ledger|approvals\.json|apply-run|ticket\.py continue|ticket\.py rule|forward-merge|per-task worktree|named copy|Workflow tool" plugins/workbench/skills plugins/workbench/hooks plugins/workbench/rules plugins/workbench/agents` prints nothing [evidence: command:! grep -rniE --exclude-dir=tests "plan-execute|heartbeat|hook-probe|verify-task|approvals ledger|approvals\.json|apply-run|ticket\.py continue|ticket\.py rule|forward-merge|per-task worktree|named copy|Workflow tool" plugins/workbench/skills plugins/workbench/hooks plugins/workbench/rules plugins/workbench/agents]
- AC2: a test pins AC1 over those four directories, skipping `tests/` directories [evidence: test:plugins/workbench/hooks/tests/test_no_retired_words.py::test_plugin_has_no_retired_words]
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

1. Read the files named under Files and the tests the ACs name; write the new or changed tests first and run them: they must fail for the expected reason.
2. Implement until the targeted verify command passes; keep every existing test green or update it where it pinned removed behaviour.
3. Run the verify command, paste its real tail in the report, commit on the epic branch, leave the tree clean.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
