---
title: Common worktree path sh
status: in-progress
repo: workbench
value: git-worktrees-push pushes the same integration tree the claim creates
files: [plugins/workbench/skills/_lib/common.sh, plugins/workbench/skills/_lib/tests/test_common.bats, plugins/workbench/skills/_lib/tests/test_common.sh, plugins/workbench/skills/git-worktrees-push/tests/test_push.bats, plugins/workbench/skills/git-worktrees-push/tests/test_push.sh, plugins/workbench/skills/git-worktrees-push/SKILL.md, plugins/workbench/hooks/subagent-commit-guard.py]
verify: "mise run test && mise run lint"
depends_on: []
owns: []
uses: []
model: sonnet
estimate: 45
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/epic-integration-worktrees--common-worktree-path-sh
branch: epic-integration-worktrees--common-worktree-path-sh
verified_head: ""
run: ""
provides: []
---

# Common worktree path sh

## Requirement

Move the shell `worktree_path` to the same config-dir layout as the Python twin (design D2).

- `worktree_path` in `plugins/workbench/skills/_lib/common.sh` prints `<configdir>/worktrees/<branch>/<repo>`, with the config dir resolved by `python3 <plugin>/scripts/lib/workbench.py config-dir` (one source of truth with `common.worktree_path`).
- `git-worktrees-push` pushes the branch checked out there.
- Updated tests: `_lib/tests/test_common.bats:93-97`, `_lib/tests/test_common.sh:101-102`, `git-worktrees-push/tests/test_push.bats:14,47,67`, `git-worktrees-push/tests/test_push.sh:54,89`.
- `git-worktrees-push/SKILL.md` names the new path. The docstring of `plugins/workbench/hooks/subagent-commit-guard.py` names task and integration trees under `<config dir>/worktrees/` and keeps `.worktrees/<branch>/<repo>` as the legacy layout.

## Acceptance conditions

- AC1: the bats suite for common.sh and git-worktrees-push passes with the config-dir path [evidence: command:cd plugins/workbench && bats skills/_lib/tests/test_common.bats skills/git-worktrees-push/tests/test_push.bats]
- AC2: the plain shell tests for common.sh and git-worktrees-push pass [evidence: command:cd plugins/workbench && bash skills/_lib/tests/test_common.sh && bash skills/git-worktrees-push/tests/test_push.sh]
- AC3: common.sh resolves the config dir through workbench.py config-dir [evidence: command:grep -q 'config-dir' plugins/workbench/skills/_lib/common.sh]
- AC4: the push skill doc no longer names the old path [evidence: command:! grep -n '\.worktrees/' plugins/workbench/skills/git-worktrees-push/SKILL.md]

## Files

- `plugins/workbench/skills/_lib/common.sh`
- `plugins/workbench/skills/_lib/tests/test_common.bats`
- `plugins/workbench/skills/_lib/tests/test_common.sh`
- `plugins/workbench/skills/git-worktrees-push/tests/test_push.bats`
- `plugins/workbench/skills/git-worktrees-push/tests/test_push.sh`
- `plugins/workbench/skills/git-worktrees-push/SKILL.md`
- `plugins/workbench/hooks/subagent-commit-guard.py`

## Interfaces

- `worktree_path <branch> <repo>` in `skills/_lib/common.sh` (existing, changed); output equals `common.worktree_path` for the same tree.

## Expected outcome

`git-worktrees-push --branch <epic> --repos <repo>` pushes from `<configdir>/worktrees/<epic>/<repo>`.

## Steps

- Red: change the pinned paths in the four test files to the config-dir layout; run `cd plugins/workbench && bats skills/_lib/tests/test_common.bats`; expect the worktree_path test to fail.
- Green: change `worktree_path` in common.sh.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only _lib && bash scripts/run-tests.sh --only git-worktrees-push`, then `mise run test && mise run lint` (shellcheck runs in lint).

## Notes

- `workbench.py config-dir` exists (plugins/workbench/scripts/lib/workbench.py:475); call it as `workbench.py config-dir --from <workbench root>`.
- The hook change is docstring only; `worktree_markers()` still lists `.worktrees/`.
