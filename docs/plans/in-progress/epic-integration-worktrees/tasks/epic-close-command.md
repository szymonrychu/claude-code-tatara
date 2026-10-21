---
title: Epic close command
status: in-progress
repo: workbench
value: "main only ever moves to an epic tip that passed the full suite, after every done task landed"
files: [plugins/workbench/skills/start-development/scripts/ticket_cmds/close_cmd.py, plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py, plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py, plugins/workbench/skills/start-development/tests/test_ticket_continue.py]
verify: "mise run test && mise run lint"
depends_on: [epic-close-sweep, merge-contained-check]
owns: []
uses: [contained-check, merge-target-worktree, integration-tree]
model: sonnet
estimate: 85
actual: ""
review: full
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/epic-integration-worktrees--epic-close-command
branch: epic-integration-worktrees--epic-close-command
verified_head: ""
run: ""
provides: []
---

# Epic close command

## Requirement

One command closes an epic into main in the order the interrogate verdict fixes, and the continue gate shows every task that still has to land (interrogate verdict D, E; design D5).

- `ticket.py continue` merge gate (`ticket_cmds/continue_cmd.py`): when the epic's integration branch exists in the task's source checkout, it prints a `MERGE` line and exits 2 for EVERY done task whose branch is not contained in `<epic>`, not only for dependencies of open tasks. The branch is the frontmatter `branch`, else `worktree_name`; containment is `_task_merged`, so ancestry or patch equivalence. An epic with no integration branch keeps today's dependency-only rule.
- New `ticket_cmds/close_cmd.py` registers `ticket.py close <epic> --verify <cmd> [--base main]`, run from the main checkout. `--verify` is the repo's full suite and lint. Steps, in order:
  1. Refuse unless the epic is in-progress at stage review with a last verdict pass (reuse the move done gates).
  2. Refuse with exit 2 while any done task is not contained in `<epic>`, printing the same `MERGE` lines; nothing is rebased.
  3. Meta mode: call `merge.merge_back(name=<epic>, base=<base>, keep=True, verify=<cmd>)`. It rebases `<epic>` onto `<base>` in the integration tree, runs `<cmd>` on the rebased tip there, and fast-forwards `<base>` in the main checkout only when that passed. A rebase conflict exits 1 with merge.py's message (resolve it with a `worktree-merger` in the integration tree, then rerun close). A failing verify exits 4. In both cases `<base>` does not move.
  4. After the fast-forward, run `<cmd>` again in the main checkout under suite-lock.sh.
  5. Write `<epic dir>/close.json` as `{epic, base, baseBefore, baseAfter, epicTip, integrationVerify: {command, passed}, mainVerify: {command, passed, tail}, at}`, where `baseBefore` is main's pre-fast-forward SHA from merge.py's summary. Commit it with `commit_ticket_change`, print it, and print the next step `ticket.py move <epic> done`. A failing main verify still writes close.json (with `passed: false`), exits 4, and names `baseBefore` as the commit main was at before the close.
  6. Component mode: steps 1 and 2 only, then print `component mode: close through the phase 6 MR from <epic>` and exit 0, with nothing rebased or fast-forwarded.
- A rerun after a successful close, when `<epic>` is already contained in `<base>` and close.json exists, changes nothing and prints the recorded close.json.
- `close` never runs `git checkout`, `reset` or `push`.

## Acceptance conditions

- AC1: continue prints a MERGE line for a done task with no dependents that is not in the epic branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue.py::test_merge_gate_lists_every_done_task_not_in_epic]
- AC2: close refuses while a done task is not in the epic branch and prints its MERGE line [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_close_refuses_task_not_landed]
- AC3: an accepted escalated task with no dependents lands before close, and close then proceeds [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_accepted_escalated_task_lands_before_close]
- AC4: close runs the verify on the rebased tip before main moves, and a failing verify leaves main where it was [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_close_failing_verify_never_moves_main]
- AC5: close fast-forwards main, reruns the verify on main and records main's pre-fast-forward SHA in close.json [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_close_records_main_pre_ff_sha]
- AC6: with main moved after the fork, close then move done removes every tree and branch of the epic [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_lifecycle_main_moved_close_then_move_done_cleans_all]
- AC7: component-mode close checks landing only and moves nothing [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_close_component_mode_moves_nothing]
- AC8: a rerun after a successful close changes nothing and prints the recorded summary [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_close_rerun_is_idempotent]
- AC9: close_cmd.py runs no git checkout, reset or push [evidence: command:! grep -nE '"(checkout|reset|push)"' plugins/workbench/skills/start-development/scripts/ticket_cmds/close_cmd.py]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/close_cmd.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_continue.py`

## Interfaces

- New subcommand `ticket.py close <epic> --verify <cmd> [--base main]`, registered by `ticket_cmds/close_cmd.py` through the existing command-module loader (no ticket.py change).
- New file `<epic dir>/close.json` (the close summary).
- `continue_cmd._merge_gate` (existing, changed: every done task not in `<epic>`).
- Uses `merge.merge_back(..., verify=...)` and its `baseBefore` (the `merge-target-worktree` part), `merge.contained` (the `contained-check` part), `ticket.integration_trees` and `ticket.integration_branch` (the `integration-tree` part).

## Expected outcome

`ticket.py close <epic> --verify 'mise run test && mise run lint'` on a reviewed, passed meta epic leaves main fast-forwarded to an epic tip that passed the full suite before main moved, with main's previous SHA recorded in close.json; while any done task is not on `<epic>` it refuses and prints the MERGE lines that fix it.

## Steps

- Red: write `plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py` and add the AC1 case to `test_ticket_continue.py`; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_close_cmd.py skills/start-development/tests/test_ticket_continue.py -q`; expect failures.
- Green: write `close_cmd.py` and widen the continue gate.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only worktree-merge`, then `mise run test && mise run lint` from the root.

## Notes

- Load modules the way `continue_cmd.py` does (`_load`, `_sibling`); reuse the move done gates rather than restating them.
- The fixture for AC6 adds a commit to main after the fork (as `chore(ticket)` commits do in a real run), so the close rebase rewrites `<epic>` and move done must use patch equivalence.
- `review: full` because this is the one step that moves main.
