---
title: Ticket drop run commands
status: todo
repo: workbench
value: Cuts ticket.py to the planning and lifecycle commands the user keeps
files: [plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/scripts/ticket_cmds/, plugins/workbench/skills/start-development/tests/, plugins/workbench/scripts/lib/estimator.py, plugins/workbench/scripts/lib/estimator.json, plugins/workbench/scripts/tests/test_estimator.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint"
depends_on: [remove-workflows]
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

# Ticket drop run commands

## Requirement

Remove from `ticket.py` every subcommand that existed for the plan-execute run loop or the approval ledger: `apply-run`, `args`, `continue`, `rule`, `estimate`, `facts`, `decide`, `contract` and `graph`, with their modules under `ticket_cmds/`, their tests (`test_ticket_run.py`, `test_ticket_continue.py`, `test_ticket_continue_launch.py`, `test_ticket_args.py`, `test_ticket_apply_run_fixes.py`, `test_ticket_decide.py`, `test_ticket_estimate.py` and the contract, graph, facts and rule tests), and the estimator (`plugins/workbench/scripts/lib/estimator.py`, `estimator.json`, `scripts/tests/test_estimator.py`). `ticket.py --help` lists exactly: slug, new-epic, new-task, check, index, existing, tasks, worktrees, move, stage, review, rename, lint, reap, path, amend, close, questions, roadmap. `new-task` loses `--estimate`; nothing writes `estimate`, `estimate_by`, `actual` or `actual_roles`. Dead helpers that only those commands used go too (the run-dir readers, rulings readers, approvals loaders used only by decide). Keep every other subcommand's behaviour and tests green. Add a retirement test that pins the removed subcommands and files.

## Acceptance conditions

- AC1: `python3 plugins/workbench/skills/start-development/scripts/ticket.py --help` lists exactly the 19 kept subcommands and none of apply-run, args, continue, rule, estimate, facts, decide, contract, graph [evidence: command:python3 plugins/workbench/skills/start-development/scripts/ticket.py --help]
- AC2: `git ls-files plugins/workbench/skills/start-development/scripts/ticket_cmds plugins/workbench/scripts/lib/estimator.py plugins/workbench/scripts/lib/estimator.json` lists only `__init__.py`, `amend.py` and `questions.py` under ticket_cmds [evidence: command:git ls-files plugins/workbench/skills/start-development/scripts/ticket_cmds plugins/workbench/scripts/lib/estimator.py plugins/workbench/scripts/lib/estimator.json]
- AC3: a retirement test pins AC1 and AC2 [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py::test_run_loop_commands_retired]
- AC4: `grep -n "estimate\|actual_roles\|apply.run\|rulings" plugins/workbench/skills/start-development/scripts/ticket.py` prints nothing [evidence: command:grep -c "estimate\|actual_roles\|apply.run\|rulings" plugins/workbench/skills/start-development/scripts/ticket.py]
- AC5: `bash plugins/workbench/scripts/run-tests.sh --only start-development` and `--only scripts` pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/`
- `plugins/workbench/skills/start-development/tests/`
- `plugins/workbench/scripts/lib/estimator.py`
- `plugins/workbench/scripts/lib/estimator.json`
- `plugins/workbench/scripts/tests/test_estimator.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
