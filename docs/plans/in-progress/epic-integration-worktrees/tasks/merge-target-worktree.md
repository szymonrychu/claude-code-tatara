---
title: Merge target worktree
status: done
repo: workbench
value: "Tasks land on the epic branch and epics land on main without ever switching the user's checkout"
files: [plugins/workbench/skills/worktree-merge/scripts/merge.py, plugins/workbench/skills/worktree-merge/tests/test_merge.py, plugins/workbench/skills/worktree-merge/tests/test_merge_target.py, plugins/workbench/skills/worktree-merge/tests/test_merge_suites.py, plugins/workbench/skills/worktree-merge/tests/test_merge_union.py, plugins/workbench/skills/worktree-merge/SKILL.md, plugins/workbench/agents/worktree-merger.md]
verify: "mise run test && mise run lint"
depends_on: []
owns: [merge-target-worktree]
uses: []
model: sonnet
estimate: 90
actual: ""
review: full
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/epic-integration-worktrees--merge-target-worktree
branch: epic-integration-worktrees--merge-target-worktree
verified_head: 1387f6b2dd8016222dbd6f2f2f81644cb0c4e8c8
run: epic-integration-worktrees
provides: []
acs_for_audit: []
process_gaps: []
---

# Merge target worktree

## Requirement

Give merge.py a target-worktree mode. It lands into whichever worktree has the base branch checked out, never switches the human's main checkout, and never advances the base onto an unverified tip (design D6; interrogate verdict B, D, H; serves U2 and U3).

- **Target tree.** `merge_back` in `plugins/workbench/skills/worktree-merge/scripts/merge.py` finds the target tree with `git worktree list --porcelain` in the source checkout: the worktree whose `branch` line is `refs/heads/<base>`. That is the integration tree for `--base <epic>` and the main checkout for `--base main`.
- **Verify before the fast-forward** (verdict B):
  - It rebases the named tree onto `<base>` (doc conflicts union-merged as today). It then runs the new `--verify <cmd>` in the rebased named tree under suite-lock.sh, before anything moves.
  - Only on a green verify does it run, in the target tree: `git merge --ff-only <name>`, the empty-directory prune, the post-merge `merged_into` check and the configured `suites` (each under suite-lock.sh).
  - A failing `--verify` exits 4 with the 15-line tail and never advances `<base>`: the target tree and `<base>` stay at their old commit, and the named tree keeps its rebased commits.
  - If the fast-forward fails because `<base>` moved after the rebase, it rebases again onto the new `<base>` and reruns `--verify`, up to 3 attempts in all. After that it raises `WorktreeError` naming the attempts. `<base>` never moves onto a tip the last verify did not pass.
  - A failing configured suite after the fast-forward exits 4 as today.
- **Summary.** The returned dict gains `baseBefore` (the `<base>` SHA before the fast-forward, which is the commit the final rebase was onto), `baseAfter` and `verification: {command, passed, tail}`. For the epic close, `baseBefore` is main's pre-fast-forward SHA (verdict D).
- **No checkout.** No code path in merge.py runs `git checkout`. When `<base>` is checked out in no worktree, it raises `WorktreeError`: `<base> is not checked out in any worktree of <src>; run ticket.py move <epic> in-progress for an integration branch, or check out <base> in the main checkout`. Nothing is rebased or merged in that case.
- **Cleanup.** `cleanup` deletes the branch with `git branch -d`, run from the target tree, so a task branch merged into `<epic>` is deleted even though the main checkout's HEAD does not contain it. A refusal keeps the branch and is reported, as today.
- **Epic close** (verdict D). `merge.py --name <epic> --base main --keep --verify '<full suite and lint>'`, in order:
  1. rebases `<epic>` onto main inside the integration tree;
  2. runs the full suite and lint on the rebased tip there;
  3. only then fast-forwards main in the main checkout and runs the configured suites there.
  The integration tree and branch stay in place.
- `--assess` works with `--base <epic>`.
- **Tests.** Updated: `test_merge.py` (the main-checkout fixtures at 169-231; a case that relied on switching the checkout now asserts the refusal), `test_merge_union.py:85`, `test_merge_suites.py` (suites run in the target tree after the fast-forward). New: `test_merge_target.py`.
- **Docs.** `worktree-merge/SKILL.md` and `plugins/workbench/agents/worktree-merger.md` document:
  - target-tree landing;
  - `--verify` before the fast-forward, and the re-rebase when the base moved;
  - the refusal;
  - the epic-close call and its order;
  - and they drop "in the main checkout" wherever the target may be the integration tree.
- **Re-conflicts** (verdict H). `worktree-merger.md` also says that a rebase drops a dependent's merge-of-`<epic>` commit (a dropped merge commit), so conflicts that merge had resolved can reappear. The merger resolves the unambiguous ones (both sides carry the same change, or one side is exactly the dependency text already on `<epic>`), reruns the task verify, then reruns merge.py. Otherwise it reports `land-failed` with the conflicting files named.

## Acceptance conditions

- AC1: a task tree lands into the integration tree where the epic branch is checked out [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_lands_into_integration_tree]
- AC2: merge.py never switches the main checkout's branch [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_never_switches_main_checkout]
- AC3: a base checked out in no worktree is refused before any rebase [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_refuses_base_checked_out_nowhere]
- AC4: --verify runs under the suite lock in the rebased tree before the fast-forward [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_verify_runs_in_rebased_tree_before_fast_forward]
- AC5: a failing --verify exits 4 and never advances the base [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_verify_failure_exits_4_and_never_advances_base]
- AC6: epic close rebases the epic onto main, fast-forwards main and keeps the integration tree with --keep [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_epic_close_fast_forwards_main_keeping_integration_tree]
- AC7: cleanup deletes a branch merged into the epic branch from the target tree [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_cleanup_deletes_branch_merged_into_epic]
- AC8: no git checkout call remains in merge.py [evidence: command:! grep -n '"checkout"' plugins/workbench/skills/worktree-merge/scripts/merge.py]
- AC9: when the base moves between the rebase and the fast-forward, merge.py rebases again and reverifies before it fast-forwards [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_base_moved_rebases_and_reverifies]
- AC10: epic close verifies the rebased epic tip before main moves and the summary records main's pre-fast-forward SHA [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_epic_close_verifies_rebased_tip_and_records_base_before]
- AC11: the merger agent doc covers re-conflicts from a dropped merge commit [evidence: command:grep -q 'dropped merge commit' plugins/workbench/agents/worktree-merger.md]

## Files

- `plugins/workbench/skills/worktree-merge/scripts/merge.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge_target.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge_suites.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge_union.py`
- `plugins/workbench/skills/worktree-merge/SKILL.md`
- `plugins/workbench/agents/worktree-merger.md`

## Interfaces

- `merge.merge_back(name, base="main", repo=None, keep=False, start=None, suites=True, verify=None) -> dict` (existing, gains `verify` and the return fields `baseBefore`, `baseAfter`, `verification`); CLI `--verify <cmd>`.
- `merge.target_tree(src: Path, base: str) -> Path` (new; the `merge-target-worktree` part, consumed by merge-contained-check, epic-close-sweep, epic-close-command and land-in-run).
- `merge.cleanup(src, wt, name, target=None)` (existing; deletes the branch from `target` when given).

## Expected outcome

`merge.py --name <epic>-<task> --base <epic> --keep --no-suites --verify '<cmd>'` lands a task into the integration tree only after its verify passed on the rebased tip. `merge.py --name <epic> --base main --keep --verify '<full suite and lint>'` closes the epic into main only after the full suite passed on the rebased `<epic>`, and reports main's previous SHA. Neither touches the branch the main checkout has checked out, and a red verify never moves a base.

## Steps

- Red: write `plugins/workbench/skills/worktree-merge/tests/test_merge_target.py` with the AC tests and update the pinned main-checkout tests; run `cd plugins/workbench && bash scripts/run-tests.sh --only worktree-merge`; expect failures. For AC9, the fixture's verify command commits to the base in the target tree on its first call, so the first fast-forward fails.
- Green: add `target_tree`, run `--verify` in the rebased tree before the fast-forward with the bounded re-rebase loop, route the fast-forward, prune, check, suites and branch delete through the target tree, add the summary fields, and remove the checkout.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only worktree-merge`, then `mise run test && mise run lint` from the root.

## Notes

- Reuse `_rebase_with_union`, `merged_into`, `prune_empty_dirs`, `run_suites`, `SUITE_LOCK` and `cleanup`.
- `git fetch origin <epic>` fails harmlessly when the epic branch has no remote; keep it a note.
- Suites stay configured by the source checkout's `.claude/workbench.json`; only where they run changes.
- The rebased named tree carries exactly the commit the target will have after the fast-forward, so verifying there is verifying the integration result (design D4).
- The nothing-to-merge path and patch equivalence belong to merge-contained-check, not here.
- AC4 and AC5 were reworded by interrogate verdict B (before it, the verify ran after the fast-forward and a failure kept the merge); see design.md "Interrogate verdict".
- `review: full` because this moves `<epic>` and main.
