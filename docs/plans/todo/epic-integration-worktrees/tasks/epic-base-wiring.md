---
title: Epic base wiring
status: todo
repo: workbench
value: "Task trees, the continue gate and the run all use the epic branch as their base"
files: [plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py, plugins/workbench/skills/start-development/scripts/ticket_cmds/args.py, plugins/workbench/skills/start-development/tests/test_ticket_args.py, plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py, plugins/workbench/skills/start-development/tests/test_ticket_continue.py, plugins/workbench/skills/start-development/tests/test_run_status_fixes.py, plugins/workbench/skills/start-development/tests/test_ticket_run.py]
verify: "mise run test && mise run lint"
depends_on: [integration-tree-create]
owns: [epic-run-args]
uses: [integration-tree]
model: sonnet
estimate: 60
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

Wire the epic integration branch in as the base for task trees, the continue merge gate and the run args (design D2, D4, D3).

- `ticket.py worktrees <epic>`: `--base` defaults to the epic's integration branch (`integration_branch(epic)`). Each task tree is created from it with `create(name, base=<epic>, repo)`. When the branch does not exist in the task's source checkout the command exits 1 with `integration branch <epic> missing in <src>; run ticket.py move <epic> in-progress`. `--refresh` fast-forwards against the same base.
- `ticket.py continue`: `--base` defaults to the epic branch, and the merge gate checks `_task_merged(..., base=<epic>)`. Each line is `MERGE <task> --name <epic>-<task> --base <epic> --repo <repo>`, with the name from `worktree_name`. The module docstring (continue_cmd.py:5) says the same.
- `ticket_cmds/args.py` writes `"baseRef": <epic slug>` and `"mainCheckout": <absolute path of the main checkout>` into the run args.
- No f-string producer `}--{` remains in continue_cmd.py.
- Updated tests: `test_ticket_args.py:88` (baseRef is the epic), `test_ticket_worktrees_refresh.py`, `test_ticket_continue.py` (gate base, the MERGE line at :178), `test_run_status_fixes.py:101` (the MERGE line), `test_ticket_run.py` (trees fork from the epic branch).

## Acceptance conditions

- AC1: ticket.py worktrees forks every task tree from the epic branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_run.py::test_worktrees_fork_from_epic_branch]
- AC2: ticket.py worktrees refuses when the integration branch is missing and names the claim command [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_run.py::test_worktrees_refuses_missing_integration_branch]
- AC3: worktrees --refresh fast-forwards task trees against the epic branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py::test_refresh_fast_forwards_against_epic_branch]
- AC4: the continue merge gate checks against the epic branch and prints the single-hyphen name and the base in each MERGE line [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue.py::test_merge_gate_uses_epic_base]
- AC5: the MERGE line carries name, base and repo [evidence: test:plugins/workbench/skills/start-development/tests/test_run_status_fixes.py::test_merge_line_has_name_and_repo]
- AC6: the run args carry baseRef equal to the epic slug and the absolute main checkout path [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_args.py::test_args_base_ref_is_epic_and_main_checkout]
- AC7: no double-hyphen producer remains in continue_cmd.py [evidence: command:! grep -n '}--{' plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py]

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

## Expected outcome

After the claim, `ticket.py worktrees <epic>` makes `<epic>-<task>` trees off `<epic>`, `continue` gates on `<epic>`, and `ticket.py args` hands plan-execute the epic branch and the main checkout path.

## Steps

- Red: add the AC tests and update the pinned base tests; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_args.py skills/start-development/tests/test_ticket_run.py -q`; expect failures on `main`.
- Green: change the defaults in `cmd_worktrees`, `continue_cmd.run` and `register`, and `build_args`.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development`, then `mise run test && mise run lint` from the root.

## Notes

- Fixtures that create task trees now need the integration branch first: call `move in-progress` (which creates it) or create the branch in the fixture.
- `create.merge_latest` fetches `origin/<epic>` and notes the miss when there is no remote branch; that is expected.
- The main checkout is `plans_root.parent.parent` in args.py (already computed as `top`).
