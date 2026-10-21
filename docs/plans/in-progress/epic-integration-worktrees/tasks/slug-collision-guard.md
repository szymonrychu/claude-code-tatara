---
title: Slug collision guard
status: in-progress
repo: workbench
value: "Two tickets can never produce the same branch, so no task lands on another's tree"
files: [plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/tests/test_ticket_naming.py]
verify: "mise run test && mise run lint"
depends_on: [epic-close-sweep]
owns: []
uses: [ticket-name-lookup]
model: sonnet
estimate: 50
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

Prevent branch-name collisions at ticket creation (design D3; interrogate verdict I), since `<epic>-<task>` cannot be split back into its parts.

- `ticket.py new-epic` refuses a slug equal to any existing `<epic>-<task>` (from `ticket_names`, all phases) with exit 1, writes and commits nothing, and prints `ticket.py: epic slug <slug> collides with the branch of task <task> in epic <epic>`; `--force` does not override it.
- `ticket.py new-task` refuses a task whose `<epic>-<task>` equals any epic slug or another epic's `<epic>-<task>` (all phases), exit 1, nothing written, the message names the clashing ticket.
- `ticket.py rename` applies the same rules to the new slug and to every `<new>-<task>` of the renamed epic.
- Names on disk count too (verdict I, matching the builder-check answer). The taken names are the tickets' names (`ticket_names`, all phases) plus every local branch of the source checkouts and every directory under `<configdir>/worktrees/`, legacy `<epic>--<task>` trees and branches included. The refused cases are: a new epic slug or a new `<epic>-<task>` equal to such a branch or directory, and a new task whose legacy name `<epic>--<task>` is still a tree or branch on disk with no ticket of its own (it would be swept as the new ticket's tree). Each refusal names the tree or branch, exits 1, writes and commits nothing, and `--force` never overrides it.
- `ticket.py check --title` reports the same clash as a failure line.
- Existing slug-uniqueness and near-duplicate behaviour is unchanged.

## Acceptance conditions

- AC1: new-epic refuses a slug equal to an existing task branch and commits nothing [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_new_epic_refuses_slug_equal_to_task_branch]
- AC2: new-task refuses a name equal to an epic slug [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_new_task_refuses_name_equal_to_epic_slug]
- AC3: new-task refuses a name equal to another epic's task branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_new_task_refuses_name_equal_to_other_epic_task]
- AC4: --force does not override a branch collision [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_force_does_not_override_branch_collision]
- AC5: rename refuses a slug whose names would collide [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_rename_refuses_colliding_slug]
- AC6: check --title lists the collision as a failure [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_check_title_reports_branch_collision]
- AC7: new-epic and new-task refuse a name whose tree or branch, legacy double-hyphen form included, is still on disk [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_refuses_name_of_legacy_tree_or_branch_on_disk]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_naming.py`

## Interfaces

- Uses `ticket.ticket_names(root)` (the `ticket-name-lookup` part from name-lookup-parsers).
- `run_check(...)` gains the collision failures; `cmd_new_epic`, `cmd_new_task`, `cmd_rename` call it or the same helper.

## Expected outcome

No two tickets can ever produce the same branch name; each refusal names the clashing epic or task and leaves the tree and git history untouched.

## Steps

- Red: write `plugins/workbench/skills/start-development/tests/test_ticket_naming.py` with the six AC tests and run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_naming.py -q`; expect six failures.
- Green: add the collision rule in `run_check` and the rename path.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development`, then `mise run test && mise run lint` from the root; expect green.

## Notes

- Exit 3 stays reserved for the near-duplicate stop; a collision is a hard failure (exit 1) that `--force` never overrides.
- Example clash: epic `foo` task `bar-baz` and epic `foo-bar` task `baz` both give `foo-bar-baz`; epic `foo-bar` equals epic `foo` task `bar`.
