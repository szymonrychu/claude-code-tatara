---
title: Epic close sweep
status: todo
repo: workbench
value: "A delivered epic leaves no worktree or branch behind, and nothing unmerged is ever removed"
files: [plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/worktree-merge/scripts/merge.py, plugins/workbench/skills/start-development/tests/test_ticket_move.py, plugins/workbench/skills/start-development/tests/test_ticket_reap_task.py, plugins/workbench/skills/start-development/tests/test_ticket_close.py, plugins/workbench/skills/epic-worktrees-remove/SKILL.md, plugins/workbench/skills/epic-move/SKILL.md]
verify: "mise run test && mise run lint"
depends_on: [epic-base-wiring, merge-target-worktree, merge-contained-check]
owns: []
uses: [ticket-name-lookup, integration-tree, merge-target-worktree, contained-check]
model: sonnet
estimate: 90
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/epic-integration-worktrees--epic-close-sweep
branch: epic-integration-worktrees--epic-close-sweep
verified_head: ""
run: epic-integration-worktrees
provides: []
acs_for_audit: []
process_gaps: []
---

# Epic close sweep

## Requirement

Close an epic by checking the whole integration chain and removing every epic and task tree and branch (user decision U3, design D5, D9; interrogate verdict A).

- `ticket.py move <epic> done` keeps today's gates (stage review, last verdict pass, every task done and verified). It then requires every task branch (frontmatter `branch`, else `worktree_name`) to be merged into the epic branch of its source checkout (`_task_merged(src, branch, verified_head, <epic>)`). It also requires every integration branch to be merged into the trunk: meta mode the local `--base` (default `main`), component mode `origin/<tracked>` after a fetch. Each failure is one problem line naming the branch and the target, and nothing moves.
- After the move the sweep removes, in order, every task tree and its branch (target `<epic>`), then every integration tree at `<configdir>/worktrees/<epic>[/<repo>]` and branch `<epic>` (target the trunk). A legacy `.worktrees/<epic>/<repo>` tree is still swept as today. A branch is deleted only after the sweep's own `merged_into(branch, target)` check passed, with `git branch -D` so the source checkout's HEAD does not matter. Dirty or unmerged trees are left and listed with their reason. No `-landed` marker branches are created.
- Every merged check here goes through `merge.contained` (merge-contained-check): ancestry first, then patch equivalence (`git cherry <target> <head>` all `-`). This covers the move done gate (`_task_merged`), `Sweep.tree` for the tree HEAD and the branch, and the guarded delete. It matters because the close rebases `<epic>` onto a main that moved through `chore(ticket)` commits, after which no task branch or task-tree HEAD is an ancestor of `<epic>` (verdict A). Anything still not contained is listed under `left` with the reason `contained` gives, and its tree and branch stay.
- `ticket.py reap --epic <epic>` (done epic) uses the same targets. `ticket.py reap --epic <epic> --task <task>` (any phase) removes one task tree and branch when merged into `<epic>`.
- The summary JSON lists every removed tree and branch and every left item with its reason.
- `merge.cleanup` gains the guarded delete (the explicit target check, then `-D`), used by the sweep.
- `plugins/workbench/skills/epic-worktrees-remove/SKILL.md` and the close line of `plugins/workbench/skills/epic-move/SKILL.md` describe the checks and the full cleanup.
- Updated tests: `test_ticket_move.py` (477-560, the integration tree at `.worktrees/<epic>/<repo>` now at `<configdir>/worktrees/<epic>/<repo>`; 711-720), `test_ticket_reap_task.py`; new `test_ticket_close.py` with the full meta lifecycle: claim, worktrees, land each task with `merge.py --base <epic> --keep`, close with `merge.py --name <epic> --base main --keep`, then `move done`.

## Acceptance conditions

- AC1: move done refuses while a task branch is not merged into the epic branch and names it [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_move_done_refuses_task_not_in_epic]
- AC2: move done refuses while the epic branch is not merged into main and names it [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_move_done_refuses_epic_not_in_main]
- AC3: after a full meta lifecycle move done leaves only the main checkout in the worktree list and no branch of the epic [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_full_meta_lifecycle_cleans_every_tree_and_branch]
- AC4: component integration trees are swept only once merged into origin of the tracked branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_move.py::test_component_integration_tree_swept_after_origin_merge]
- AC5: a dirty or unmerged tree is left and listed with its reason [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_sweep_leaves_dirty_or_unmerged_trees]
- AC6: reap of one task removes its tree and branch once merged into the epic branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_reap_task.py::test_reap_task_merged_into_epic_branch]
- AC7: the epic-worktrees-remove skill names the integration tree cleanup [evidence: command:grep -q 'integration' plugins/workbench/skills/epic-worktrees-remove/SKILL.md]
- AC8: with main gaining a commit after the fork, the close by merge.py then move done removes every task and integration tree and branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_main_moved_after_fork_close_then_move_done_removes_all]
- AC9: a task branch with a commit that has no equivalent in the epic branch is left with the contained reason [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_sweep_lists_non_equivalent_branch_with_reason]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/worktree-merge/scripts/merge.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_move.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_reap_task.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_close.py`
- `plugins/workbench/skills/epic-worktrees-remove/SKILL.md`
- `plugins/workbench/skills/epic-move/SKILL.md`

## Interfaces

- Uses `ticket.ticket_names`, `ticket.integration_trees`, `ticket.integration_branch`, `merge.target_tree`, `merge.contained`.
- `Sweep.epic(root, epic_dir)` and `Sweep.task(...)` (existing, changed targets); `merge.cleanup(..., target=...)` guarded delete.

## Expected outcome

`ticket.py move <epic> done` on a delivered meta epic whose `<epic>` is in main leaves `git worktree list` with only the main checkout and `git branch --list '<epic>*'` empty; anything not provably merged stays and is listed.

## Steps

- Red: write `plugins/workbench/skills/start-development/tests/test_ticket_close.py` and update the pinned move and reap tests; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_close.py -q`; expect failures.
- Green: change `_move_done`, `Sweep`, `cmd_reap` and `merge.cleanup`.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only worktree-merge`, then `mise run test && mise run lint` from the root.

## Notes

- Branch deletion is the only irreversible step here; it runs only after the explicit merged check, and the commits stay reachable from `<epic>` and main (design Irreversible operations).
- A task branch is deleted before its integration branch; both checks are against refs, so the order of tree removal does not matter for correctness.
- The sweep never uses `git worktree remove --force`.
- The close itself is `ticket.py close` (epic-close-command, which runs after this task); the tests here close with `merge.py --name <epic> --base main --keep` directly.

- 2026-10-21 run epic-integration-worktrees: dependency-failed on epic-base-wiring
