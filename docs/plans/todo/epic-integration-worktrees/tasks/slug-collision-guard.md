---
title: Slug collision guard
status: todo
repo: workbench
value: "Two tickets can never produce the same branch, so no task lands on another's tree"
files: [plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/tests/test_ticket_naming.py]
verify: "mise run test && mise run lint"
depends_on: [epic-close-sweep]
owns: []
uses: [ticket-name-lookup]
model: sonnet
estimate: 40
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Slug collision guard

## Requirement

Prevent branch-name collisions at ticket creation (design D3), since `<epic>-<task>` cannot be split back into its parts.

- `ticket.py new-epic` refuses a slug equal to any existing `<epic>-<task>` (from `ticket_names`, all phases) with exit 1, writes and commits nothing, and prints `ticket.py: epic slug <slug> collides with the branch of task <task> in epic <epic>`; `--force` does not override it.
- `ticket.py new-task` refuses a task whose `<epic>-<task>` equals any epic slug or another epic's `<epic>-<task>` (all phases), exit 1, nothing written, the message names the clashing ticket.
- `ticket.py rename` applies the same rules to the new slug and to every `<new>-<task>` of the renamed epic.
- `ticket.py check --title` reports the same clash as a failure line.
- Existing slug-uniqueness and near-duplicate behaviour is unchanged.

## Acceptance conditions

- AC1: new-epic refuses a slug equal to an existing task branch and commits nothing [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_new_epic_refuses_slug_equal_to_task_branch]
- AC2: new-task refuses a name equal to an epic slug [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_new_task_refuses_name_equal_to_epic_slug]
- AC3: new-task refuses a name equal to another epic's task branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_new_task_refuses_name_equal_to_other_epic_task]
- AC4: --force does not override a branch collision [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_force_does_not_override_branch_collision]
- AC5: rename refuses a slug whose names would collide [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_rename_refuses_colliding_slug]
- AC6: check --title lists the collision as a failure [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_check_title_reports_branch_collision]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_naming.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
