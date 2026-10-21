---
name: worktree-merge
description: >
  Rebases one subagent's worktree onto the base branch, fast-forwards it back
  into the main checkout, verifies every commit landed, and only then removes
  the worktree and its branch. Keeps the worktree intact on any conflict, dirty
  tree, or failed check. Use after a subagent returns work created with
  worktree-create.
---

# worktree-merge

Lands one agent's work and cleans up after it. Cleanup is conditional: the
worktree is removed only once the merge is verified. A stranded worktree is
recoverable; lost commits are not.

## Procedure

```sh
python3 "${CLAUDE_PLUGIN_ROOT}/skills/worktree-merge/scripts/merge.py" \
  --name <name> [--base main] [--repo <code/ submodule>] [--keep]
```

What it does, in order, stopping at the first failure:

1. **Refuses a dirty worktree.** Uncommitted changes mean the agent did not
   finish. Nothing is discarded - commit the work in the worktree, then re-run.
2. **Rebases onto `origin/<base>`** (or local `<base>` with no remote), so the
   history lands linear on top of whatever else merged meanwhile. A conflict
   in a doc file or a file matching `overlapIgnore` (workbench.json, plus the
   defaults) is union-merged: both sides are kept. Any other conflict aborts the
   rebase and keeps the worktree for resolution. A malformed workbench.json
   prints `[ERR] <message>` and exits 1 before any rebase.
3. **Fast-forwards `<base>`** in the main checkout. Fast-forward only by design:
   after a clean rebase, anything else means the base moved again, and a merge
   commit would paper over it. Re-run instead.
4. **Verifies the merge landed** - every commit on the branch is present in
   base. This is a real check against the repo, not an assumption.
5. **Removes the worktree and deletes the branch.** Only after step 4 passes.
   `--keep` merges without cleaning up. Directories left empty by the merge are
   pruned.
6. **Runs the `suites` from workbench.json after the fast-forward**, by default,
   in the main checkout. `--no-suites` skips them. A failing suite exits 4 (exit 4):
   the merge stays in place, it is not undone.

## Rules

- Do not run this until the agent's task is review-clean and verified. Merging
  unfinished work is how the remainder gets forgotten.
- Merge in plan order when several agents ran in parallel. A conflict between
  two agents' branches is information: they were probably one task.
- Never `git worktree remove --force` around a failure. The failure is the
  signal; forcing past it discards the work the check just protected.
- If a merge fails and you cannot resolve it, leave the worktree and surface the
  name. Named and stranded beats silently dropped.
