---
title: Merge contained check
status: done
repo: workbench
value: "Merged checks survive the close rebase, and a task already on the epic branch is still verified"
files: [plugins/workbench/skills/worktree-merge/scripts/merge.py, plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py, plugins/workbench/skills/worktree-merge/SKILL.md]
verify: "mise run test && mise run lint"
depends_on: [merge-target-worktree]
model: sonnet
review: ""
verified_head: f0bf47ba2c859ad5bfa3a907b59b9c75edfe4050
points: 3
expected_minutes: 45
expected_tokens: 2250000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Merge contained check

## Requirement

Make every merged check in merge.py survive a rewritten base, and make the nothing-to-merge path still verify (interrogate verdict A and C; design D6, D9).

- New `contained(repo, head, target) -> tuple[bool, str]` in `plugins/workbench/skills/worktree-merge/scripts/merge.py`:
  - `(True, "ancestor")` when `git rev-list --count <target>..<head>` is 0;
  - else `(True, "patch-equivalent")` when `git cherry <target> <head>` exits 0 and every line it prints starts with `-`;
  - else `(False, "<n> commit(s) of <head> have no equivalent in <target>")`, where n counts the `+` lines.
- `merged_into(repo, branch, base)` returns `contained(repo, branch, base)[0]`. `ticket._task_merged` (the continue and move done gates), `Sweep.tree` and merge_back's post-merge check all call `merged_into`, so all of them fall back to patch equivalence when ancestry fails. This is needed because the epic close rebases `<epic>` onto a main that moved through `chore(ticket)` commits, after which no task branch or task-tree HEAD is an ancestor of `<epic>`.
- `git cherry` skips merge commits, so a dependent's merge-of-`<epic>` commit never counts against it.
- `merge_back` nothing-to-merge path: when the named tree's HEAD is contained in `<base>` (either reason), it merges nothing. It runs `--verify <cmd>` in the target tree (the worktree where `<base>` is checked out) under suite-lock.sh and returns `{merged: 0, contained: true, containedBy: <reason>, verification: {command, passed, tail}, baseBefore, baseAfter}` with `baseBefore == baseAfter`.
  - A failing verify on this path exits 4 with the 15-line tail and moves nothing.
  - Without `--verify` the path behaves as today, plus `contained: true` and `containedBy`.
- `plugins/workbench/skills/worktree-merge/SKILL.md` documents the patch-equivalent fallback and the verify on the nothing-to-merge path.

## Acceptance conditions

- AC1: contained reports ancestor for a branch already in the target [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py::test_contained_ancestor]
- AC2: after the target was rebased onto a moved base, the old branch counts as merged by patch equivalence [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py::test_contained_patch_equivalent_after_rebase]
- AC3: a branch with a commit absent from the target is not contained and the reason counts the missing commits [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py::test_not_contained_names_missing_commits]
- AC4: a merge commit of the target on the branch never counts against containment [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py::test_merge_commit_ignored_by_patch_check]
- AC5: nothing to merge still runs --verify in the target tree and reports contained [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py::test_nothing_to_merge_runs_verify_in_target_tree]
- AC6: a failing verify on the nothing-to-merge path exits 4 and moves nothing [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py::test_nothing_to_merge_failing_verify_exits_4]
- AC7: the worktree-merge skill documents the patch-equivalent fallback [evidence: command:grep -q 'patch-equivalent' plugins/workbench/skills/worktree-merge/SKILL.md]

## Files

- `plugins/workbench/skills/worktree-merge/scripts/merge.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py`
- `plugins/workbench/skills/worktree-merge/SKILL.md`

## Interfaces

- `merge.contained(repo: Path, head: str, target: str) -> tuple[bool, str]` (new; the `contained-check` part, consumed by epic-base-wiring, epic-close-sweep, epic-close-command and land-outcomes).
- `merge.merged_into(repo, branch, base) -> bool` (existing; now `contained(...)[0]`).
- `merge_back(...)` nothing-to-merge return gains `contained`, `containedBy`, `verification`, `baseBefore`, `baseAfter`.

## Expected outcome

After `<epic>` was rebased onto a moved main, every task branch and task-tree HEAD of the epic counts as merged into `<epic>` by patch equivalence, and a task already on `<epic>` is still verified in the integration tree when it is landed again.

## Steps

- Red: write `plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py` with the six AC tests (a fixture repo where `<epic>` is rebased onto a main that gained a commit after the fork); run `cd plugins/workbench && pytest skills/worktree-merge/tests/test_merge_contained.py -q`; expect failures on the patch-equivalence and nothing-to-merge cases.
- Green: add `contained`, route `merged_into` through it, and add the verify to the nothing-to-merge path through the target-tree helper from merge-target-worktree.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only worktree-merge && bash scripts/run-tests.sh --only start-development`, then `mise run test && mise run lint` from the root.

## Notes

- `ticket._task_merged` already falls back to `git cherry` when the branch is gone (ticket.py:1220-1228); after this task both of its paths agree.
- `git cherry` sets `max_parents = 1`, so merge commits are never listed; a branch whose only extra commit is a merge of the target is contained.
- The nothing-to-merge verify runs in the target tree, which carries the same commit as the task tree when the task is an ancestor; when the task is only patch-equivalent the target tree is the one that will be tested at close, so it is the right place.
