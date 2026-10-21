---
title: Sweep guard
status: escalated
repo: workbench
value: "Closing an epic can never delete a trunk branch or a tree that is not the task's own"
files: [plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/tests/test_ticket_close.py, plugins/workbench/skills/worktree-merge/scripts/merge.py, plugins/workbench/skills/worktree-merge/tests/test_merge_target.py, plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-land.test.mjs]
verify: "cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only worktree-merge && bash scripts/run-tests.sh --only workflows && cd ../.. && mise run lint"
depends_on: []
owns: []
uses: []
model: sonnet
estimate: 45
actual: ""
review: full
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/epic-integration-worktrees--sweep-guard
branch: epic-integration-worktrees--sweep-guard
verified_head: 0c240451044087f3061aa077b3b95b80e38b43c7
run: epic-integration-worktrees
provides: []
acs_for_audit: []
process_gaps: [tests.red and verification.evidence were never filled with the revert-and-run output the verifier asks for]
---

# Sweep guard

## Requirement

Close the three findings of the Epic B security review (scratchpad security-review.md); verified against the code by the orchestrator.

- MEDIUM, ticket.py `Sweep.task` / `Sweep.branch_only` (about lines 1690-1760): the swept branch comes from free-text task frontmatter (`branch = m.get("branch") or tree`) and the swept tree from frontmatter `worktree`. A task file with `branch: main` passes `contained(main, <epic>)` and the sweep runs `git branch -D main`; a `worktree` pointing at any clean linked tree (for example the integration tree) gets removed. Fix: `Sweep.task` only sweeps a branch that equals the task's own tree name (`worktree_name(epic, task)`), or its legacy `<epic>--<task>` name, or starts with `<epic>-` and is not the integration branch `<epic>` itself, and never one equal to the base, a trunk or `HEAD`. A frontmatter `branch: HEAD` (recorded by runs today) falls back to the tree name. It only removes a tree whose resolved path is under `workbench.worktrees_dir(wb)` or the legacy `<wb>/.worktrees`, and whose name is the task's tree name (or its legacy name, or a `<tree>-2` style rebased copy). Anything refused is listed under `left` with the reason `not this task's branch` or `outside the worktrees dir`, and nothing is deleted.
- LOW, merge.py `merge_back`: `wt = worktrees_dir(root) / name` with an unvalidated `name`; reject a name containing `/`, `..` or starting with `-` with exit 2 and a message, before any git call.
- LOW, plugins/workbench/workflows/plan-execute.js land prompt (about lines 2030-2040): `--name`, `--base` and `--repo` are interpolated unquoted; pass each through the existing `shq()` like the verify command and paths.
- Tests first, each seen failing before the fix.

## Acceptance conditions

- AC1: a task whose frontmatter branch is main is left with reason "not this task's branch" and main still exists after move done [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_sweep_refuses_foreign_branch_from_frontmatter]
- AC2: a task whose frontmatter worktree points at the integration tree leaves that tree in place, listed outside the worktrees dir or not this task's tree [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_sweep_refuses_foreign_worktree_from_frontmatter]
- AC3: frontmatter branch HEAD still sweeps the task's own tree and branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_sweep_branch_head_falls_back_to_tree_name]
- AC4: merge.py rejects a --name with a slash or dot-dot with exit 2 before any git call [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_merge_back_rejects_unsafe_name]
- AC5: the land prompt quotes name, base and repo with shq [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_close.py`
- `plugins/workbench/skills/worktree-merge/scripts/merge.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge_target.py`
- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-land.test.mjs`

## Interfaces

- `ticket.py:Sweep.task(root, epic, p, m)` keeps its signature; refused items go to `Sweep.leave(item, reason)`.
- `merge.py:merge_back` exits 2 on an unsafe `--name`.
- `plan-execute.js:shq` is reused, not redefined.

## Expected outcome

`move <epic> done` and `reap` only delete the task's own trees and branches; a hostile or stale frontmatter value is listed under `left` and deletes nothing.

## Steps

- Red: add the AC1-AC5 tests; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_close.py skills/worktree-merge/tests/test_merge_target.py -q` and `node --test workflows/tests/plan-execute-land.test.mjs`; expect the new tests to fail.
- Green: guard `Sweep.task`/`branch_only`, validate the name in `merge_back`, `shq()` the land prompt flags.
- Run the task's verify command; expect all green.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
