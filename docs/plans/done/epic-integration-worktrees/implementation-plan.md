# Epic integration worktrees implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: Common worktree path py

- Status: done
- Files: `plugins/workbench/skills/_lib/common.py`, `plugins/workbench/skills/_lib/tests/test_common.py`, `plugins/workbench/skills/git-worktrees-create/tests/test_create.py`, `plugins/workbench/skills/git-worktrees-commit/tests/test_commit.py`, `plugins/workbench/skills/git-worktrees-create/SKILL.md`, `plugins/workbench/skills/git-worktrees-commit/SKILL.md`
- Verify: `mise run test && mise run lint`
- Verified head: 36c3e72778efec20c81409eee0f273ff6cbd96fe

#### Requirement

Move the Python `worktree_path` to the config-dir layout so `git-worktrees-create` and `git-worktrees-commit` address the integration tree that the claim creates (design D2).

- `common.worktree_path(branch, repo)` in `plugins/workbench/skills/_lib/common.py` returns `workbench.worktrees_dir(repo_root()) / branch / repo` (by default `<workbench>/.claude/worktrees/<branch>/<repo>`); nothing produces `.worktrees/` any more.
- `git-worktrees-create` creates there and still skips an existing tree, so running it after `move in-progress` reports `skipped`.
- `git-worktrees-commit` commits there.
- Updated tests: `_lib/tests/test_common.py:98-100`, `git-worktrees-create/tests/test_create.py:74,103,135,145`, `git-worktrees-commit/tests/test_commit.py:25`.
- `git-worktrees-create/SKILL.md` and `git-worktrees-commit/SKILL.md` name `<configdir>/worktrees/<branch>/<repo>` and no longer mention `.worktrees/`.

#### Acceptance conditions

- AC1: worktree_path resolves under the config dir [evidence: test:plugins/workbench/skills/_lib/tests/test_common.py::test_worktree_path_under_config_dir]
- AC2: git-worktrees-create creates the tree under the config dir [evidence: test:plugins/workbench/skills/git-worktrees-create/tests/test_create.py::test_creates_worktree_under_config_dir]
- AC3: git-worktrees-create skips a tree the claim already created [evidence: test:plugins/workbench/skills/git-worktrees-create/tests/test_create.py::test_skips_existing_integration_tree]
- AC4: git-worktrees-commit commits in the config-dir tree [evidence: test:plugins/workbench/skills/git-worktrees-commit/tests/test_commit.py::test_commits_in_config_dir_worktree]
- AC5: neither skill doc mentions the old .worktrees path [evidence: command:! grep -n '\.worktrees/' plugins/workbench/skills/git-worktrees-create/SKILL.md plugins/workbench/skills/git-worktrees-commit/SKILL.md]

#### Files

- `plugins/workbench/skills/_lib/common.py`
- `plugins/workbench/skills/_lib/tests/test_common.py`
- `plugins/workbench/skills/git-worktrees-create/tests/test_create.py`
- `plugins/workbench/skills/git-worktrees-commit/tests/test_commit.py`
- `plugins/workbench/skills/git-worktrees-create/SKILL.md`
- `plugins/workbench/skills/git-worktrees-commit/SKILL.md`

#### Interfaces

- `common.worktree_path(branch: str, repo: str) -> Path` (existing, changed), built on `workbench.worktrees_dir` (plugins/workbench/scripts/lib/workbench.py:192).

#### Expected outcome

`git-worktrees-create --branch <epic> --repos <repo>` and `ticket.py move <epic> in-progress` produce or reuse the same `<configdir>/worktrees/<epic>/<repo>` tree; the shell twin is common-worktree-path-sh.

#### Steps

- Red: change the pinned paths and add the AC tests; run `cd plugins/workbench && pytest skills/_lib/tests/test_common.py -q` and the two skills' test files; expect failures on `.worktrees/`.
- Green: change `worktree_path`, importing the workbench lib the way `worktree-create/scripts/create.py` does.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only _lib && bash scripts/run-tests.sh --only git-worktrees-create && bash scripts/run-tests.sh --only git-worktrees-commit`, then `mise run test && mise run lint` from the root.

#### Notes

- The `.worktrees/` hook marker and `.gitignore` entry stay for legacy trees (design D10); do not touch them.
- `git-worktrees-create` keeps forking off `origin/<tracked>`; only the path changes.

### S2: Common worktree path sh

- Status: done
- Files: `plugins/workbench/skills/_lib/common.sh`, `plugins/workbench/skills/_lib/tests/test_common.bats`, `plugins/workbench/skills/_lib/tests/test_common.sh`, `plugins/workbench/skills/git-worktrees-push/tests/test_push.bats`, `plugins/workbench/skills/git-worktrees-push/tests/test_push.sh`, `plugins/workbench/skills/git-worktrees-push/SKILL.md`, `plugins/workbench/hooks/subagent-commit-guard.py`
- Verify: `mise run test && mise run lint`
- Verified head: 4d8582ea7c39819c0f5069be7ae5f276ed7ce516

#### Requirement

Move the shell `worktree_path` to the same config-dir layout as the Python twin (design D2).

- `worktree_path` in `plugins/workbench/skills/_lib/common.sh` prints `<configdir>/worktrees/<branch>/<repo>`, with the config dir resolved by `python3 <plugin>/scripts/lib/workbench.py config-dir` (one source of truth with `common.worktree_path`).
- `git-worktrees-push` pushes the branch checked out there.
- Updated tests: `_lib/tests/test_common.bats:93-97`, `_lib/tests/test_common.sh:101-102`, `git-worktrees-push/tests/test_push.bats:14,47,67`, `git-worktrees-push/tests/test_push.sh:54,89`.
- `git-worktrees-push/SKILL.md` names the new path. The docstring of `plugins/workbench/hooks/subagent-commit-guard.py` names task and integration trees under `<config dir>/worktrees/` and keeps `.worktrees/<branch>/<repo>` as the legacy layout.

#### Acceptance conditions

- AC1: the bats suite for common.sh and git-worktrees-push passes with the config-dir path [evidence: command:cd plugins/workbench && bats skills/_lib/tests/test_common.bats skills/git-worktrees-push/tests/test_push.bats]
- AC2: the plain shell tests for common.sh and git-worktrees-push pass [evidence: command:cd plugins/workbench && bash skills/_lib/tests/test_common.sh && bash skills/git-worktrees-push/tests/test_push.sh]
- AC3: common.sh resolves the config dir through workbench.py config-dir [evidence: command:grep -q 'config-dir' plugins/workbench/skills/_lib/common.sh]
- AC4: the push skill doc no longer names the old path [evidence: command:! grep -n '\.worktrees/' plugins/workbench/skills/git-worktrees-push/SKILL.md]

#### Files

- `plugins/workbench/skills/_lib/common.sh`
- `plugins/workbench/skills/_lib/tests/test_common.bats`
- `plugins/workbench/skills/_lib/tests/test_common.sh`
- `plugins/workbench/skills/git-worktrees-push/tests/test_push.bats`
- `plugins/workbench/skills/git-worktrees-push/tests/test_push.sh`
- `plugins/workbench/skills/git-worktrees-push/SKILL.md`
- `plugins/workbench/hooks/subagent-commit-guard.py`

#### Interfaces

- `worktree_path <branch> <repo>` in `skills/_lib/common.sh` (existing, changed); output equals `common.worktree_path` for the same tree.

#### Expected outcome

`git-worktrees-push --branch <epic> --repos <repo>` pushes from `<configdir>/worktrees/<epic>/<repo>`.

#### Steps

- Red: change the pinned paths in the four test files to the config-dir layout; run `cd plugins/workbench && bats skills/_lib/tests/test_common.bats`; expect the worktree_path test to fail.
- Green: change `worktree_path` in common.sh.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only _lib && bash scripts/run-tests.sh --only git-worktrees-push`, then `mise run test && mise run lint` (shellcheck runs in lint).

#### Notes

- `workbench.py config-dir` exists (plugins/workbench/scripts/lib/workbench.py:475); call it as `workbench.py config-dir --from <workbench root>`.
- The hook change is docstring only; `worktree_markers()` still lists `.worktrees/`.

### S3: Merge target worktree

- Status: done
- Files: `plugins/workbench/skills/worktree-merge/scripts/merge.py`, `plugins/workbench/skills/worktree-merge/tests/test_merge.py`, `plugins/workbench/skills/worktree-merge/tests/test_merge_target.py`, `plugins/workbench/skills/worktree-merge/tests/test_merge_suites.py`, `plugins/workbench/skills/worktree-merge/tests/test_merge_union.py`, `plugins/workbench/skills/worktree-merge/SKILL.md`, `plugins/workbench/agents/worktree-merger.md`
- Verify: `mise run test && mise run lint`
- Verified head: 1387f6b2dd8016222dbd6f2f2f81644cb0c4e8c8

#### Requirement

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

#### Acceptance conditions

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

#### Files

- `plugins/workbench/skills/worktree-merge/scripts/merge.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge_target.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge_suites.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge_union.py`
- `plugins/workbench/skills/worktree-merge/SKILL.md`
- `plugins/workbench/agents/worktree-merger.md`

#### Interfaces

- `merge.merge_back(name, base="main", repo=None, keep=False, start=None, suites=True, verify=None) -> dict` (existing, gains `verify` and the return fields `baseBefore`, `baseAfter`, `verification`); CLI `--verify <cmd>`.
- `merge.target_tree(src: Path, base: str) -> Path` (new; the `merge-target-worktree` part, consumed by merge-contained-check, epic-close-sweep, epic-close-command and land-in-run).
- `merge.cleanup(src, wt, name, target=None)` (existing; deletes the branch from `target` when given).

#### Expected outcome

`merge.py --name <epic>-<task> --base <epic> --keep --no-suites --verify '<cmd>'` lands a task into the integration tree only after its verify passed on the rebased tip. `merge.py --name <epic> --base main --keep --verify '<full suite and lint>'` closes the epic into main only after the full suite passed on the rebased `<epic>`, and reports main's previous SHA. Neither touches the branch the main checkout has checked out, and a red verify never moves a base.

#### Steps

- Red: write `plugins/workbench/skills/worktree-merge/tests/test_merge_target.py` with the AC tests and update the pinned main-checkout tests; run `cd plugins/workbench && bash scripts/run-tests.sh --only worktree-merge`; expect failures. For AC9, the fixture's verify command commits to the base in the target tree on its first call, so the first fast-forward fails.
- Green: add `target_tree`, run `--verify` in the rebased tree before the fast-forward with the bounded re-rebase loop, route the fast-forward, prune, check, suites and branch delete through the target tree, add the summary fields, and remove the checkout.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only worktree-merge`, then `mise run test && mise run lint` from the root.

#### Notes

- Reuse `_rebase_with_union`, `merged_into`, `prune_empty_dirs`, `run_suites`, `SUITE_LOCK` and `cleanup`.
- `git fetch origin <epic>` fails harmlessly when the epic branch has no remote; keep it a note.
- Suites stay configured by the source checkout's `.claude/workbench.json`; only where they run changes.
- The rebased named tree carries exactly the commit the target will have after the fast-forward, so verifying there is verifying the integration result (design D4).
- The nothing-to-merge path and patch equivalence belong to merge-contained-check, not here.
- AC4 and AC5 were reworded by interrogate verdict B (before it, the verify ran after the fast-forward and a failure kept the merge); see design.md "Interrogate verdict".
- `review: full` because this moves `<epic>` and main.

### S4: Plan execute epic names

- Status: done
- Files: `plugins/workbench/workflows/plan-execute.js`, `plugins/workbench/workflows/tests/plan-execute-epic.test.mjs`, `plugins/workbench/workflows/tests/plan-execute-epic-audit.test.mjs`
- Verify: `mise run test && mise run lint`
- Verified head: 772697036c84a9d79930eb78a307cb84c37a4add

#### Requirement

Make the plan-execute epic-run name check expect `<epic>-<id>`, and still accept the recorded legacy tree of an epic claimed before this change (design D3, D13; interrogate verdict F).

- In `plugins/workbench/workflows/plan-execute.js` (316-326) an epic run requires each task worktree to end in `<epic>-<id>` or `<epic>-<id>/<repo>`; the name cap is 57 characters. It also accepts the legacy `<epic>--<id>` or `<epic>--<id>/<repo>` that `ticket.py worktrees` kept for a live tree of an epic claimed before this change. The legacy separator is a named constant `LEGACY_SEP`, so no `EPIC}--` literal remains, and the legacy cap stays 58. Errors read `plan-execute: task <id> worktree <wt> must be <epic>-<id>` and `... is <n> chars; the cap is 57`.
- The header comment (line 76) says `<epic>-<id>[/<repo>]`.
- Updated tests: `plan-execute-epic.test.mjs:59-91` (the message `must be epic-x-a`, a 58-character name throws, exactly 57 passes) and `plan-execute-epic-audit.test.mjs:57,65,215-216` (branches `epic-x-parser`, `epic-x-writer`).
- Runs without `args.epic` are unchanged.
- Every new or renamed test title in these files is a single kebab token, so the AC refs run with the refRunners `--test-name-pattern {name}` command.

#### Acceptance conditions

- AC1: an epic run rejects a worktree that ends in neither the single-hyphen name nor the legacy double-hyphen name [evidence: test:plugins/workbench/workflows/tests/plan-execute-epic.test.mjs::epic-worktree-must-end-in-epic-hyphen-id]
- AC2: a 58-character single-hyphen name throws with the cap 57 [evidence: test:plugins/workbench/workflows/tests/plan-execute-epic.test.mjs::epic-worktree-name-over-57-throws]
- AC3: a 57-character name passes [evidence: test:plugins/workbench/workflows/tests/plan-execute-epic.test.mjs::epic-worktree-name-of-57-passes]
- AC4: the epic-close audit prompt lists single-hyphen branches [evidence: test:plugins/workbench/workflows/tests/plan-execute-epic-audit.test.mjs::epic-audit-lists-single-hyphen-branches]
- AC5: no double-hyphen epic name check remains in plan-execute.js [evidence: command:! grep -n 'EPIC}--' plugins/workbench/workflows/plan-execute.js]
- AC6: an epic run accepts a task whose recorded worktree is a legacy double-hyphen tree [evidence: test:plugins/workbench/workflows/tests/plan-execute-epic.test.mjs::epic-worktree-legacy-double-hyphen-accepted]

#### Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-epic.test.mjs`
- `plugins/workbench/workflows/tests/plan-execute-epic-audit.test.mjs`

#### Interfaces

- plan-execute args validation for `args.epic` (existing, changed); no new args.

#### Expected outcome

`ticket.py args` output for an epic whose trees are `<epic>-<task>` passes plan-execute's validation; a recorded legacy `<epic>--<task>` tree is still accepted, and any other name is rejected.

#### Steps

- Red: rename and update the pinned tests; run `cd plugins/workbench && node --test workflows/tests/plan-execute-epic.test.mjs workflows/tests/plan-execute-epic-audit.test.mjs`; expect failures.
- Green: change `want` and the cap in plan-execute.js.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`, then `mise run test && mise run lint` from the root.

#### Notes

- validate-tasks.mjs runs plan-execute without `args.epic`, so the lint is unaffected.

### S5: Single hyphen names

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket.py`, `plugins/workbench/skills/start-development/tests/test_ticket_files.py`, `plugins/workbench/skills/start-development/tests/test_ticket_move.py`, `plugins/workbench/skills/start-development/tests/test_ticket_continue.py`, `plugins/workbench/skills/start-development/tests/test_run_status_fixes.py`, `plugins/workbench/skills/start-development/tests/test_ticket_run.py`, `plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py`, `plugins/workbench/skills/start-development/tests/test_ticket_reap_task.py`
- Verify: `mise run test && mise run lint`
- Verified head: 29d1c794f025f8eb5a8444e9efa2cacc9aeee612

#### Requirement

Switch every task worktree and branch name that ticket.py produces from `<epic>--<task>` to `<epic>-<task>` (user decision U2, design D3, D13; interrogate verdict F).

- `worktree_name(epic, task)` in `plugins/workbench/skills/start-development/scripts/ticket.py` returns `f"{epic}-{task}"`. `WORKTREE_MAX` is `SLUG_MAX + 1 + SLUG_MAX` (57), and a longer name raises `TicketError` naming its length and the cap 57.
- The producers that build a task tree or branch name use `worktree_name` or the task's `branch` frontmatter: `cmd_worktrees`, the `_move_done` fallback (ticket.py:1247) and `Sweep.task` (:1457-1463).
- `cmd_worktrees` keeps both the recorded `worktree` and the recorded `branch` of a task whose recorded tree is live, whatever its name (today it rewrites `branch`). So a legacy `<epic>--<task>` tree of an epic claimed before this change keeps its record, and only a task with no live tree gets a new `<epic>-<task>` name (interrogate verdict F, design D13).
- Every test that pins the produced `--` name is updated in this task: test_ticket_files.py:84-86 (join and cap 57), test_ticket_move.py (394-395, 425-480, 549-571, 596-708, 852-856), test_ticket_worktrees_refresh.py:118,143,195-196, test_ticket_reap_task.py:20,29, test_ticket_continue.py:106-107,153-159 (tree paths and branch fixtures), test_run_status_fixes.py:64,74 and test_ticket_run.py:207,235,268.
- Not here: the name parsers and the `_counting_overlaps` fallback (name-lookup-parsers), the `continue` MERGE line (epic-base-wiring), the docs (docs-worktree-refs), the forking base and merge targets.

#### Acceptance conditions

- AC1: worktree_name joins epic and task with one hyphen and rejects names over 57 characters [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_worktree_name_single_hyphen_cap_57]
- AC2: ticket.py worktrees creates and records single-hyphen trees and branches [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_move.py::test_worktrees_creates_single_hyphen_trees]
- AC3: reap of one task finds its single-hyphen tree and branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_reap_task.py::test_reap_task_merged_into_epic_branch]
- AC4: move done falls back to the single-hyphen branch name when the frontmatter has none [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_move.py::test_move_done_fallback_branch_single_hyphen]
- AC5: ticket.py worktrees keeps the recorded worktree and branch of a live legacy double-hyphen tree [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py::test_worktrees_keeps_live_legacy_tree_record]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_files.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_move.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_continue.py`
- `plugins/workbench/skills/start-development/tests/test_run_status_fixes.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_run.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_reap_task.py`

#### Interfaces

- `ticket.worktree_name(epic: str, task: str) -> str` and `ticket.WORKTREE_MAX = 57` (existing, changed).

#### Expected outcome

`ticket.py worktrees <epic>` creates `<configdir>/worktrees/<epic>-<task>` on branch `<epic>-<task>`; reap and move done find those trees; the start-development suite is green with every produced-name test updated.

#### Steps

- Red: change the pinned assertions and add the AC tests; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_files.py -q`; expect failures on the old `--` join and cap.
- Green: change `worktree_name`, `WORKTREE_MAX` and the producers listed in the requirement.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development`, then `mise run test && mise run lint` from the root.

#### Notes

- Slugs contain `-` but never `--` (`slugify`, skills/_lib/common.py:124-136), so a single-hyphen name cannot be split back; never try (name-lookup-parsers adds the lookup).
- `test_run_status_fixes.py:44,56` use a fixture branch `busy--b1` from frontmatter; it is not produced by `worktree_name` and may stay.
- The `continue` MERGE line still prints the old form until epic-base-wiring; its assertions in test_ticket_continue.py:178 and test_run_status_fixes.py:101 stay as they are here.

### S6: Sweep guard

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket.py`, `plugins/workbench/skills/start-development/tests/test_ticket_close.py`, `plugins/workbench/skills/worktree-merge/scripts/merge.py`, `plugins/workbench/skills/worktree-merge/tests/test_merge_target.py`, `plugins/workbench/workflows/plan-execute.js`, `plugins/workbench/workflows/tests/plan-execute-land.test.mjs`
- Verify: `cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only worktree-merge && bash scripts/run-tests.sh --only workflows && cd ../.. && mise run lint`
- Verified head: 0c240451044087f3061aa077b3b95b80e38b43c7

#### Requirement

Close the three findings of the Epic B security review (scratchpad security-review.md); verified against the code by the orchestrator.

- MEDIUM, ticket.py `Sweep.task` / `Sweep.branch_only` (about lines 1690-1760): the swept branch comes from free-text task frontmatter (`branch = m.get("branch") or tree`) and the swept tree from frontmatter `worktree`. A task file with `branch: main` passes `contained(main, <epic>)` and the sweep runs `git branch -D main`; a `worktree` pointing at any clean linked tree (for example the integration tree) gets removed. Fix: `Sweep.task` only sweeps a branch that equals the task's own tree name (`worktree_name(epic, task)`), or its legacy `<epic>--<task>` name, or starts with `<epic>-` and is not the integration branch `<epic>` itself, and never one equal to the base, a trunk or `HEAD`. A frontmatter `branch: HEAD` (recorded by runs today) falls back to the tree name. It only removes a tree whose resolved path is under `workbench.worktrees_dir(wb)` or the legacy `<wb>/.worktrees`, and whose name is the task's tree name (or its legacy name, or a `<tree>-2` style rebased copy). Anything refused is listed under `left` with the reason `not this task's branch` or `outside the worktrees dir`, and nothing is deleted.
- LOW, merge.py `merge_back`: `wt = worktrees_dir(root) / name` with an unvalidated `name`; reject a name containing `/`, `..` or starting with `-` with exit 2 and a message, before any git call.
- LOW, plugins/workbench/workflows/plan-execute.js land prompt (about lines 2030-2040): `--name`, `--base` and `--repo` are interpolated unquoted; pass each through the existing `shq()` like the verify command and paths.
- Tests first, each seen failing before the fix.

#### Acceptance conditions

- AC1: a task whose frontmatter branch is main is left with reason "not this task's branch" and main still exists after move done [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_sweep_refuses_foreign_branch_from_frontmatter]
- AC2: a task whose frontmatter worktree points at the integration tree leaves that tree in place, listed outside the worktrees dir or not this task's tree [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_sweep_refuses_foreign_worktree_from_frontmatter]
- AC3: frontmatter branch HEAD still sweeps the task's own tree and branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_sweep_branch_head_falls_back_to_tree_name]
- AC4: merge.py rejects a --name with a slash or dot-dot with exit 2 before any git call [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_target.py::test_merge_back_rejects_unsafe_name]
- AC5: the land prompt quotes name, base and repo with shq [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_close.py`
- `plugins/workbench/skills/worktree-merge/scripts/merge.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge_target.py`
- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-land.test.mjs`

#### Interfaces

- `ticket.py:Sweep.task(root, epic, p, m)` keeps its signature; refused items go to `Sweep.leave(item, reason)`.
- `merge.py:merge_back` exits 2 on an unsafe `--name`.
- `plan-execute.js:shq` is reused, not redefined.

#### Expected outcome

`move <epic> done` and `reap` only delete the task's own trees and branches; a hostile or stale frontmatter value is listed under `left` and deletes nothing.

#### Steps

- Red: add the AC1-AC5 tests; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_close.py skills/worktree-merge/tests/test_merge_target.py -q` and `node --test workflows/tests/plan-execute-land.test.mjs`; expect the new tests to fail.
- Green: guard `Sweep.task`/`branch_only`, validate the name in `merge_back`, `shq()` the land prompt flags.
- Run the task's verify command; expect all green.

#### Ruling

- 2026-10-21 accepted: sweep-guard accepted: round-cap escalation was only the verifier's --prev-head unknown crash; hand-run verify-task.py on 0c24045 passed (clean, TDD revert red then green, AC1-AC5 met). builtin-worktree-guard landed on main ba81b5e

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S7: Close entry docs

- Status: done
- Files: `plugins/workbench/agents/worktree-merger.md`, `plugins/workbench/skills/worktree-merge/SKILL.md`, `plugins/workbench/skills/worktree-merge/tests/test_close_entry_docs.py`, `plugins/workbench/skills/start-development/scripts/ticket.py`
- Verify: `cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only worktree-merge && bash scripts/run-tests.sh --only workflows && cd ../.. && mise run lint`
- Verified head: c6f82cd125dc21f376866c469b6583880a728aa1

#### Requirement

Close the two phase 5 review findings (scratchpad epic-review.md and scope-audit.md), both verified against the code by the orchestrator.

- The epic close has one entry point, `ticket.py close <epic> --verify '<full suite and lint>'` (design D5, `references/phases-5-7.md` step 3). `plugins/workbench/agents/worktree-merger.md` "## Epic close" (about lines 89-100) and `plugins/workbench/skills/worktree-merge/SKILL.md` "## Epic close" (about lines 83-93) instead tell the merger to run `merge.py --name <epic> --base main --keep --verify ...` itself. That skips the done-task gate, the review gate and `close.json`. Rewrite both sections. The close is run by the orchestrator through `ticket.py close`. The merger is dispatched for an epic close only to resolve a rebase conflict of `<epic>` onto main inside the integration tree, and it never fast-forwards main itself. Name `ticket.py close` as the command that is rerun afterwards. No direct `merge.py --name <epic> --base main` close command remains in either file.
- `plugins/workbench/skills/start-development/scripts/ticket.py` defines `LEGACY_SEP = "--"` twice (about lines 37 and 39). Keep one definition, with an accurate comment: the old `<epic>--<task>` separator, used by the collision guard, worktree lookup and the sweep.
- Test first: a new test pins the docs, and the ticket.py change is a deletion covered by the existing suite.

#### Acceptance conditions

- AC1: worktree-merger.md and worktree-merge SKILL.md name ticket.py close as the epic close and contain no direct merge.py --name <epic> --base main close command [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_close_entry_docs.py::test_epic_close_goes_through_ticket_close]
- AC2: both docs limit the merger's epic-close role to a rebase conflict in the integration tree [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_close_entry_docs.py::test_merger_close_role_is_conflict_only]
- AC3: ticket.py defines LEGACY_SEP exactly once [evidence: command:test "$(grep -c '^LEGACY_SEP = ' plugins/workbench/skills/start-development/scripts/ticket.py)" = 1]

#### Files

- `plugins/workbench/agents/worktree-merger.md`
- `plugins/workbench/skills/worktree-merge/SKILL.md`
- `plugins/workbench/skills/worktree-merge/tests/test_close_entry_docs.py`
- `plugins/workbench/skills/start-development/scripts/ticket.py`

#### Interfaces

- `ticket_cmds/close_cmd.py` (`ticket.py close`) is the close; unchanged here.
- `ticket.py:LEGACY_SEP` keeps its value `"--"`.

#### Expected outcome

Both merger docs send the epic close through `ticket.py close`; `LEGACY_SEP` is defined once.

#### Steps

- Red: write `test_close_entry_docs.py`; run `cd plugins/workbench && pytest skills/worktree-merge/tests/test_close_entry_docs.py -q`; expect failures.
- Green: rewrite both Epic close sections; drop the duplicate `LEGACY_SEP`.
- Run the task's verify command; expect all green.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S8: Merge contained check

- Status: done
- Files: `plugins/workbench/skills/worktree-merge/scripts/merge.py`, `plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py`, `plugins/workbench/skills/worktree-merge/SKILL.md`
- Verify: `mise run test && mise run lint`
- Verified head: f0bf47ba2c859ad5bfa3a907b59b9c75edfe4050

#### Requirement

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

#### Acceptance conditions

- AC1: contained reports ancestor for a branch already in the target [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py::test_contained_ancestor]
- AC2: after the target was rebased onto a moved base, the old branch counts as merged by patch equivalence [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py::test_contained_patch_equivalent_after_rebase]
- AC3: a branch with a commit absent from the target is not contained and the reason counts the missing commits [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py::test_not_contained_names_missing_commits]
- AC4: a merge commit of the target on the branch never counts against containment [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py::test_merge_commit_ignored_by_patch_check]
- AC5: nothing to merge still runs --verify in the target tree and reports contained [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py::test_nothing_to_merge_runs_verify_in_target_tree]
- AC6: a failing verify on the nothing-to-merge path exits 4 and moves nothing [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py::test_nothing_to_merge_failing_verify_exits_4]
- AC7: the worktree-merge skill documents the patch-equivalent fallback [evidence: command:grep -q 'patch-equivalent' plugins/workbench/skills/worktree-merge/SKILL.md]

#### Files

- `plugins/workbench/skills/worktree-merge/scripts/merge.py`
- `plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py`
- `plugins/workbench/skills/worktree-merge/SKILL.md`

#### Interfaces

- `merge.contained(repo: Path, head: str, target: str) -> tuple[bool, str]` (new; the `contained-check` part, consumed by epic-base-wiring, epic-close-sweep, epic-close-command and land-outcomes).
- `merge.merged_into(repo, branch, base) -> bool` (existing; now `contained(...)[0]`).
- `merge_back(...)` nothing-to-merge return gains `contained`, `containedBy`, `verification`, `baseBefore`, `baseAfter`.

#### Expected outcome

After `<epic>` was rebased onto a moved main, every task branch and task-tree HEAD of the epic counts as merged into `<epic>` by patch equivalence, and a task already on `<epic>` is still verified in the integration tree when it is landed again.

#### Steps

- Red: write `plugins/workbench/skills/worktree-merge/tests/test_merge_contained.py` with the six AC tests (a fixture repo where `<epic>` is rebased onto a main that gained a commit after the fork); run `cd plugins/workbench && pytest skills/worktree-merge/tests/test_merge_contained.py -q`; expect failures on the patch-equivalence and nothing-to-merge cases.
- Green: add `contained`, route `merged_into` through it, and add the verify to the nothing-to-merge path through the target-tree helper from merge-target-worktree.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only worktree-merge && bash scripts/run-tests.sh --only start-development`, then `mise run test && mise run lint` from the root.

#### Notes

- `ticket._task_merged` already falls back to `git cherry` when the branch is gone (ticket.py:1220-1228); after this task both of its paths agree.
- `git cherry` sets `max_parents = 1`, so merge commits are never listed; a branch whose only extra commit is a merge of the target is contained.
- The nothing-to-merge verify runs in the target tree, which carries the same commit as the task tree when the task is an ancestor; when the task is only patch-equivalent the target tree is the one that will be tested at close, so it is the right place.

### S9: Name lookup parsers

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket.py`, `plugins/workbench/skills/start-development/tests/test_ticket_names.py`, `plugins/workbench/skills/start-development/tests/test_ticket_check.py`, `plugins/workbench/skills/start-development/tests/test_ticket_overlap_ignore.py`, `plugins/workbench/skills/start-development/tests/test_ticket_move.py`
- Verify: `cd plugins/workbench && bash scripts/run-tests.sh --only start-development && cd ../.. && mise run lint`
- Verified head: 97192abc1ba9aa7faeec3d43e698b831248f5bba

#### Requirement

Replace every name parser in ticket.py with one lookup from the tickets (design D3, D10), because `<epic>-<task>` cannot be split.

- New `ticket_names(root) -> dict[str, tuple[str, str | None]]` maps every epic slug in all three phases to `(epic, None)`, and every `<epic>-<task>` built with `worktree_name` from the epic's task files to `(epic, task)`. It is the one way code maps a tree or branch name to a ticket.
- The `run_check` live-worktree warning (ticket.py:571) resolves each live tree name through `ticket_names`, as an integration tree `<epic>` or a task tree `<epic>-<task>`. It warns when that epic is not in-progress.
- Reap-all (`cmd_reap` with no `--epic`, :1520) sweeps a directory under `<configdir>/worktrees/` only when `ticket_names` maps it to an epic that is not in-progress, or when it is a legacy `<x>--<y>` directory whose `<x>` is not an in-progress epic, so old trees stay reapable. Every other directory is left untouched and is not listed as removed.
- The `_counting_overlaps` fallback branch (:473) uses `worktree_name`; its base stays `main` (design D10).
- No f-string producer `}--{` and no `split("--")` remains in ticket.py; the legacy check uses a named constant.
- Updated tests: test_ticket_check.py:312-321 (the warning names single-hyphen trees of a real task), test_ticket_overlap_ignore.py:138, and the reap-all stray-tree tests in test_ticket_move.py; new test_ticket_names.py.

#### Acceptance conditions

- AC1: ticket_names maps every epic slug and every epic-task name to its ticket across all phases [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_names.py::test_ticket_names_maps_epics_and_tasks]
- AC2: the check warning resolves live tree names through the lookup [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_check.py::test_live_tree_warning_uses_ticket_lookup]
- AC3: reap-all leaves a directory that maps to no ticket untouched and still reaps a merged legacy double-hyphen tree [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_move.py::test_reap_all_ignores_dirs_with_no_ticket]
- AC4: the overlap fallback branch uses the single-hyphen name [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_overlap_ignore.py::test_merged_fallback_branch_single_hyphen]
- AC5: no double-hyphen producer or splitter remains in ticket.py [evidence: command:! grep -nE '\}--\{|split\("--"' plugins/workbench/skills/start-development/scripts/ticket.py]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_names.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_check.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_overlap_ignore.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_move.py`

#### Interfaces

- `ticket.ticket_names(root: Path) -> dict[str, tuple[str, str | None]]` (new; the `ticket-name-lookup` part, consumed by slug-collision-guard and epic-close-sweep).

#### Expected outcome

Nothing in ticket.py splits a name: the warning, reap-all and the overlap check all go through the tickets, and unknown directories under the worktrees dir are never touched.

#### Steps

- Red: write `plugins/workbench/skills/start-development/tests/test_ticket_names.py` and update the pinned tests; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_names.py skills/start-development/tests/test_ticket_check.py -q`; expect failures.
- Green: add `ticket_names` (built on `scan(root)`), switch the parsers and the fallback.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development`, then `mise run test && mise run lint` from the root.

#### Notes

- `scan(root)` already walks every phase and task file; reuse it.
- An integration tree `<epic>` (created by integration-tree-create) maps to `(epic, None)`, so the warning covers it too.

### S10: Integration tree create

- Status: done
- Files: `plugins/workbench/skills/worktree-create/scripts/create.py`, `plugins/workbench/skills/worktree-create/tests/test_create.py`, `plugins/workbench/skills/worktree-create/tests/test_fast_forward.py`, `plugins/workbench/skills/start-development/scripts/ticket.py`, `plugins/workbench/skills/start-development/tests/test_ticket_integration.py`, `plugins/workbench/skills/start-development/tests/test_ticket_move.py`, `plugins/workbench/skills/worktree-create/SKILL.md`, `plugins/workbench/skills/epic-move/SKILL.md`
- Verify: `mise run test && mise run lint`
- Verified head: 49daf3ed2297d08202c012f393e2af0761991bed

#### Requirement

Create the epic integration worktree when the epic is claimed (user decision U2, design D2, D8).

- `plugins/workbench/skills/worktree-create/scripts/create.py` gains `integration(epic, base="main", repo=None, start=None) -> dict` returning `{name, path, branch, base, verb, notes}` with `verb` `created` or `reused`. Destination: `worktrees_dir(root) / epic`, plus `/ repo` in component mode. When the destination is already a linked worktree of the source checkout on branch `<epic>` it is reused unchanged. When it exists as anything else the call raises `WorktreeError` naming the path. When branch `<epic>` exists, `git worktree add <dest> <epic>` reuses it. Otherwise `git worktree add -b <epic> <dest> <start>`, where `<start>` is `base` in meta mode, and in component mode `origin/<base>` when that ref resolves, else `base`. Never `--force`. CLI: `create.py --integration --name <epic> [--base main] [--repo <repo>]` prints the path, branch, base and verb.
- `ticket.py` gains `integration_trees(root, epic_dir) -> dict[str, Path]` (key `""` for the superrepo, else the repo name) and `integration_branch(epic) -> str` (the epic slug); the only place integration paths are computed.
- The claim step is one function, `ensure_integration_trees(root, epic_dir) -> list[dict]`, which returns one `integration()` result per tree. `move in-progress` calls it, and epic-base-wiring's `ticket.py worktrees <epic> --integration` reuses it for epics claimed before this change (interrogate verdict F, design D13).
- `ticket.py move <epic> in-progress`, after the blocker and check gates and before the move: the repos in scope are the README `repos` that name a `code/<repo>` submodule plus every task repo that does (`_task_repo`). With no such repo it is meta mode: one superrepo tree forked from `main`. With such repos and no task outside them it is component mode: one tree per repo, forked from that submodule's tracked branch (`.gitmodules` `submodule.<repo>.branch`, default `main`). An epic with tasks in both refuses: `epic <epic> mixes meta and component tasks; split it into two epics`. Each tree prints one line `integration <path> (<verb>)`. A creation failure exits 1, the epic stays in todo, and nothing is committed. Running the claim again reuses whatever was already created. Outside a git checkout no tree is made and the move proceeds as today.
- `plugins/workbench/skills/worktree-create/SKILL.md` documents `--integration`; `plugins/workbench/skills/epic-move/SKILL.md` says the claim creates the integration tree.
- Existing move tests in test_ticket_move.py are adapted only where the new tree changes what they observe.
- `create.fast_forward` is pinned against a non-main base (the epic branch) in `worktree-create/tests/test_fast_forward.py:37-74`.

#### Acceptance conditions

- AC1: integration() creates the meta tree on branch epic from main [evidence: test:plugins/workbench/skills/worktree-create/tests/test_create.py::test_integration_creates_meta_tree]
- AC2: integration() reuses an existing tree and an existing branch without -b [evidence: test:plugins/workbench/skills/worktree-create/tests/test_create.py::test_integration_reuses_tree_and_branch]
- AC3: integration() in component mode forks from origin of the tracked branch when it exists, else the local branch [evidence: test:plugins/workbench/skills/worktree-create/tests/test_create.py::test_integration_component_forks_tracked_branch]
- AC4: move in-progress creates the meta integration tree and prints its line [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_integration.py::test_claim_creates_meta_integration_tree]
- AC5: move in-progress creates one tree per component repo under the epic directory [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_integration.py::test_claim_creates_component_trees]
- AC6: move in-progress refuses an epic mixing meta and component tasks [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_integration.py::test_claim_refuses_mixed_epic]
- AC7: a creation failure leaves the epic in todo with nothing committed, and a second claim reuses the tree [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_integration.py::test_claim_failure_moves_nothing_and_retry_reuses]
- AC8: the worktree-create skill documents the integration flag [evidence: command:grep -q -- '--integration' plugins/workbench/skills/worktree-create/SKILL.md]
- AC9: fast_forward updates a tree behind a non-main base such as the epic branch [evidence: test:plugins/workbench/skills/worktree-create/tests/test_fast_forward.py::test_fast_forward_against_epic_base]
- AC10: the claim step is the one reusable function ensure_integration_trees [evidence: symbol:plugins/workbench/skills/start-development/scripts/ticket.py::ensure_integration_trees]

#### Files

- `plugins/workbench/skills/worktree-create/scripts/create.py`
- `plugins/workbench/skills/worktree-create/tests/test_create.py`
- `plugins/workbench/skills/worktree-create/tests/test_fast_forward.py`
- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_integration.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_move.py`
- `plugins/workbench/skills/worktree-create/SKILL.md`
- `plugins/workbench/skills/epic-move/SKILL.md`

#### Interfaces

- `create.integration(epic: str, base: str = "main", repo: str | None = None, start: Path | None = None) -> dict` (new; the `integration-tree` part).
- `ticket.integration_trees(root: Path, epic_dir: Path) -> dict[str, Path]` and `ticket.integration_branch(epic: str) -> str` (new; consumed by epic-base-wiring and epic-close-sweep).
- `ticket.ensure_integration_trees(root: Path, epic_dir: Path) -> list[dict]` (new; the claim step, consumed by epic-base-wiring's `worktrees --integration`).

#### Expected outcome

After `ticket.py move <epic> in-progress`, `git worktree list` shows `<configdir>/worktrees/<epic>` on `[<epic>]` (meta) or `<configdir>/worktrees/<epic>/<repo>` per repo (component), and a rerun of the claim on a half-created epic is safe.

#### Steps

- Red: add the three integration tests to `plugins/workbench/skills/worktree-create/tests/test_create.py` and write `plugins/workbench/skills/start-development/tests/test_ticket_integration.py`; run `cd plugins/workbench && pytest skills/worktree-create/tests/test_create.py skills/start-development/tests/test_ticket_integration.py -q` (separately if the module names clash); expect failures.
- Green: implement `integration()` and the CLI flag, then the claim step in `_move_in_progress`.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only worktree-create && bash scripts/run-tests.sh --only start-development`, then `mise run test && mise run lint` from the root.

#### Notes

- Reuse `create.branch_exists`, `create.workbench_root`, `ticket._task_repo`, `ticket._linked_worktrees`.
- Create the trees before `_git_mv` so a failure moves nothing; the claim stays idempotent because existing trees and branches are reused.
- The integration tree sits beside task trees `<epic>-<task>` under `<configdir>/worktrees/`; `create.validate_name` already refuses a duplicate name.
- Plain `git worktree add` gets no Claude Code marker, so the built-in sweep never removes it (design D1).

- 2026-10-21 run epic-integration-worktrees: dependency-failed on name-lookup-parsers

### S11: Epic base wiring

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket.py`, `plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py`, `plugins/workbench/skills/start-development/scripts/ticket_cmds/args.py`, `plugins/workbench/skills/start-development/tests/test_ticket_args.py`, `plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py`, `plugins/workbench/skills/start-development/tests/test_ticket_continue.py`, `plugins/workbench/skills/start-development/tests/test_run_status_fixes.py`, `plugins/workbench/skills/start-development/tests/test_ticket_run.py`
- Verify: `mise run test && mise run lint`
- Verified head: 7f26e08446441dd1276e5852db0a9482a7ea720a

#### Requirement

Wire the epic integration branch in as the base for task trees, the continue merge gate and the run args, and give epics claimed before this change an upgrade path (design D2, D4, D3, D13; interrogate verdict A, F).

- `ticket.py worktrees <epic>`: `--base` defaults to the epic's integration branch (`integration_branch(epic)`). Each task tree is created from it with `create(name, base=<epic>, repo)`. When the branch does not exist in the task's source checkout the command exits 1 with `integration branch <epic> missing in <src>; run ticket.py worktrees <epic> --integration`. `--refresh` fast-forwards against the same base.
- `ticket.py continue`: `--base` defaults to the epic branch, and the merge gate checks `_task_merged(..., base=<epic>)`. Each line is `MERGE <task> --name <branch> --base <epic> --repo <repo>`, where `<branch>` is the task's recorded `branch` when set, else `worktree_name` (so a legacy `<epic>--<task>` branch is named as it is, verdict F). The module docstring (continue_cmd.py:5) says the same.
- `ticket_cmds/args.py` writes `"baseRef": <epic slug>` and `"mainCheckout": <absolute path of the main checkout>` into the run args.
- Upgrade path (verdict F): `ticket.py worktrees <epic> --integration` creates or reuses the integration tree(s) of an epic that is already in-progress, through `ensure_integration_trees(root, epic_dir)` from integration-tree-create. It prints one `integration <path> (<verb>)` line per tree, creates no task tree, and refuses an epic that is not in-progress. This is how an epic claimed before this change, with legacy `<epic>--<task>` trees and no `<epic>` branch, gets its integration tree; its live legacy trees keep their records (single-hyphen-names) and land on `<epic>` like any other.
- Patch equivalence (verdict A): the merge gate's `_task_merged` goes through `merge.merged_into`, which falls back to `git cherry` (merge-contained-check). So after `<epic>` was rebased, a patch-equivalent task counts as merged and gets no MERGE line.
- No f-string producer `}--{` remains in continue_cmd.py.
- Updated tests: `test_ticket_args.py:88` (baseRef is the epic), `test_ticket_worktrees_refresh.py`, `test_ticket_continue.py` (gate base, the MERGE line at :178), `test_run_status_fixes.py:101` (the MERGE line), `test_ticket_run.py` (trees fork from the epic branch).

#### Acceptance conditions

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

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/args.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_args.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_continue.py`
- `plugins/workbench/skills/start-development/tests/test_run_status_fixes.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_run.py`

#### Interfaces

- Uses `ticket.integration_branch` and `ticket.integration_trees` (the `integration-tree` part).
- Run args gain `baseRef` (the epic slug) and `mainCheckout` (absolute path): the `epic-run-args` part, consumed by land-in-run.
- `continue --base` and `worktrees --base` defaults become the epic branch.
- `worktrees --integration` (new flag) calls `ticket.ensure_integration_trees` (the `integration-tree` part); the gate uses `merge.merged_into` with its patch-equivalence fallback (the `contained-check` part).

#### Expected outcome

After the claim, `ticket.py worktrees <epic>` makes `<epic>-<task>` trees off `<epic>`, `continue` gates on `<epic>`, and `ticket.py args` hands plan-execute the epic branch and the main checkout path. An epic claimed before this change gets its integration tree from `ticket.py worktrees <epic> --integration` without losing its live legacy trees.

#### Steps

- Red: add the AC tests and update the pinned base tests; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_args.py skills/start-development/tests/test_ticket_run.py -q`; expect failures on `main`.
- Green: change the defaults in `cmd_worktrees`, `continue_cmd.run` and `register`, and `build_args`.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development`, then `mise run test && mise run lint` from the root.

#### Notes

- Fixtures that create task trees now need the integration branch first: call `move in-progress` (which creates it) or create the branch in the fixture.
- `create.merge_latest` fetches `origin/<epic>` and notes the miss when there is no remote branch; that is expected.
- The main checkout is `plans_root.parent.parent` in args.py (already computed as `top`).
- An epic is never re-claimed: `move in-progress` on an in-progress epic is not the upgrade path, which is why the missing-branch message names `--integration`.

- 2026-10-21 run epic-integration-worktrees: dependency-failed on integration-tree-create

### S12: Epic close sweep

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket.py`, `plugins/workbench/skills/worktree-merge/scripts/merge.py`, `plugins/workbench/skills/start-development/tests/test_ticket_move.py`, `plugins/workbench/skills/start-development/tests/test_ticket_reap_task.py`, `plugins/workbench/skills/start-development/tests/test_ticket_close.py`, `plugins/workbench/skills/epic-worktrees-remove/SKILL.md`, `plugins/workbench/skills/epic-move/SKILL.md`
- Verify: `mise run test && mise run lint`
- Verified head: fe94d96b8e939cecca93bb7b7332feb4cf3ae30e

#### Requirement

Close an epic by checking the whole integration chain and removing every epic and task tree and branch (user decision U3, design D5, D9; interrogate verdict A).

- `ticket.py move <epic> done` keeps today's gates (stage review, last verdict pass, every task done and verified). It then requires every task branch (frontmatter `branch`, else `worktree_name`) to be merged into the epic branch of its source checkout (`_task_merged(src, branch, verified_head, <epic>)`). It also requires every integration branch to be merged into the trunk: meta mode the local `--base` (default `main`), component mode `origin/<tracked>` after a fetch. Each failure is one problem line naming the branch and the target, and nothing moves.
- After the move the sweep removes, in order, every task tree and its branch (target `<epic>`), then every integration tree at `<configdir>/worktrees/<epic>[/<repo>]` and branch `<epic>` (target the trunk). A legacy `.worktrees/<epic>/<repo>` tree is still swept as today. A branch is deleted only after the sweep's own `merged_into(branch, target)` check passed, with `git branch -D` so the source checkout's HEAD does not matter. Dirty or unmerged trees are left and listed with their reason. No `-landed` marker branches are created.
- Every merged check here goes through `merge.contained` (merge-contained-check): ancestry first, then patch equivalence (`git cherry <target> <head>` all `-`). This covers the move done gate (`_task_merged`), `Sweep.tree` for the tree HEAD and the branch, and the guarded delete. It matters because the close rebases `<epic>` onto a main that moved through `chore(ticket)` commits, after which no task branch or task-tree HEAD is an ancestor of `<epic>` (verdict A). Anything still not contained is listed under `left` with the reason `contained` gives, and its tree and branch stay.
- `ticket.py reap --epic <epic>` (done epic) uses the same targets. `ticket.py reap --epic <epic> --task <task>` (any phase) removes one task tree and branch when merged into `<epic>`.
- The summary JSON lists every removed tree and branch and every left item with its reason.
- `merge.cleanup` gains the guarded delete (the explicit target check, then `-D`), used by the sweep.
- `plugins/workbench/skills/epic-worktrees-remove/SKILL.md` and the close line of `plugins/workbench/skills/epic-move/SKILL.md` describe the checks and the full cleanup.
- Updated tests: `test_ticket_move.py` (477-560, the integration tree at `.worktrees/<epic>/<repo>` now at `<configdir>/worktrees/<epic>/<repo>`; 711-720), `test_ticket_reap_task.py`; new `test_ticket_close.py` with the full meta lifecycle: claim, worktrees, land each task with `merge.py --base <epic> --keep`, close with `merge.py --name <epic> --base main --keep`, then `move done`.

#### Acceptance conditions

- AC1: move done refuses while a task branch is not merged into the epic branch and names it [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_move_done_refuses_task_not_in_epic]
- AC2: move done refuses while the epic branch is not merged into main and names it [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_move_done_refuses_epic_not_in_main]
- AC3: after a full meta lifecycle move done leaves only the main checkout in the worktree list and no branch of the epic [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_full_meta_lifecycle_cleans_every_tree_and_branch]
- AC4: component integration trees are swept only once merged into origin of the tracked branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_move.py::test_component_integration_tree_swept_after_origin_merge]
- AC5: a dirty or unmerged tree is left and listed with its reason [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_sweep_leaves_dirty_or_unmerged_trees]
- AC6: reap of one task removes its tree and branch once merged into the epic branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_reap_task.py::test_reap_task_merged_into_epic_branch]
- AC7: the epic-worktrees-remove skill names the integration tree cleanup [evidence: command:grep -q 'integration' plugins/workbench/skills/epic-worktrees-remove/SKILL.md]
- AC8: with main gaining a commit after the fork, the close by merge.py then move done removes every task and integration tree and branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_main_moved_after_fork_close_then_move_done_removes_all]
- AC9: a task branch with a commit that has no equivalent in the epic branch is left with the contained reason [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close.py::test_sweep_lists_non_equivalent_branch_with_reason]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/worktree-merge/scripts/merge.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_move.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_reap_task.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_close.py`
- `plugins/workbench/skills/epic-worktrees-remove/SKILL.md`
- `plugins/workbench/skills/epic-move/SKILL.md`

#### Interfaces

- Uses `ticket.ticket_names`, `ticket.integration_trees`, `ticket.integration_branch`, `merge.target_tree`, `merge.contained`.
- `Sweep.epic(root, epic_dir)` and `Sweep.task(...)` (existing, changed targets); `merge.cleanup(..., target=...)` guarded delete.

#### Expected outcome

`ticket.py move <epic> done` on a delivered meta epic whose `<epic>` is in main leaves `git worktree list` with only the main checkout and `git branch --list '<epic>*'` empty; anything not provably merged stays and is listed.

#### Steps

- Red: write `plugins/workbench/skills/start-development/tests/test_ticket_close.py` and update the pinned move and reap tests; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_close.py -q`; expect failures.
- Green: change `_move_done`, `Sweep`, `cmd_reap` and `merge.cleanup`.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only worktree-merge`, then `mise run test && mise run lint` from the root.

#### Notes

- Branch deletion is the only irreversible step here; it runs only after the explicit merged check, and the commits stay reachable from `<epic>` and main (design Irreversible operations).
- A task branch is deleted before its integration branch; both checks are against refs, so the order of tree removal does not matter for correctness.
- The sweep never uses `git worktree remove --force`.
- The close itself is `ticket.py close` (epic-close-command, which runs after this task); the tests here close with `merge.py --name <epic> --base main --keep` directly.

- 2026-10-21 run epic-integration-worktrees: dependency-failed on epic-base-wiring

### S13: Land in run

- Status: done
- Files: `plugins/workbench/workflows/plan-execute.js`, `plugins/workbench/workflows/tests/plan-execute-land.test.mjs`, `plugins/workbench/workflows/tests/plan-execute-verify.test.mjs`, `plugins/workbench/workflows/tests/plan-execute-rulings.test.mjs`
- Verify: `mise run test && mise run lint`
- Verified head: 307ed018d5f324b7d090491d3d81acdb10d0e4ed

#### Requirement

Land each task on the epic integration branch inside the plan-execute run, and start dependents from the updated epic branch (user decision U2, design D4, D9, D10; gate question Q1).

- New arg `mainCheckout` (absolute path, documented in the header). Landing is on exactly when `args.epic` and `args.mainCheckout` are both set and the run is not `auditOnly`; every other run behaves exactly as today.
- Land step: when a task becomes released (clean and verified, process-only, triage-rejected, or released by an accept ruling) and before any dependent counts it as released, the run dispatches one agent. It has label `<name>:land:<short>`, phase `Land`, agentType `workbench:worktree-merger`, model `sonnet` and a `LAND` schema `{landed, head, conflict, verification: {command, passed, evidence}, notes}`. Its prompt runs, from the main checkout by absolute path, `python3 <pluginRoot>/skills/worktree-merge/scripts/merge.py --name <epic>-<id> --base <baseRef> [--repo <repo>] --keep --no-suites --verify <task verify>`, with `--repo` only for a component tree `<...>/<repo>`. The agent relays the script output and never runs `git checkout` in the main checkout.
- Landings are serialised: at most one land agent runs at a time in a run.
- Success (`landed` true and `verification.passed` true): the task's verification head becomes the landed head, and the return carries `landed: [{id, head}]`.
- Failure: the task ends `clean: false` with reason `land-failed` (an escalation reason) and carries the land result; its dependents end `dependency-failed`.
- Tasks that escalate or are blocked never get a land agent.
- A task released mid-run by an accept ruling lands before its dependents start.
- `dependencyLines` in landing mode: same-repo dependencies give one line: first, before anything else, run `mergeCommand(t, <baseRef>)`, which merges the epic branch that carries every landed dependency, and list the dependencies it carries. Cross-repo dependencies keep the "lands with the integration" line.
- The verifier `--base` and the reviewer merge-base diff use `baseRef`; with `baseRef` `epic-x` both prompts name `epic-x`.
- Every role prompt of a task (implement, review, fix, verify, land) names that task's one worktree path; the land prompt also names the main checkout.
- Tests: new `plan-execute-land.test.mjs`, plus added cases in `plan-execute-verify.test.mjs` and `plan-execute-rulings.test.mjs`. Existing tests stay unchanged and green.

#### Acceptance conditions

- AC1: a clean verified task in an epic run with mainCheckout gets one land agent running merge.py with the epic base, keep, no-suites and the task verify [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-dispatches-merge-into-epic]
- AC2: a dependent starts only after its dependency landed and merges the epic branch instead of the dependency branch [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-dependent-merges-epic-branch]
- AC3: two released tasks never land at the same time [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-serialised-one-at-a-time]
- AC4: a failed landing escalates the task as land-failed and fails its dependents [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-failure-escalates-and-fails-dependents]
- AC5: an escalated task gets no land agent [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-skips-escalated-tasks]
- AC6: a successful landing sets the verification head and the return lists it under landed [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-records-landed-head]
- AC7: runs without epic or without mainCheckout dispatch no land agent and keep dependency-branch merges [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-off-without-epic-or-main-checkout]
- AC8: every role prompt of a task names its one worktree [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-every-role-shares-the-task-tree]
- AC9: the verifier and reviewer diff against the epic baseRef [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify.test.mjs::verify-and-review-use-epic-base-ref]
- AC10: a task released by an accept ruling lands before its dependents start [evidence: test:plugins/workbench/workflows/tests/plan-execute-rulings.test.mjs::ruled-task-lands-before-dependents]

#### Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-land.test.mjs`
- `plugins/workbench/workflows/tests/plan-execute-verify.test.mjs`
- `plugins/workbench/workflows/tests/plan-execute-rulings.test.mjs`

#### Interfaces

- Uses `merge.py --verify` and target-tree landing (the `merge-target-worktree` part) and the run args `baseRef` and `mainCheckout` (the `epic-run-args` part).
- New in plan-execute.js: the `LAND` schema, the land step and its serialising queue (the `land-step` part, consumed by forward-merge-via-epic), the return field `landed`, the reason `land-failed` in `ESCALATE`.

#### Expected outcome

In an epic run the integration branch advances task by task as each lands, dependents build on it, and every diff a reviewer or verifier reads is the task's own change against `<epic>`.

#### Steps

- Red: write `plugins/workbench/workflows/tests/plan-execute-land.test.mjs` on the existing harness (`workflows/tests/harness.mjs`) and the two added cases; run `cd plugins/workbench && node --test workflows/tests/plan-execute-land.test.mjs`; expect failures.
- Green: add the land step in `runTasks` (between settle and release), the queue, the dependency line and the return field.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`, then `mise run test && mise run lint` from the root.

#### Notes

- Reuse `repoDir`, `mergeCommand`, `OWN_CHECKOUT_ONLY`, `verifyCommand`, `shq`, `safeAgent`; follow the forwardMerge pattern for replacing the verification head.
- A subagent's `cd` does not persist between Bash calls, so the land prompt is one `cd <mainCheckout> && python3 ...` command with absolute paths.
- The hooks treat the integration tree as an agent tree; if the merger resolves a conflict in the task tree it reruns the task verify there before re-running merge.py, or the commit guard fires once on the stale record.
- `model: opus` because this changes the run's scheduling core (release, rulings, escalation).
- merge.py verifies the rebased task tip before it fast-forwards `<epic>` (merge-target-worktree, interrogate verdict B), so a `land-failed` task never advanced `<epic>`.
- The contained, re-conflict and legacy-name outcomes of the land step are land-outcomes; fork points and diff bases after landing are fork-point-diffs.

- 2026-10-21 run epic-integration-worktrees: dependency-failed on epic-base-wiring

### S14: Epic close command

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket_cmds/close_cmd.py`, `plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py`, `plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py`, `plugins/workbench/skills/start-development/tests/test_ticket_continue.py`
- Verify: `mise run test && mise run lint`
- Verified head: e0debe5f11dd7737db06e93373335a740d489b00

#### Requirement

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

#### Acceptance conditions

- AC1: continue prints a MERGE line for a done task with no dependents that is not in the epic branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue.py::test_merge_gate_lists_every_done_task_not_in_epic]
- AC2: close refuses while a done task is not in the epic branch and prints its MERGE line [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_close_refuses_task_not_landed]
- AC3: an accepted escalated task with no dependents lands before close, and close then proceeds [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_accepted_escalated_task_lands_before_close]
- AC4: close runs the verify on the rebased tip before main moves, and a failing verify leaves main where it was [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_close_failing_verify_never_moves_main]
- AC5: close fast-forwards main, reruns the verify on main and records main's pre-fast-forward SHA in close.json [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_close_records_main_pre_ff_sha]
- AC6: with main moved after the fork, close then move done removes every tree and branch of the epic [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_lifecycle_main_moved_close_then_move_done_cleans_all]
- AC7: component-mode close checks landing only and moves nothing [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_close_component_mode_moves_nothing]
- AC8: a rerun after a successful close changes nothing and prints the recorded summary [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_close_rerun_is_idempotent]
- AC9: close_cmd.py runs no git checkout, reset or push [evidence: command:! grep -nE '"(checkout|reset|push)"' plugins/workbench/skills/start-development/scripts/ticket_cmds/close_cmd.py]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/close_cmd.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_continue.py`

#### Interfaces

- New subcommand `ticket.py close <epic> --verify <cmd> [--base main]`, registered by `ticket_cmds/close_cmd.py` through the existing command-module loader (no ticket.py change).
- New file `<epic dir>/close.json` (the close summary).
- `continue_cmd._merge_gate` (existing, changed: every done task not in `<epic>`).
- Uses `merge.merge_back(..., verify=...)` and its `baseBefore` (the `merge-target-worktree` part), `merge.contained` (the `contained-check` part), `ticket.integration_trees` and `ticket.integration_branch` (the `integration-tree` part).

#### Expected outcome

`ticket.py close <epic> --verify 'mise run test && mise run lint'` on a reviewed, passed meta epic leaves main fast-forwarded to an epic tip that passed the full suite before main moved, with main's previous SHA recorded in close.json; while any done task is not on `<epic>` it refuses and prints the MERGE lines that fix it.

#### Steps

- Red: write `plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py` and add the AC1 case to `test_ticket_continue.py`; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_close_cmd.py skills/start-development/tests/test_ticket_continue.py -q`; expect failures.
- Green: write `close_cmd.py` and widen the continue gate.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only worktree-merge`, then `mise run test && mise run lint` from the root.

#### Notes

- Load modules the way `continue_cmd.py` does (`_load`, `_sibling`); reuse the move done gates rather than restating them.
- The fixture for AC6 adds a commit to main after the fork (as `chore(ticket)` commits do in a real run), so the close rebase rewrites `<epic>` and move done must use patch equivalence.
- `review: full` because this is the one step that moves main.

- 2026-10-21 run epic-integration-worktrees: dependency-failed on epic-close-sweep

### S15: Land outcomes

- Status: done
- Files: `plugins/workbench/workflows/plan-execute.js`, `plugins/workbench/workflows/tests/plan-execute-land-outcomes.test.mjs`
- Verify: `cd plugins/workbench && bash scripts/run-tests.sh --only workflows && cd ../.. && mise run lint`
- Verified head: c5a069a2c814c53a0a8ada10af54bdf9313848c4

#### Requirement

Handle the three land outcomes that land-in-run's land step leaves open: a task already contained in `<epic>`, a rebase re-conflict, and a legacy tree name (interrogate verdict C, H, F; design D4, D13).

- Contained: when merge.py reports `contained: true` with `verification.passed` true, the land step counts the task as landed. Its head is the task tree HEAD, it is listed under `landed`, and it never ends `land-failed`.
- Re-conflict:
  - The land prompt tells the merger why re-conflicts happen: rebasing a dependent onto `<epic>` drops its merge-of-`<epic>` commit, so conflicts that merge had resolved can come back.
  - The merger resolves a conflicted file only when the resolution is unambiguous: both sides carry the same change, or one side's hunk is exactly the dependency text already on `<epic>`. It then commits in the task tree, reruns the task verify there, and reruns merge.py once.
  - Otherwise it aborts the rebase and returns `landed: false` with `conflict` listing every conflicting file. The task ends `land-failed`, and the escalation names those files.
- Legacy name: the `--name` passed to merge.py is the task's recorded worktree name: the last path component of `t.worktree`, without the `/<repo>` suffix. So a legacy `<epic>--<id>` tree recorded before the upgrade lands through the same step.
- Every new test title is a single kebab token (refRunners `--test-name-pattern {name}`).

#### Acceptance conditions

- AC1: a task already contained in the epic branch with a passing verify is landed, never land-failed [evidence: test:plugins/workbench/workflows/tests/plan-execute-land-outcomes.test.mjs::land-contained-task-counts-as-landed]
- AC2: the land prompt tells the merger to resolve unambiguous re-conflicts from a dropped merge commit and otherwise name the files [evidence: test:plugins/workbench/workflows/tests/plan-execute-land-outcomes.test.mjs::land-prompt-resolves-rebase-reconflicts]
- AC3: an unresolved conflict escalates the task as land-failed naming every conflicting file [evidence: test:plugins/workbench/workflows/tests/plan-execute-land-outcomes.test.mjs::land-conflict-escalation-names-files]
- AC4: a legacy double-hyphen tree lands with its recorded name [evidence: test:plugins/workbench/workflows/tests/plan-execute-land-outcomes.test.mjs::land-uses-recorded-legacy-tree-name]

#### Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-land-outcomes.test.mjs`

#### Interfaces

- Uses the `land-step` part (land-in-run) and merge.py's `contained`, `containedBy` and `verification` return fields (the `contained-check` part).
- Changes the land prompt and the land-result handling in plan-execute.js; no new args.

#### Expected outcome

A land never fails merely because the task is already on `<epic>`; a rebase re-conflict is either resolved unambiguously and reverified or escalated with the files named; a task recorded on a legacy `<epic>--<id>` tree lands like any other.

#### Steps

- Red: write `plugins/workbench/workflows/tests/plan-execute-land-outcomes.test.mjs` on `workflows/tests/harness.mjs` with the four cases; run `cd plugins/workbench && node --test workflows/tests/plan-execute-land-outcomes.test.mjs`; expect failures.
- Green: handle `contained`, extend the land prompt, take `--name` from the recorded worktree.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`, then `mise run test && mise run lint` from the root.

#### Notes

- The recorded worktree is `t.worktree` from the args; strip a trailing `/<repo>` (the same tail rule as plan-execute-epic-names) before taking the last component.
- The merger reruns the task verify in the task tree after a conflict fix before rerunning merge.py, or the commit guard fires once on the stale record (land-in-run Notes).

- 2026-10-21 run epic-integration-worktrees: dependency-failed on land-in-run

### S16: Slug collision guard

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket.py`, `plugins/workbench/skills/start-development/tests/test_ticket_naming.py`
- Verify: `cd plugins/workbench && bash scripts/run-tests.sh --only start-development && cd ../.. && mise run lint`
- Verified head: 72b58a39928b86aff24ddf0f13b43800016c6ad2

#### Requirement

Prevent branch-name collisions at ticket creation (design D3; interrogate verdict I), since `<epic>-<task>` cannot be split back into its parts.

- `ticket.py new-epic` refuses a slug equal to any existing `<epic>-<task>` (from `ticket_names`, all phases) with exit 1, writes and commits nothing, and prints `ticket.py: epic slug <slug> collides with the branch of task <task> in epic <epic>`; `--force` does not override it.
- `ticket.py new-task` refuses a task whose `<epic>-<task>` equals any epic slug or another epic's `<epic>-<task>` (all phases), exit 1, nothing written, the message names the clashing ticket.
- `ticket.py rename` applies the same rules to the new slug and to every `<new>-<task>` of the renamed epic.
- Names on disk count too (verdict I, matching the builder-check answer). The taken names are the tickets' names (`ticket_names`, all phases) plus every local branch of the source checkouts and every directory under `<configdir>/worktrees/`, legacy `<epic>--<task>` trees and branches included. The refused cases are: a new epic slug or a new `<epic>-<task>` equal to such a branch or directory, and a new task whose legacy name `<epic>--<task>` is still a tree or branch on disk with no ticket of its own (it would be swept as the new ticket's tree). Each refusal names the tree or branch, exits 1, writes and commits nothing, and `--force` never overrides it.
- `ticket.py check --title` reports the same clash as a failure line.
- Existing slug-uniqueness and near-duplicate behaviour is unchanged.

#### Acceptance conditions

- AC1: new-epic refuses a slug equal to an existing task branch and commits nothing [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_new_epic_refuses_slug_equal_to_task_branch]
- AC2: new-task refuses a name equal to an epic slug [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_new_task_refuses_name_equal_to_epic_slug]
- AC3: new-task refuses a name equal to another epic's task branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_new_task_refuses_name_equal_to_other_epic_task]
- AC4: --force does not override a branch collision [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_force_does_not_override_branch_collision]
- AC5: rename refuses a slug whose names would collide [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_rename_refuses_colliding_slug]
- AC6: check --title lists the collision as a failure [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_check_title_reports_branch_collision]
- AC7: new-epic and new-task refuse a name whose tree or branch, legacy double-hyphen form included, is still on disk [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_naming.py::test_refuses_name_of_legacy_tree_or_branch_on_disk]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_naming.py`

#### Interfaces

- Uses `ticket.ticket_names(root)` (the `ticket-name-lookup` part from name-lookup-parsers).
- `run_check(...)` gains the collision failures; `cmd_new_epic`, `cmd_new_task`, `cmd_rename` call it or the same helper.

#### Expected outcome

No two tickets can ever produce the same branch name; each refusal names the clashing epic or task and leaves the tree and git history untouched.

#### Steps

- Red: write `plugins/workbench/skills/start-development/tests/test_ticket_naming.py` with the six AC tests and run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_naming.py -q`; expect six failures.
- Green: add the collision rule in `run_check` and the rename path.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development`, then `mise run test && mise run lint` from the root; expect green.

#### Notes

- Exit 3 stays reserved for the near-duplicate stop; a collision is a hard failure (exit 1) that `--force` never overrides.
- Example clash: epic `foo` task `bar-baz` and epic `foo-bar` task `baz` both give `foo-bar-baz`; epic `foo-bar` equals epic `foo` task `bar`.

- 2026-10-21 run epic-integration-worktrees: dependency-failed on epic-close-sweep

### S17: Fork point diffs

- Status: done
- Files: `plugins/workbench/workflows/plan-execute.js`, `plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs`
- Verify: `cd plugins/workbench && bash scripts/run-tests.sh --only workflows && cd ../.. && mise run lint`
- Verified head: 739bb65444108908be1ec0387059ae71f9d52db0

#### Requirement

Take every diff of a task from its recorded fork point once it has landed. After landing, `merge-base(HEAD, <epic>)` is the task's own HEAD, so that diff is empty (interrogate verdict G; design D14).

- The `LAND` schema gains `base`: the `baseBefore` SHA that merge.py reports, which is the `<epic>` commit the task was rebased onto and fast-forwarded from. On a successful landing the run records it as the task's fork point. A contained landing keeps the fork point the task already had.
- New optional task arg `forkPoint` (a SHA, documented in the header) seeds the fork point for a task that landed in an earlier run.
- One helper `diffBase(t)` produces every diff base in a task's prompts: the fork point when one is recorded, else `$(git merge-base HEAD <baseRef>)` as today. It feeds:
  - the reviewer diff (plan-execute.js:933);
  - the verifier `--base` (:1016);
  - the TDD `git show <merge-base>:<path>` instruction (:1204);
  - remediation and audit re-review prompts;
  - the forward-merge re-verify.
- The return carries `landed: [{id, head, forkPoint}]` and `tasks[].forkPoint` whenever a fork point is set.
- Runs with no landing and no `forkPoint` args are unchanged; existing tests stay unchanged and green.
- Every new test title is a single kebab token.

#### Acceptance conditions

- AC1: a landed task's remediation review diffs from its fork point, not the merge-base [evidence: test:plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs::fork-point-remediation-review-diffs-from-fork-point]
- AC2: the verifier base of a landed task is its fork point [evidence: test:plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs::fork-point-verifier-base-after-landing]
- AC3: a task with forkPoint in its args uses it in every role prompt [evidence: test:plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs::fork-point-arg-seeds-diff-base]
- AC4: the return lists the fork point of each landed task [evidence: test:plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs::fork-point-in-landed-return]
- AC5: without landing or a forkPoint arg the diff base stays the merge-base with baseRef [evidence: test:plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs::fork-point-absent-keeps-merge-base]

#### Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs`

#### Interfaces

- `LAND` schema field `base` and task arg `forkPoint` (the `fork-point` part, consumed by fork-point-record and forward-merge-via-epic).
- New `diffBase(t)` in plan-execute.js; return fields `landed[].forkPoint` and `tasks[].forkPoint`.

#### Expected outcome

After a task lands, every later diff of it (remediation, audit re-review, forward-merge re-verify) shows exactly its own change from the `<epic>` commit it forked or was last rebased from.

#### Steps

- Red: write `plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs` with the five cases; run `cd plugins/workbench && node --test workflows/tests/plan-execute-fork-point.test.mjs`; expect failures.
- Green: add `base` to `LAND`, the fork-point state, `diffBase(t)` at every diff site, and the return fields.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`, then `mise run test && mise run lint` from the root.

#### Ruling

- 2026-10-21 accepted: run 3: land-outcomes, slug-collision-guard clean; fork-point-diffs accepted (gate-repeat on a false-positive parking flag: plan-execute.js:2115 is a state-describing comment, verified 739bb65); epic-close-command landed on main 4f0a59c

#### Notes

- merge.py reports `baseBefore` (merge-target-worktree); the land agent relays it as `base`.
- `git merge-base HEAD <sha>` is `<sha>` when the fork point is an ancestor of HEAD, so passing the SHA as `--base` to the verifier needs no verifier change.

- 2026-10-21 run epic-integration-worktrees: dependency-failed on land-outcomes

### S18: Fork point record

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket.py`, `plugins/workbench/skills/start-development/tests/test_ticket_fork_point.py`
- Verify: `cd plugins/workbench && bash scripts/run-tests.sh --only start-development && cd ../.. && mise run lint`
- Verified head: 7fcb7c5ee698ada342f8e6f72870d84bb079cfa1

#### Requirement

Persist each task's fork point across runs, so remediation and the epic-close audit in a later run still diff from it (interrogate verdict G; design D14).

- `ticket.py apply-run` writes task frontmatter `fork_point` from the return's `tasks[].forkPoint`, else from the matching `landed[].forkPoint`. When the return has neither, the recorded value is kept.
- `derive_tasks` exports `forkPoint` (from `fork_point`, `""` when absent), so `ticket.py args` and every args builder built on `derive_tasks` hand it to plan-execute.
- Applying the same return twice changes nothing the second time.

#### Acceptance conditions

- AC1: apply-run records fork_point from the landed return [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_fork_point.py::test_apply_run_records_fork_point]
- AC2: a return without a fork point keeps the recorded value [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_fork_point.py::test_apply_run_keeps_fork_point_when_absent]
- AC3: ticket.py args hands forkPoint to the run [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_fork_point.py::test_args_carry_fork_point]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_fork_point.py`

#### Interfaces

- Task frontmatter `fork_point` (a SHA, restricted format scalar) and `derive_tasks` field `forkPoint`; consumes the `fork-point` part from fork-point-diffs.

#### Expected outcome

`ticket.py apply-run` on a return that landed a task writes its `fork_point`, and the next `ticket.py args` (or audit args) passes it back as `forkPoint`.

#### Steps

- Red: write `plugins/workbench/skills/start-development/tests/test_ticket_fork_point.py` with the three AC tests; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_fork_point.py -q`; expect failures.
- Green: write `fork_point` in `cmd_apply_run` and export `forkPoint` in `derive_tasks`.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development`, then `mise run test && mise run lint` from the root.

#### Notes

- `_write_task` keeps any frontmatter key; no whitelist changes.
- `ticket_cmds/args.py` builds tasks from `derive_tasks`, so it needs no change.

- 2026-10-21 run epic-integration-worktrees: dependency-failed on slug-collision-guard, fork-point-diffs

- 2026-10-21 run epic-integration-worktrees: dependency-failed on fork-point-diffs

### S19: Forward merge via epic

- Status: done
- Files: `plugins/workbench/workflows/plan-execute.js`, `plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs`
- Verify: `cd plugins/workbench && bash scripts/run-tests.sh --only workflows && cd ../.. && mise run lint`
- Verified head: 7624d1d036f51b01d9c806215f24a9169fd1738c

#### Requirement

Route forward merges of a remediated dependency through the epic branch (design D4, D14; interrogate verdict C, G).

- In landing mode (`args.epic` and `args.mainCheckout` set), `forwardMerge` first lands a remediated dependency R again through the land step: R is rebased onto `<epic>`, `<epic>` is fast-forwarded, and R's verify runs in the integration tree. Each live same-repo dependent D then merges `<epic>` (`mergeCommand(d, <baseRef>)`) instead of R's branch, re-verifies, and is landed again through the land step.
- `forwardMerged` entries record `branch: <epic>`.
- If R's landing fails, R ends `land-failed` and no dependent is merged. If a dependent's merge or verify fails, it ends `forward-merge-failed` as today.
- A dependent whose tip is already contained in `<epic>` after the merge, with nothing new to land, is landed again through the contained path: merge.py runs its verify in the integration tree and the dependent counts as landed. It never ends `land-failed` (verdict C).
- The re-verify, and any re-review, of a relanded dependency or dependent diffs from its fork point (`diffBase(t)` from fork-point-diffs), never from `merge-base(HEAD, <epic>)`, which is empty once landed (verdict G).
- Outside landing mode `forwardMerge` is unchanged.
- Tests: added cases in `plan-execute-forward-merge.test.mjs`; the existing cases stay unchanged and green.

#### Acceptance conditions

- AC1: a remediated dependency is landed again before its dependents merge the epic branch [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-relands-then-merges-epic]
- AC2: a dependent merges the epic branch, not the dependency branch, and is landed again [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-dependent-merges-epic-and-relands]
- AC3: a failed landing of the remediated dependency merges no dependent [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-land-failure-stops-dependents]
- AC4: outside landing mode forward merges use the dependency branch as today [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-unchanged-without-landing]
- AC5: a dependent whose tip is already in the epic branch is relanded as contained, never land-failed [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-dependent-already-in-epic-not-land-failed]
- AC6: the forward-merge re-verify of a landed task diffs from its fork point [evidence: test:plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs::forward-merge-reverify-diffs-from-fork-point]

#### Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs`

#### Interfaces

- Uses the `land-step` part from land-in-run and the `fork-point` part from fork-point-diffs; changes `forwardMerge(latest, remediated)` and `mergePrompt(d, impl, branch)` callers.

#### Expected outcome

A remediation never leaves the integration branch behind a dependent: the dependency lands again first, and every dependent rebuilds on the updated `<epic>`.

#### Steps

- Red: add the six cases to `plugins/workbench/workflows/tests/plan-execute-forward-merge.test.mjs`; run `cd plugins/workbench && node --test workflows/tests/plan-execute-forward-merge.test.mjs`; expect the five landing-mode cases to fail.
- Green: branch `forwardMerge` on landing mode.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`, then `mise run test && mise run lint` from the root.

#### Ruling

- 2026-10-21 accepted: run 4: fork-point-record, docs-worktree-refs clean; forward-merge-via-epic accepted (gate-repeat on the same false-positive parking flag at plan-execute.js:2115, verified 7624d1d); run 3 tasks landed on main f2e2131

#### Notes

- Epic runs default to `audit: 'off'`, so forward merges in epic runs happen only when an audit runs; the tests set `audit: 'run'`.

- 2026-10-21 run epic-integration-worktrees: dependency-failed on fork-point-diffs

### S20: Docs flow phases

- Status: done
- Files: `plugins/workbench/skills/start-development/SKILL.md`, `plugins/workbench/skills/start-development/references/phase-4-execute.md`, `plugins/workbench/skills/start-development/references/phases-5-7.md`, `plugins/workbench/skills/start-development/references/multi-epic.md`, `plugins/workbench/skills/start-development/references/run-handback.md`, `plugins/workbench/skills/start-research/tests/test_start_skills_structure.py`, `plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py`, `plugins/workbench/skills/start-development/tests/test_start_development_generic.py`
- Verify: `cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only start-research && cd ../.. && mise run lint`
- Verified head: e5270eb1649c3fd84ff6b321455fb8ba1986ae98

#### Requirement

Describe the epic worktree lifecycle in the start-development flow docs (design D5, D7, D13, D14; user decisions U2, U3; interrogate verdict D, E).

- `plugins/workbench/skills/start-development/SKILL.md`. Modes: meta mode tasks land on the integration branch `<epic>`, and the epic closes by rebase plus fast-forward of the local main, with or without an `origin` remote; that replaces the meta-mode PR path, and pushing main stays with the user. Component mode keeps the MR from the integration branch. Lean path: "work in the integration worktree" names the tree `move in-progress` creates. Phase 4: the claim creates the integration tree, task trees fork from `<epic>`, and the run lands each task. Phases 5-7: the close order below. `test_skill_size.py` stays green.
- `references/phase-4-execute.md`:
  - lines 7-18: the hand-run `git-worktrees-create` step is replaced by "`move in-progress` creates it";
  - `baseRef` is the epic branch and `mainCheckout` is the main checkout;
  - landing happens in the run, `land-failed` is an escalation reason;
  - escalated tasks land after a ruling through `continue`'s `MERGE ... --base <epic>` lines and a `worktree-merger`.
  - an epic claimed before this change gets its integration tree from `ticket.py worktrees <epic> --integration`, and its live legacy double-hyphen trees keep running.
- `references/phases-5-7.md` (25-41, 59), the close order (interrogate verdict D, E); main is never moved onto an untested tip:
  1. the pass verdict;
  2. every done task is on `<epic>`: `ticket.py continue` prints no MERGE line, and that includes a task released by an accept ruling that has no dependents;
  3. meta mode: `ticket.py close <epic> --verify '<full suite and lint>'`, which does three things in order:
     - it rebases `<epic>` onto main inside the integration tree and runs the full suite and lint on the rebased tip there;
     - only when they pass, it fast-forwards main;
     - it then runs the full suite on main and records main's pre-fast-forward SHA in `close.json`.
     A rebase conflict goes to a `worktree-merger` in the integration tree, then close runs again;
  4. `ticket.py move <epic> done`, which removes every task and integration tree and branch.
  Component mode: the phase 6 MR from the integration branch, then `move done` once the MRs merge.
- `references/multi-epic.md`: each epic has its own integration tree and branch; concurrent epics never share one; each closes into main on its own, rebasing onto whatever main has become.
- `references/run-handback.md`: the `landed` return field (with each task's `forkPoint`) and the `land-failed` reason, and what the orchestrator does with each.
- Doc needle tests updated in this task: `start-research/tests/test_start_skills_structure.py:518` (Phase 4 names `baseRef`, the epic branch and `mainCheckout`), `test_ticket_flow_docs.py:81` (needles for the integration tree created by the claim and the landing in the run), and `test_start_development_generic.py:24` (the meta-mode sentences now pin the local fast-forward close, and the old "never commits" sentence is gone).

#### Acceptance conditions

- AC1: Phase 4 names baseRef as the epic branch and mainCheckout [evidence: test:plugins/workbench/skills/start-research/tests/test_start_skills_structure.py::test_phase4_names_epic_base_ref_and_main_checkout]
- AC2: the flow docs say the claim creates the integration tree and the run lands each task [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_flow_docs_integration_tree_and_landing]
- AC3: the meta-mode rule describes the local rebase and fast-forward close [evidence: test:plugins/workbench/skills/start-development/tests/test_start_development_generic.py::test_meta_mode_closes_by_local_fast_forward]
- AC4: phases-5-7 gives the close order ending in move done removing every tree and branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_close_order_documented]
- AC5: run-handback names landed and land-failed [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_run_handback_names_landing]
- AC6: SKILL.md stays within its size budget [evidence: command:cd plugins/workbench && pytest skills/start-development/tests/test_skill_size.py -q]
- AC7: phases-5-7 says close verifies the rebased epic tip before main moves, refuses while a done task is not on the epic branch, and records main's pre-fast-forward SHA [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_close_order_verifies_rebased_tip_before_main_moves]

#### Files

- `plugins/workbench/skills/start-development/SKILL.md`
- `plugins/workbench/skills/start-development/references/phase-4-execute.md`
- `plugins/workbench/skills/start-development/references/phases-5-7.md`
- `plugins/workbench/skills/start-development/references/multi-epic.md`
- `plugins/workbench/skills/start-development/references/run-handback.md`
- `plugins/workbench/skills/start-research/tests/test_start_skills_structure.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py`
- `plugins/workbench/skills/start-development/tests/test_start_development_generic.py`

#### Interfaces

- Documentation only; the needles in the three test files pin the wording.

#### Expected outcome

An orchestrator reading SKILL.md and its references runs claim, worktrees, run with in-run landing, close and cleanup in that order, in either mode, without consulting the code.

#### Steps

- Red: update the needles in the three test files to the new lifecycle and add the AC tests; run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development`; expect the needle tests to fail.
- Green: edit SKILL.md and the four references.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only start-research && cd ../.. && mise run lint`.

#### Notes

- Q2's recommended answer is the written rule; if the gate answers otherwise the orchestrator amends this task before the run.
- Keep SKILL.md short: details belong in the references (test_skill_size.py).

- 2026-10-21 run epic-integration-worktrees: dependency-failed on epic-close-sweep, epic-close-command, forward-merge-via-epic

- 2026-10-21 run epic-integration-worktrees: dependency-failed on forward-merge-via-epic

### S21: Docs readmes fallback

- Status: done
- Files: `README.md`, `plugins/workbench/README.md`, `AGENTS.md`, `scripts/harness/fallbacks/plan-execute/SKILL.md`, `plugins/workbench/skills/start-development/tests/test_release.py`, `plugins/workbench/skills/start-development/tests/test_review_flow_docs.py`, `scripts/tests/harness/test_fallbacks.py`
- Verify: `mise run test && mise run lint`
- Verified head: 60906119073242a54bdd65606893945f5759d255

#### Requirement

Describe the same lifecycle in the READMEs, AGENTS.md and the off-Claude plan-execute fallback (design D7, D1, D5; user decisions U1-U3; interrogate verdict D).

- `plugins/workbench/README.md` (202, 217): task trees are `<epic>-<task>`; the claim creates the integration tree; the move to done checks that the epic reached main and removes every tree and branch.
- `README.md`:
  - line 98: "worktree isolation" becomes "per-task git worktrees with an epic integration worktree";
  - the worktree caveat (353-357): plugin edits made in a task or integration tree take effect only after the epic merges to main and `/reload-plugins` runs.
- `AGENTS.md` template-maintenance bullet: the same caveat.
- `scripts/harness/fallbacks/plan-execute/SKILL.md`:
  - the claim creates the integration tree;
  - `ticket.py worktrees <epic>` forks task trees from `<epic>`;
  - phase 1 merges `<epic>` into the task tree, not the dependency branches;
  - phase 6 lands with `python3 ${CLAUDE_PLUGIN_ROOT}/skills/worktree-merge/scripts/merge.py --name <epic>-<task> --base <epic> --keep --verify '<verify>'` from the main checkout;
  - a close section gives the epic close order: every done task on `<epic>` (no MERGE line from `ticket.py continue`); then, in meta mode, `ticket.py close <epic> --verify '<full suite and lint>'`, which rebases `<epic>` onto main in the integration tree, runs the full suite and lint on the rebased tip, fast-forwards main only when green, runs the full suite on main and records main's pre-fast-forward SHA; then `ticket.py move <epic> done`. The section says main never moves onto an untested tip;
  - an epic claimed before this change runs `ticket.py worktrees <epic> --integration` first;
  - one sentence: never the harness's built-in worktree feature.
- Needles updated in this task: `test_release.py:144` (`<epic>-<task>`), `test_review_flow_docs.py:266-267` (README reap line, no `<epic>--<task>` form), `scripts/tests/harness/test_fallbacks.py` (the fallback names `--base <epic>`, `merge.py` and `move <epic> done`).

#### Acceptance conditions

- AC1: the plugin README names single-hyphen trees and the integration tree [evidence: test:plugins/workbench/skills/start-development/tests/test_release.py::test_readme_names_epic_task_trees_and_integration]
- AC2: the README reap line carries no double-hyphen form [evidence: test:plugins/workbench/skills/start-development/tests/test_review_flow_docs.py::test_readme_reap_task_needs_epic]
- AC3: the fallback describes forking from the epic, landing with merge.py on the epic base and the close order [evidence: test:scripts/tests/harness/test_fallbacks.py::test_plan_execute_fallback_epic_lifecycle]
- AC4: the root README and AGENTS.md say plugin edits are live only after the epic reaches main [evidence: command:grep -q 'integration' README.md && grep -q 'integration' AGENTS.md]
- AC5: no double-hyphen task name remains in the READMEs or the fallback [evidence: command:! grep -n '<epic>--<task>' README.md plugins/workbench/README.md scripts/harness/fallbacks/plan-execute/SKILL.md]
- AC6: the fallback close order verifies the rebased epic tip before main moves [evidence: test:scripts/tests/harness/test_fallbacks.py::test_plan_execute_fallback_close_order_verifies_before_main_moves]

#### Files

- `README.md`
- `plugins/workbench/README.md`
- `AGENTS.md`
- `scripts/harness/fallbacks/plan-execute/SKILL.md`
- `plugins/workbench/skills/start-development/tests/test_release.py`
- `plugins/workbench/skills/start-development/tests/test_review_flow_docs.py`
- `scripts/tests/harness/test_fallbacks.py`

#### Interfaces

- Documentation only; the fallback is hand-written source emitted by `scripts/harness/skills_emit.py:164-174`.

#### Expected outcome

Every entry point a human or another harness reads describes claim, fork, in-run landing, close and cleanup the same way as SKILL.md.

#### Steps

- Red: update the needles in the three test files; run `pytest scripts/tests/harness/test_fallbacks.py -q` and `cd plugins/workbench && pytest skills/start-development/tests/test_release.py -q`; expect failures.
- Green: edit the four docs.
- Run `mise run test && mise run lint` from the root (the root suite covers the harness emitter).

#### Notes

- AGENTS.md outside the `workbench:rules` block is hand-written; never edit the block by hand (AGENTS.md template maintenance).
- `mise run harness-setup` regenerates emitted harness copies only when a target is enabled; nothing tracked is regenerated here.

- 2026-10-21 run epic-integration-worktrees: dependency-failed on epic-close-sweep, epic-close-command, forward-merge-via-epic

- 2026-10-21 run epic-integration-worktrees: dependency-failed on forward-merge-via-epic

### S22: Docs worktree refs

- Status: done
- Files: `plugins/workbench/skills/start-development/references/worktrees.md`, `plugins/workbench/skills/start-development/references/tickets.md`, `plugins/workbench/skills/start-development/references/hooks.md`, `plugins/workbench/agents/implementer.md`, `plugins/workbench/skills/start-development/tests/test_ticket_files.py`, `plugins/workbench/skills/worktree-create/SKILL.md`, `plugins/workbench/skills/start-development/tests/test_ticket_run.py`
- Verify: `cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only workflows && cd ../.. && mise run lint`
- Verified head: cdc965c3d5981ff89cf00e9c0b0c00a7166d3ee9

#### Requirement

Describe naming, the integration tree, landing and cleanup in the worktree reference docs (design D1, D3, D7, D13, D14; user decisions U1, U2; interrogate verdict F, G, I).

- `references/worktrees.md`:
  - names: `<epic>-<task>`, at most 57 characters;
  - the integration tree: `<configdir>/worktrees/<epic>[/<repo>]` on branch `<epic>`, created by `move in-progress`;
  - task trees fork from `<epic>` and land on it in the run through a `worktree-merger` (`merge.py --base <epic> --keep --verify`);
  - every role on a task shares the task's one tree;
  - the harness built-in worktree feature is never used (keep the existing EnterWorktree guard sentence);
  - `move done` removes every tree and branch.
- `references/tickets.md`:
  - Naming table: per-task worktree and branch `<epic>-<task>`, at most 57 characters (28 + 1 + 28); the integration branch and tree `<epic>` at `<configdir>/worktrees/<epic>[/<repo>]`;
  - the collision rule of new-epic, new-task and rename, including names whose tree or branch (legacy double-hyphen form included) is still on disk;
  - `ticket.py close <epic> --verify <cmd>` and its `close.json` summary, `ticket.py worktrees <epic> --integration` for an epic claimed before this change, and the task frontmatter field `fork_point`;
  - the continue MERGE line `MERGE <task> --name <epic>-<task> --base <epic> --repo <repo>`;
  - the `worktree_name` cap 57.
- `references/hooks.md` (6-7): the guarded paths are `<configdir>/worktrees/<name>` for task and integration trees, plus the legacy `.worktrees/`.
- `plugins/workbench/agents/implementer.md`: a dependent's first step merges the epic branch; the tree is shared by every role on the task; the sentence `Do not call the built-in EnterWorktree` stays.
- `test_ticket_files.py:351` needles become `<epic>-<task>`, `57` and `Integration branch`, and assert `<epic>--<task>` is absent from tickets.md.
- `plugins/workbench/skills/worktree-create/SKILL.md` names task trees `<epic>-<task>` (the procedure's naming step), and the needle in `test_ticket_run.py:462` asserts `<epic>-<task>` is present and `<epic>--<task>` absent.

#### Acceptance conditions

- AC1: tickets.md names the single-hyphen trees, the cap 57 and the integration branch, and no double-hyphen name [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_tickets_doc_names_single_hyphen_and_integration]
- AC2: tickets.md documents the collision rule and the MERGE line with the epic base [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_tickets_doc_collision_rule_and_merge_line]
- AC3: worktrees.md describes the integration tree, landing on the epic branch and that every role shares the task tree [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_worktrees_doc_integration_lifecycle]
- AC4: the implementer agent keeps the EnterWorktree guard [evidence: command:grep -q 'Do not call the built-in EnterWorktree' plugins/workbench/agents/implementer.md plugins/workbench/skills/worktree-create/SKILL.md]
- AC5: no double-hyphen task name remains in the worktree reference docs [evidence: command:! grep -n '<epic>--<task>' plugins/workbench/skills/start-development/references/worktrees.md plugins/workbench/skills/start-development/references/tickets.md plugins/workbench/skills/start-development/references/hooks.md plugins/workbench/agents/implementer.md plugins/workbench/skills/worktree-create/SKILL.md]
- AC6: the worktree-create skill names task trees with one hyphen [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_run.py::test_worktree_create_skill_uses_epic_task_naming]
- AC7: tickets.md documents the close command, the integration upgrade flag and the fork_point field [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_tickets_doc_close_upgrade_and_fork_point]

#### Files

- `plugins/workbench/skills/start-development/references/worktrees.md`
- `plugins/workbench/skills/start-development/references/tickets.md`
- `plugins/workbench/skills/start-development/references/hooks.md`
- `plugins/workbench/agents/implementer.md`
- `plugins/workbench/skills/start-development/tests/test_ticket_files.py`
- `plugins/workbench/skills/worktree-create/SKILL.md`
- `plugins/workbench/skills/start-development/tests/test_ticket_run.py`

#### Interfaces

- Documentation only; needles in test_ticket_files.py pin the wording.

#### Expected outcome

A reader of worktrees.md and tickets.md finds one consistent naming and lifecycle that matches the code.

#### Steps

- Red: update and add the needle tests in `test_ticket_files.py`; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_files.py -q`; expect failures.
- Green: edit the five docs.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only workflows && cd ../.. && mise run lint`.

#### Notes

- `plan-execute-implementer.test.mjs:64` pins `Do not call the built-in EnterWorktree` in implementer.md; keep it.
- AC5 forbids the literal double-hyphen name in these docs: describe legacy trees as "legacy double-hyphen trees", never by the literal form.

- 2026-10-21 run epic-integration-worktrees: dependency-failed on slug-collision-guard, land-in-run, epic-base-wiring, epic-close-command, fork-point-record

- 2026-10-21 run epic-integration-worktrees: dependency-failed on slug-collision-guard, fork-point-record

- 2026-10-21 run epic-integration-worktrees: dependency-failed on fork-point-record

### S23: Builtin worktree guard

- Status: done
- Files: `scripts/tests/test_builtin_worktree_guard.py`, `plugins/workbench/skills/start-development/tests/test_repo_hygiene.py`, `plugins/workbench/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`
- Verify: `mise run test && mise run lint`
- Verified head: 61bcaef2c5435998973842fbad6a5fee53374360

#### Requirement

Pin with tests that no workbench file uses or instructs the harness built-in worktree feature (user decision U1, design D1).

- New `scripts/tests/test_builtin_worktree_guard.py` scans every tracked file (`git ls-files`) under `plugins/workbench/skills`, `agents`, `workflows`, `hooks` and `rules`, plus `scripts/harness`. It also scans every file the harness emitters render from this repo's sources into `tmp_path`, using the emitter registry the harness tests use.
- The patterns it looks for: `isolation: "worktree"`, `isolation: 'worktree'`, `isolation: worktree`, `EnterWorktree`, `ExitWorktree`, `claude --worktree`, `claude -w `, `WorktreeCreate`, `WorktreeRemove`.
- A matching line passes only when it forbids the feature (it carries a negation such as "never", "not", "no" or "do not"), or when it sits in a test file that asserts the pattern's absence. Every other match fails, naming the file, the line and the pattern.
- The test also asserts:
  - `plugins/workbench/.claude-plugin/plugin.json` declares no `WorktreeCreate` or `WorktreeRemove` hook;
  - no agent frontmatter under `plugins/workbench/agents` carries `isolation`.
- Self-test of the matcher: fixture lines `isolation: "worktree"` and `Use EnterWorktree to enter the tree` fail; `Do not call the built-in EnterWorktree` passes.
- `plugins/workbench/skills/start-development/tests/test_repo_hygiene.py` drops `isolation` from `AGENT_KEYS`, so an agent declaring it fails hygiene.
- `plugins/workbench/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` change "per-subagent worktree isolation" to "per-task git worktrees with an epic integration worktree", and the two descriptions stay equal.

#### Acceptance conditions

- AC1: no tracked plugin, harness or emitted file instructs the built-in worktree feature [evidence: test:scripts/tests/test_builtin_worktree_guard.py::test_no_builtin_worktree_instructions]
- AC2: the matcher flags instructing lines and passes forbidding ones [evidence: test:scripts/tests/test_builtin_worktree_guard.py::test_matcher_flags_use_and_passes_guards]
- AC3: plugin.json declares no WorktreeCreate or WorktreeRemove hook and no agent declares isolation [evidence: test:scripts/tests/test_builtin_worktree_guard.py::test_manifest_and_agents_declare_no_builtin_worktree]
- AC4: repo hygiene no longer allows isolation in agent frontmatter [evidence: command:! grep -n '"isolation"' plugins/workbench/skills/start-development/tests/test_repo_hygiene.py]
- AC5: the manifests describe per-task git worktrees and stay equal [evidence: test:plugins/workbench/skills/start-development/tests/test_release.py::test_marketplace_description_matches_plugin_json]
- AC6: neither manifest says worktree isolation [evidence: command:! grep -n 'worktree isolation' plugins/workbench/.claude-plugin/plugin.json .claude-plugin/marketplace.json]

#### Files

- `scripts/tests/test_builtin_worktree_guard.py`
- `plugins/workbench/skills/start-development/tests/test_repo_hygiene.py`
- `plugins/workbench/.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`

#### Interfaces

- Test only plus manifest wording; no runtime change.

#### Expected outcome

Adding any instruction to use EnterWorktree, Agent isolation, `claude --worktree` or a WorktreeCreate/WorktreeRemove hook anywhere in the plugin or its generated harness files turns `mise run test` red.

#### Steps

- Red: write the test with the matcher self-test first, and remove `isolation` from `AGENT_KEYS`; run `pytest scripts/tests/test_builtin_worktree_guard.py -q`. The self-test fails until the matcher exists; the manifest-wording AC fails until the descriptions change.
- Green: implement the matcher and change the two descriptions.
- Run `mise run test && mise run lint` from the root.

#### Notes

- Existing guard pins stay: start-research/tests/test_start_skills_structure.py:257-269, workflows/tests/plan-execute.test.mjs:349-356, plan-execute-implementer.test.mjs:64.
- plan-execute.js:348 lists `isolation` among agent() options and :1846 says "No isolation option here on purpose"; neither matches the patterns.
- Runs last so it scans the final wording of every doc task.

- 2026-10-21 run epic-integration-worktrees: dependency-failed on docs-flow-phases, docs-worktree-refs, docs-readmes-fallback

- 2026-10-21 run epic-integration-worktrees: dependency-failed on docs-flow-phases, docs-readmes-fallback

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none

## Rulings (migrated)

- fork-point-diffs: accept true, at 2026-10-21T18:03:56Z: run 3: land-outcomes, slug-collision-guard clean; fork-point-diffs accepted (gate-repeat on a false-positive parking flag: plan-execute.js:2115 is a state-describing comment, verified 739bb65); epic-close-command landed on main 4f0a59c
- forward-merge-via-epic: accept true, at 2026-10-21T19:10:21Z: run 4: fork-point-record, docs-worktree-refs clean; forward-merge-via-epic accepted (gate-repeat on the same false-positive parking flag at plan-execute.js:2115, verified 7624d1d); run 3 tasks landed on main f2e2131
- sweep-guard: accept true, at 2026-10-21T23:00:02Z: sweep-guard accepted: round-cap escalation was only the verifier's --prev-head unknown crash; hand-run verify-task.py on 0c24045 passed (clean, TDD revert red then green, AC1-AC5 met). builtin-worktree-guard landed on main ba81b5e
