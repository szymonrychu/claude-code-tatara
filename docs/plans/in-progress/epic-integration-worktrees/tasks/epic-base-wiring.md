---
title: Epic base wiring
status: in-progress
repo: workbench
value: "Task trees, the continue gate and the run all use the epic branch as their base"
files: [plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py, plugins/workbench/skills/start-development/scripts/ticket_cmds/args.py, plugins/workbench/skills/start-development/tests/test_ticket_args.py, plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py, plugins/workbench/skills/start-development/tests/test_ticket_continue.py, plugins/workbench/skills/start-development/tests/test_run_status_fixes.py, plugins/workbench/skills/start-development/tests/test_ticket_run.py]
verify: "mise run test && mise run lint"
depends_on: [integration-tree-create, merge-contained-check]
owns: [epic-run-args]
uses: [integration-tree, contained-check]
model: sonnet
estimate: 85
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Epic base wiring

## Requirement

Wire the epic integration branch in as the base for task trees, the continue merge gate and the run args, and give epics claimed before this change an upgrade path (design D2, D4, D3, D13; interrogate verdict A, F).

- `ticket.py worktrees <epic>`: `--base` defaults to the epic's integration branch (`integration_branch(epic)`). Each task tree is created from it with `create(name, base=<epic>, repo)`. When the branch does not exist in the task's source checkout the command exits 1 with `integration branch <epic> missing in <src>; run ticket.py worktrees <epic> --integration`. `--refresh` fast-forwards against the same base.
- `ticket.py continue`: `--base` defaults to the epic branch, and the merge gate checks `_task_merged(..., base=<epic>)`. Each line is `MERGE <task> --name <branch> --base <epic> --repo <repo>`, where `<branch>` is the task's recorded `branch` when set, else `worktree_name` (so a legacy `<epic>--<task>` branch is named as it is, verdict F). The module docstring (continue_cmd.py:5) says the same.
- `ticket_cmds/args.py` writes `"baseRef": <epic slug>` and `"mainCheckout": <absolute path of the main checkout>` into the run args.
- Upgrade path (verdict F): `ticket.py worktrees <epic> --integration` creates or reuses the integration tree(s) of an epic that is already in-progress, through `ensure_integration_trees(root, epic_dir)` from integration-tree-create. It prints one `integration <path> (<verb>)` line per tree, creates no task tree, and refuses an epic that is not in-progress. This is how an epic claimed before this change, with legacy `<epic>--<task>` trees and no `<epic>` branch, gets its integration tree; its live legacy trees keep their records (single-hyphen-names) and land on `<epic>` like any other.
- Patch equivalence (verdict A): the merge gate's `_task_merged` goes through `merge.merged_into`, which falls back to `git cherry` (merge-contained-check). So after `<epic>` was rebased, a patch-equivalent task counts as merged and gets no MERGE line.
- No f-string producer `}--{` remains in continue_cmd.py.
- Updated tests: `test_ticket_args.py:88` (baseRef is the epic), `test_ticket_worktrees_refresh.py`, `test_ticket_continue.py` (gate base, the MERGE line at :178), `test_run_status_fixes.py:101` (the MERGE line), `test_ticket_run.py` (trees fork from the epic branch).

## Acceptance conditions

- AC1: ticket.py worktrees forks every task tree from the epic branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_run.py::test_worktrees_fork_from_epic_branch]
- AC2: ticket.py worktrees refuses when the integration branch is missing and names the integration command [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_run.py::test_worktrees_refuses_missing_integration_branch]
- AC3: worktrees --refresh fast-forwards task trees against the epic branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py::test_refresh_fast_forwards_against_epic_branch]
- AC4: the continue merge gate checks against the epic branch and prints the single-hyphen name and the base in each MERGE line [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue.py::test_merge_gate_uses_epic_base]
- AC5: the MERGE line carries name, base and repo [evidence: test:plugins/workbench/skills/start-development/tests/test_run_status_fixes.py::test_merge_line_has_name_and_repo]
- AC6: the run args carry baseRef equal to the epic slug and the absolute main checkout path [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_args.py::test_args_base_ref_is_epic_and_main_checkout]
- AC7: no double-hyphen producer remains in continue_cmd.py [evidence: command:! grep -n '}--{' plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py]
- AC8: the continue merge gate counts a patch-equivalent task as merged after the epic branch was rebased onto a moved main [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue.py::test_merge_gate_counts_patch_equivalent_task_as_merged]
- AC9: worktrees --integration creates the integration tree of an in-progress epic that has none and creates no task tree [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_run.py::test_worktrees_integration_creates_tree_for_in_progress_epic]
- AC10: the MERGE line names a recorded legacy double-hyphen branch as it is [evidence: test:plugins/workbench/skills/start-development/tests/test_run_status_fixes.py::test_merge_line_uses_recorded_legacy_branch]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/args.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_args.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_continue.py`
- `plugins/workbench/skills/start-development/tests/test_run_status_fixes.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_run.py`

## Interfaces

- Uses `ticket.integration_branch` and `ticket.integration_trees` (the `integration-tree` part).
- Run args gain `baseRef` (the epic slug) and `mainCheckout` (absolute path): the `epic-run-args` part, consumed by land-in-run.
- `continue --base` and `worktrees --base` defaults become the epic branch.
- `worktrees --integration` (new flag) calls `ticket.ensure_integration_trees` (the `integration-tree` part); the gate uses `merge.merged_into` with its patch-equivalence fallback (the `contained-check` part).

## Expected outcome

After the claim, `ticket.py worktrees <epic>` makes `<epic>-<task>` trees off `<epic>`, `continue` gates on `<epic>`, and `ticket.py args` hands plan-execute the epic branch and the main checkout path. An epic claimed before this change gets its integration tree from `ticket.py worktrees <epic> --integration` without losing its live legacy trees.

## Steps

- Red: add the AC tests and update the pinned base tests; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_args.py skills/start-development/tests/test_ticket_run.py -q`; expect failures on `main`.
- Green: change the defaults in `cmd_worktrees`, `continue_cmd.run` and `register`, and `build_args`.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development`, then `mise run test && mise run lint` from the root.

## Notes

- Fixtures that create task trees now need the integration branch first: call `move in-progress` (which creates it) or create the branch in the fixture.
- `create.merge_latest` fetches `origin/<epic>` and notes the miss when there is no remote branch; that is expected.
- The main checkout is `plans_root.parent.parent` in args.py (already computed as `top`).
- An epic is never re-claimed: `move in-progress` on an in-progress epic is not the upgrade path, which is why the missing-branch message names `--integration`.
