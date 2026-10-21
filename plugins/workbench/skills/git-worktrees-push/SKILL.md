---
name: git-worktrees-push
description: "Push committed worktree branches to origin across code/ repos. Use to push a worktree branch or publish worktree commits for a PR or MR."
---

# git-worktrees-push

Pushes the branch checked out in `.worktrees/<branch>/<repo>` to `origin` for
each requested repo. Runs after `git-worktrees-commit` has produced local
commits and before opening or updating a pull request.

## Procedure

1. Determine the branch name and target repos from the user's request. If no
   repos are given, the script defaults to every submodule under `code/`.
2. Run the script:
   ```
   mise exec -- bash ${CLAUDE_PLUGIN_ROOT}/skills/git-worktrees-push/scripts/push.sh --branch <branch> --repos <repo-a>,<repo-b>
   ```
   Omit `--repos` to push all repos.
3. The script pushes each repo independently and never aborts early: a
   missing worktree or a rejected push in one repo does not stop the others.
4. Read the printed report table (repo, status, detail) and relay it to the
   user. `ok` means pushed; `failed` means either no worktree exists at the
   expected path, or `git push` was rejected (non-fast-forward, missing
   remote permissions, etc) - the detail column carries the git error text.
5. The script exits non-zero if any repo failed. Surface that as a failure to
   the user; do not silently retry or force-push on their behalf.
