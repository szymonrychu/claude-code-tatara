---
name: git-worktrees-commit
description: "Commit changes across repo worktrees under <configdir>/worktrees/<branch>/<repo>, with per-repo semantic commit titles you compose. Use to commit or wrap up work in a workbench worktree."
---

# git-worktrees-commit

Commits changes inside `<configdir>/worktrees/<branch>/<repo>` for one or more repos.
This is a **two-phase** flow: the script never writes the commit message
itself, it only shows diffs and performs git plumbing. You (the agent) read
the diff and write the title.

## Phase 1: collect

Run for the branch and repos in scope (optionally restrict to a file subset):

```
mise exec -- python3 ${CLAUDE_PLUGIN_ROOT}/skills/git-worktrees-commit/scripts/commit.py collect --branch <branch> --repos repo-a,repo-b [--files file1,file2]
```

This prints, per repo, `git status --short` and `git diff` (staged +
unstaged, restricted to `--files` if given). A repo with no changes is
reported as `skipped` and printed with no diff section.

## Phase 2: compose titles

Read each repo's diff and write **one Conventional Commits title per repo**:

- `type: short imperative description`
- Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`.
- **Title only. No body, no bullet list, no extra paragraph.** If the diff
  needs more explanation than a title can carry, that's a signal to consider
  splitting the change, not to add a body here.
- Do not commit a repo you did not actually read the diff for.

## Phase 3: commit

Run once with a `--message repo=title` for every repo that has changes
(matching the repos/files scope used in collect):

```
mise exec -- python3 ${CLAUDE_PLUGIN_ROOT}/skills/git-worktrees-commit/scripts/commit.py commit --branch <branch> --repos repo-a,repo-b [--files file1,file2] \
  --message repo-a="fix: handle nil pointer in reconciler" \
  --message repo-b="docs: document worktree commit flow"
```

Behavior:

- Stages all changes in the repo, or only the `--files` subset if given
  (`git add -- <files>`), then commits with the supplied title.
- Empty diff (nothing to stage) is `skipped`, no message required.
- A repo with changes but no `--message` entry is `failed` with reason
  `no commit message provided` - it is never committed with a placeholder.
- An unknown repo name (not a submodule under `code/`) is `failed`, other
  repos still process.
- Report line per repo: `committed <short-sha> <title>`, `skipped`, or
  `failed <reason>`. Exit code is non-zero iff any repo failed.

## Notes

- Repos are resolved as `<configdir>/worktrees/<branch>/<repo>`; the worktree must
  already exist (see `git-worktrees-create`). A missing worktree dir is a
  per-repo `failed`, not an abort.
- `--repos` accepts comma-separated or repeated flags.
