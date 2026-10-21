---
title: Single hyphen names
status: done
repo: workbench
value: "Task trees and branches carry the name the user asked for, <epic>-<task>"
files: [plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/tests/test_ticket_files.py, plugins/workbench/skills/start-development/tests/test_ticket_move.py, plugins/workbench/skills/start-development/tests/test_ticket_continue.py, plugins/workbench/skills/start-development/tests/test_run_status_fixes.py, plugins/workbench/skills/start-development/tests/test_ticket_run.py, plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py, plugins/workbench/skills/start-development/tests/test_ticket_reap_task.py]
verify: "mise run test && mise run lint"
depends_on: []
owns: []
uses: []
model: sonnet
estimate: 70
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/epic-integration-worktrees--single-hyphen-names
branch: epic-integration-worktrees--single-hyphen-names
verified_head: 29d1c794f025f8eb5a8444e9efa2cacc9aeee612
run: epic-integration-worktrees
provides: []
acs_for_audit: []
process_gaps: []
---

# Single hyphen names

## Requirement

Switch every task worktree and branch name that ticket.py produces from `<epic>--<task>` to `<epic>-<task>` (user decision U2, design D3, D13; interrogate verdict F).

- `worktree_name(epic, task)` in `plugins/workbench/skills/start-development/scripts/ticket.py` returns `f"{epic}-{task}"`. `WORKTREE_MAX` is `SLUG_MAX + 1 + SLUG_MAX` (57), and a longer name raises `TicketError` naming its length and the cap 57.
- The producers that build a task tree or branch name use `worktree_name` or the task's `branch` frontmatter: `cmd_worktrees`, the `_move_done` fallback (ticket.py:1247) and `Sweep.task` (:1457-1463).
- `cmd_worktrees` keeps both the recorded `worktree` and the recorded `branch` of a task whose recorded tree is live, whatever its name (today it rewrites `branch`). So a legacy `<epic>--<task>` tree of an epic claimed before this change keeps its record, and only a task with no live tree gets a new `<epic>-<task>` name (interrogate verdict F, design D13).
- Every test that pins the produced `--` name is updated in this task: test_ticket_files.py:84-86 (join and cap 57), test_ticket_move.py (394-395, 425-480, 549-571, 596-708, 852-856), test_ticket_worktrees_refresh.py:118,143,195-196, test_ticket_reap_task.py:20,29, test_ticket_continue.py:106-107,153-159 (tree paths and branch fixtures), test_run_status_fixes.py:64,74 and test_ticket_run.py:207,235,268.
- Not here: the name parsers and the `_counting_overlaps` fallback (name-lookup-parsers), the `continue` MERGE line (epic-base-wiring), the docs (docs-worktree-refs), the forking base and merge targets.

## Acceptance conditions

- AC1: worktree_name joins epic and task with one hyphen and rejects names over 57 characters [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_worktree_name_single_hyphen_cap_57]
- AC2: ticket.py worktrees creates and records single-hyphen trees and branches [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_move.py::test_worktrees_creates_single_hyphen_trees]
- AC3: reap of one task finds its single-hyphen tree and branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_reap_task.py::test_reap_task_mid_epic]
- AC4: move done falls back to the single-hyphen branch name when the frontmatter has none [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_move.py::test_move_done_fallback_branch_single_hyphen]
- AC5: ticket.py worktrees keeps the recorded worktree and branch of a live legacy double-hyphen tree [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py::test_worktrees_keeps_live_legacy_tree_record]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_files.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_move.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_continue.py`
- `plugins/workbench/skills/start-development/tests/test_run_status_fixes.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_run.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_reap_task.py`

## Interfaces

- `ticket.worktree_name(epic: str, task: str) -> str` and `ticket.WORKTREE_MAX = 57` (existing, changed).

## Expected outcome

`ticket.py worktrees <epic>` creates `<configdir>/worktrees/<epic>-<task>` on branch `<epic>-<task>`; reap and move done find those trees; the start-development suite is green with every produced-name test updated.

## Steps

- Red: change the pinned assertions and add the AC tests; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_files.py -q`; expect failures on the old `--` join and cap.
- Green: change `worktree_name`, `WORKTREE_MAX` and the producers listed in the requirement.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development`, then `mise run test && mise run lint` from the root.

## Notes

- Slugs contain `-` but never `--` (`slugify`, skills/_lib/common.py:124-136), so a single-hyphen name cannot be split back; never try (name-lookup-parsers adds the lookup).
- `test_run_status_fixes.py:44,56` use a fixture branch `busy--b1` from frontmatter; it is not produced by `worktree_name` and may stay.
- The `continue` MERGE line still prints the old form until epic-base-wiring; its assertions in test_ticket_continue.py:178 and test_run_status_fixes.py:101 stay as they are here.
