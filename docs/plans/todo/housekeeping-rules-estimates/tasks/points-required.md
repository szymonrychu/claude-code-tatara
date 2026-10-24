---
title: Points required
status: todo
repo: workbench
value: No task can be created or pass lint without storypoints
files: [plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/tests/ticket_repo_helpers.py, plugins/workbench/skills/start-development/tests/test_ticket_overlap_ignore.py, plugins/workbench/skills/start-development/tests/test_ticket_check.py, plugins/workbench/skills/start-development/tests/test_ticket_naming.py, plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py, plugins/workbench/skills/start-development/tests/test_ticket_files.py, plugins/workbench/skills/start-development/tests/test_ticket_lint.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [estimate-fields]
model: opus
review: ""
verified_head: ""
---

# Points required

## Requirement

User requirement (U2, verbatim): "each task consists also of: complexity estimate in storypoints; expected time; expected tokens"

Design D7: `new-task --points` is required (argparse exits 2 naming `--points` when it is missing), and `ticket.py lint` reports every task of a todo or in-progress epic that has no `points`. Every test that creates a task through `new-task` passes `--points`; no compatibility default is added (U1: no backward compatibility unless asked).

## Acceptance conditions

- AC1: `new-task` without `--points` exits 2 and names `--points` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_new_task_requires_points]
- AC2: lint reports a task of a todo epic with no points and passes once points are set [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_lint.py::test_lint_requires_points]
- AC3: every test helper and call that runs `new-task` passes `--points` (no default added in ticket.py) [evidence: command:! grep -n "default=.*points\|points.*default=" plugins/workbench/skills/start-development/scripts/ticket.py]
- AC4: start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/ticket_repo_helpers.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_overlap_ignore.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_check.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_naming.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_files.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_lint.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
