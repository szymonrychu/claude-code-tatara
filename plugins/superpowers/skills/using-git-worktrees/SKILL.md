---
name: using-git-worktrees
description: "Use before running an agreed plan: the plan tree is created by ticket.py move <plan> in-progress, reused with ticket.py worktrees <plan> --refresh, and every agent on the plan works in it by absolute path."
---

# Using Git Worktrees

## Overview

Ensure the plan's work happens in an isolated workspace: one tree per plan, on branch `<plan>`, shared by every chunk and by the reviewer.

**Core principle:** Detect existing isolation first. Then let ticket.py make the tree. Never fight the harness.

`ticket.py` is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket.py`, run from the main checkout, never in the tree.

## Step 0: Detect Existing Isolation

**Before creating anything, check if you are already in an isolated workspace.**

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

**Submodule guard:** `GIT_DIR != GIT_COMMON` is also true inside git submodules. Before concluding "already in a worktree," verify you are not in a submodule:

```bash
# If this returns a path, you're in a submodule, not a worktree - treat as normal repo
git rev-parse --show-superproject-working-tree 2>/dev/null
```

**If `GIT_DIR != GIT_COMMON` (and not a submodule):** You are in a linked worktree. If it is this plan's tree (branch `<plan>`), skip to Step 2. Any other tree belongs to another plan or session: go back to the main checkout; never work or commit there.

**If `GIT_DIR == GIT_COMMON` (or in a submodule):** You are in the main checkout, where ticket.py runs. Continue with Step 1.

## Step 1: The Plan Tree

`ticket.py move <plan> in-progress` is the one way a plan tree is made. The gate in brainstorming is the consent; nothing else is asked. The move is refused unless plan.md `rung` is set and implementation-plan.md exists. It creates the tree at `<configdir>/worktrees/<plan>[/<repo>]` on branch `<plan>`, with the newest `origin/main` and local `main` merged in, moves the plan dir to `in-progress/` and sets the owner.

- A plan claimed before its tree existed gets it through `ticket.py worktrees <plan>`, which creates or reuses the tree.
- Reuse: `ticket.py worktrees <plan> --refresh` fast-forwards each clean tree with nothing ahead of the base, so it picks up what merged since. A repeat claim reuses the tree too.
- Never call a native worktree tool (`EnterWorktree` or similar) and never create a tree by hand: those relocate the permission root and leave phantom state ticket.py cannot see or clean up.

**Both layouts are supported.** A workbench tree holds the repo at `<tree>/<repo>`; on a plain repo the tree is the repo root. Agents cd into `<tree>/<repo>` when that directory exists, else into `<tree>`.

## Step 2: Rules for Every Agent in the Tree

- The orchestrator passes the absolute tree path; every agent works in it by absolute path and starts every command with `cd <tree>`.
- `git commit` runs only inside the tree. Before its first commit the implementer checks that `git rev-parse --show-toplevel` prints the tree it was given.
- Nobody resets, amends, rebases or stashes on `<plan>`: the commits are the hand-off between chunks.
- Chunks never run in parallel inside one tree: they share files and tests. Parallelism is across plans, each in its own tree.
- `ticket.py` never runs in the tree.

## Step 3: Verify Clean Baseline

Run the repo's own test and lint command in the tree (the Final verify of implementation-plan.md) before the first chunk is dispatched.

**If it fails:** that is pre-existing breakage. It is cleared first, as its own commit on `<plan>`, by the first implementer (boy scout rule), and named in the ledger. It is never a reason the plan's own work is incomplete.

**If it passes:** report ready in one line.

## Closing

Never merge a tree yourself; superpowers:finishing-a-development-branch hands it to one `workbench:worktree-merger`. `ticket.py move <plan> done` removes the tree and branch after the plan reached main, and `ticket.py reap --plan <plan>` sweeps any tree left over. If a tree cannot be removed, leave it and name it: named and stranded beats silently dropped.

## Quick Reference

| Situation | Action |
|-----------|--------|
| In this plan's tree | Skip creation (Step 0) |
| In another tree | Back to the main checkout |
| In a submodule | Treat as normal repo (Step 0 guard) |
| Plan agreed, no tree yet | `ticket.py move <plan> in-progress` |
| Claimed, tree missing | `ticket.py worktrees <plan>` |
| Tree exists, main moved on | `ticket.py worktrees <plan> --refresh` |
| Baseline fails | First commit on `<plan>` clears it |

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'm obviously not in a worktree - no need to check" | Run Step 0. Harness-created isolation and submodules both fool eyeballing; the detection commands settle it. |
| "`EnterWorktree` is quicker" | It relocates the permission root, and ticket.py cannot see or clean up its tree. The plan tree comes from ticket.py. |
| "I'll run ticket.py from the tree, it's where I am" | ticket.py runs from the main checkout; the tree is for the plan's commits. |
| "The workspace is fresh - baseline tests can wait" | A dirty baseline makes every later failure ambiguous. Run the tests now. |
