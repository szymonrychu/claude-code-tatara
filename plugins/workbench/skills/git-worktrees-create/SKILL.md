---
name: git-worktrees-create
description: "Create git worktrees for a branch across code/ submodules. Use to start a new branch, check an existing branch into a worktree, or spin up an isolated workspace."
---

Creates `.worktrees/<branch>/<repo>` for each requested submodule under
`code/`. If `<branch>` already exists (locally or on the remote) it is
checked out into the worktree; otherwise it is created fresh off the repo's
tracked default branch (from `.gitmodules`, default `main`).

## Procedure

1. Map the user's request to a branch name and a repo list. If the user says
   "all repos", pass every name from `all_repos()`.
2. Run:
   ```
   mise exec -- python3 ${CLAUDE_PLUGIN_ROOT}/skills/git-worktrees-create/scripts/create.py --branch <branch> --repos a,b,c
   ```
3. The script, per repo:
   - fetches `origin`
   - checks out `<branch>` into `.worktrees/<branch>/<repo>` if it exists
     locally or on the remote; otherwise creates it off
     `origin/<tracked-branch>`
   - skips (status `skipped`) if a worktree already exists at that path
   - continues on error; a single repo failure never aborts the others
4. Relay the printed report table (repo / status / detail) to the user
   verbatim or summarized. Exit code is non-zero iff any repo failed.
