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

- `ticket.py` new-task parser: `--points` required, `type=int`.
- `ticket.py:_task_problems` - "task <slug> has no points" for non-done epics.

## Expected outcome

No task can be created or pass lint without storypoints.

## Steps

1. List the files under Files, read them in one pass; write AC1 and AC2 and run them: they fail.
2. Make the flag required, add the lint check, add `--points` to every new-task call in the listed tests and helpers; run the verify once.
3. Commit; leave the tree clean.

## Notes

- Estimate: 3 points.
- The callers are the `"new-task"` invocations in test_ticket_overlap_ignore.py, test_ticket_check.py, test_ticket_naming.py (helper), ticket_repo_helpers.py, test_ticket_worktrees_refresh.py and test_ticket_files.py (helper). If a caller outside Files turns up, report it in `discovered`.
- Splitting this from estimate-fields keeps each task at most 8 files; the two land in order.
