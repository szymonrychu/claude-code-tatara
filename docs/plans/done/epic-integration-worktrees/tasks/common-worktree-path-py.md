---
title: Common worktree path py
status: done
repo: workbench
value: git-worktrees-create and -commit work on the same integration tree the claim creates
files: [plugins/workbench/skills/_lib/common.py, plugins/workbench/skills/_lib/tests/test_common.py, plugins/workbench/skills/git-worktrees-create/tests/test_create.py, plugins/workbench/skills/git-worktrees-commit/tests/test_commit.py, plugins/workbench/skills/git-worktrees-create/SKILL.md, plugins/workbench/skills/git-worktrees-commit/SKILL.md]
verify: "mise run test && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: 36c3e72778efec20c81409eee0f273ff6cbd96fe
points: 3
expected_minutes: 40
expected_tokens: 2250000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Common worktree path py

## Requirement

Move the Python `worktree_path` to the config-dir layout so `git-worktrees-create` and `git-worktrees-commit` address the integration tree that the claim creates (design D2).

- `common.worktree_path(branch, repo)` in `plugins/workbench/skills/_lib/common.py` returns `workbench.worktrees_dir(repo_root()) / branch / repo` (by default `<workbench>/.claude/worktrees/<branch>/<repo>`); nothing produces `.worktrees/` any more.
- `git-worktrees-create` creates there and still skips an existing tree, so running it after `move in-progress` reports `skipped`.
- `git-worktrees-commit` commits there.
- Updated tests: `_lib/tests/test_common.py:98-100`, `git-worktrees-create/tests/test_create.py:74,103,135,145`, `git-worktrees-commit/tests/test_commit.py:25`.
- `git-worktrees-create/SKILL.md` and `git-worktrees-commit/SKILL.md` name `<configdir>/worktrees/<branch>/<repo>` and no longer mention `.worktrees/`.

## Acceptance conditions

- AC1: worktree_path resolves under the config dir [evidence: test:plugins/workbench/skills/_lib/tests/test_common.py::test_worktree_path_under_config_dir]
- AC2: git-worktrees-create creates the tree under the config dir [evidence: test:plugins/workbench/skills/git-worktrees-create/tests/test_create.py::test_creates_worktree_under_config_dir]
- AC3: git-worktrees-create skips a tree the claim already created [evidence: test:plugins/workbench/skills/git-worktrees-create/tests/test_create.py::test_skips_existing_integration_tree]
- AC4: git-worktrees-commit commits in the config-dir tree [evidence: test:plugins/workbench/skills/git-worktrees-commit/tests/test_commit.py::test_commits_in_config_dir_worktree]
- AC5: neither skill doc mentions the old .worktrees path [evidence: command:! grep -n '\.worktrees/' plugins/workbench/skills/git-worktrees-create/SKILL.md plugins/workbench/skills/git-worktrees-commit/SKILL.md]

## Files

- `plugins/workbench/skills/_lib/common.py`
- `plugins/workbench/skills/_lib/tests/test_common.py`
- `plugins/workbench/skills/git-worktrees-create/tests/test_create.py`
- `plugins/workbench/skills/git-worktrees-commit/tests/test_commit.py`
- `plugins/workbench/skills/git-worktrees-create/SKILL.md`
- `plugins/workbench/skills/git-worktrees-commit/SKILL.md`

## Interfaces

- `common.worktree_path(branch: str, repo: str) -> Path` (existing, changed), built on `workbench.worktrees_dir` (plugins/workbench/scripts/lib/workbench.py:192).

## Expected outcome

`git-worktrees-create --branch <epic> --repos <repo>` and `ticket.py move <epic> in-progress` produce or reuse the same `<configdir>/worktrees/<epic>/<repo>` tree; the shell twin is common-worktree-path-sh.

## Steps

- Red: change the pinned paths and add the AC tests; run `cd plugins/workbench && pytest skills/_lib/tests/test_common.py -q` and the two skills' test files; expect failures on `.worktrees/`.
- Green: change `worktree_path`, importing the workbench lib the way `worktree-create/scripts/create.py` does.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only _lib && bash scripts/run-tests.sh --only git-worktrees-create && bash scripts/run-tests.sh --only git-worktrees-commit`, then `mise run test && mise run lint` from the root.

## Notes

- The `.worktrees/` hook marker and `.gitignore` entry stay for legacy trees (design D10); do not touch them.
- `git-worktrees-create` keeps forking off `origin/<tracked>`; only the path changes.
