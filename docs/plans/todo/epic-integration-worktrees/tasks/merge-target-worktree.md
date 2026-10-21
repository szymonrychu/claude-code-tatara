---
title: Merge target worktree
status: todo
repo: workbench
value: "Tasks land on the epic branch and epics land on main without ever switching the user's checkout"
files: [plugins/workbench/skills/worktree-merge/scripts/merge.py, plugins/workbench/skills/worktree-merge/tests/test_merge.py, plugins/workbench/skills/worktree-merge/tests/test_merge_target.py, plugins/workbench/skills/worktree-merge/tests/test_merge_suites.py, plugins/workbench/skills/worktree-merge/tests/test_merge_union.py, plugins/workbench/skills/worktree-merge/SKILL.md, plugins/workbench/agents/worktree-merger.md]
verify: "mise run test && mise run lint"
depends_on: []
owns: [merge-target-worktree]
uses: []
model: sonnet
estimate: 75
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Merge target worktree

## Requirement

Give merge.py a target-worktree mode: it lands into whichever worktree has the base branch checked out and never switches the human's main checkout (design D6; serves U2 and U3).

- `merge_back` in `plugins/workbench/skills/worktree-merge/scripts/merge.py` finds the target tree with `git worktree list --porcelain` in the source checkout: the worktree whose `branch` line is `refs/heads/<base>`. That is the integration tree for `--base <epic>` and the main checkout for `--base main`.
- It rebases the named tree onto `<base>` (doc conflicts union-merged as today). In the target tree it then runs `git merge --ff-only <name>`, the empty-directory prune, the post-merge `merged_into` check, the configured `suites`, and the new `--verify <cmd>`. Each command runs under `suite-lock.sh`; a failing `--verify` exits 4 with the 15-line tail, exactly like a failing suite, and the merge stays in place.
- No code path in merge.py runs `git checkout`. When `<base>` is checked out in no worktree it raises `WorktreeError`: `<base> is not checked out in any worktree of <src>; run ticket.py move <epic> in-progress for an integration branch, or check out <base> in the main checkout`. Nothing is rebased or merged in that case.
- `cleanup` deletes the branch with `git branch -d` run from the target tree, so a task branch merged into `<epic>` is deleted even though the main checkout's HEAD does not contain it. A refusal keeps the branch and is reported, as today.
- Epic close works: `merge.py --name <epic> --base main --keep` rebases `<epic>` onto main inside the integration tree, fast-forwards main in the main checkout, and leaves the integration tree and branch in place.
- `--assess` works with `--base <epic>`.
- Updated tests: `test_merge.py` (the main-checkout fixtures at 169-231; a case that relied on switching the checkout now asserts the refusal), `test_merge_union.py:85`, `test_merge_suites.py` (suites and `--verify` run in the target tree); new `test_merge_target.py`.
- `worktree-merge/SKILL.md` and `plugins/workbench/agents/worktree-merger.md` document target-tree landing, `--verify`, the refusal and the epic-close call, and drop "in the main checkout" wherever the target may be the integration tree.

## Acceptance conditions

- AC1: a task tree lands into the integration tree where the epic branch is checked out [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_lands_into_integration_tree]
- AC2: merge.py never switches the main checkout's branch [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_never_switches_main_checkout]
- AC3: a base checked out in no worktree is refused before any rebase [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_refuses_base_checked_out_nowhere]
- AC4: --verify runs in the target tree under the suite lock [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_verify_runs_in_target_tree]
- AC5: a failing --verify exits 4 and keeps the merge [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_verify_failure_exits_4_and_keeps_merge]
- AC6: epic close rebases the epic onto main, fast-forwards main and keeps the integration tree with --keep [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_epic_close_fast_forwards_main_keeping_integration_tree]
- AC7: cleanup deletes a branch merged into the epic branch from the target tree [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_cleanup_deletes_branch_merged_into_epic]
- AC8: no git checkout call remains in merge.py [evidence: command:! grep -n '"checkout"' plugins/workbench/skills/worktree-merge/scripts/merge.py]

## Files

- `plugins/workbench/skills/worktree-merge/scripts/merge.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge_target.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge_suites.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge_union.py`
- `plugins/workbench/skills/worktree-merge/SKILL.md`
- `plugins/workbench/agents/worktree-merger.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
