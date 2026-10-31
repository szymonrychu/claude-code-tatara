# Worktrees: one tree per plan

Read from `superpowers:subagent-driven-development` and `superpowers:using-git-worktrees`.
One tree per plan; every chunk of the plan runs in it, sequential, in the order implementation-plan.md lists them.

## The plan tree

`ticket.py move <plan> in-progress` creates the plan's tree at `<configdir>/worktrees/<plan>[/<repo>]` on
branch `<plan>`, with the newest `origin/main` and local `main` merged in, through `worktree-create`. A
plan claimed before its tree existed gets it through `ticket.py worktrees <plan>`, which creates or reuses
the tree. `ticket.py worktrees <plan> --refresh` fast-forwards a clean tree with nothing ahead of the
base, so it picks up what merged since.

Every role on the plan (implementer, reviewer) works in that one tree. Each step commits on `<plan>`, so a
later chunk starts on top of the earlier commits and the plan is one tested unit. Chunks never run in
parallel inside one tree: they share files and tests, and two agents in one tree overwrite each other.
Parallelism is across plans, each in its own tree.

## Rules for every agent in the tree

- The orchestrator passes the absolute tree path, and the agent works in it by absolute path.
  It never calls the built-in `EnterWorktree`, which relocates the permission root and prompts on
  every skill-created tree. Every tree is plain `git worktree` made by `worktree-create`.
- `git commit` runs only inside the tree; never in the main checkout or another tree. Before its first
  commit the implementer checks that `git rev-parse --show-toplevel` prints the tree it was given.
- Nobody resets, amends, rebases or stashes on `<plan>`: the commits are the hand-off between chunks.
- `ticket.py` never runs in the tree; the orchestrator and the worktree-merger run it from the main
  checkout.

**Helpers.** A helper spawned by an implementer works inside its parent's tree; the parent partitions the
helpers' work by file and stays accountable for what they return. A helper spawned by the reviewer is
read-only like its parent: it reads, greps and runs commands, never edits or commits. A merge helper
works in its plan's tree and never in another.

**Both layouts are supported.** A workbench worktree holds the repo at `<worktree>/<repo>`; on a plain
(non-workbench) repo the worktree is the repo root. Agents cd into `<worktree>/<repo>` when that directory
exists, else into `<worktree>`.

## Closing

Never merge a worktree yourself. The `worktree-merger` does: meta mode runs `ticket.py close <plan>
--verify <cmd>`, which rebases `<plan>` onto main in the tree and fast-forwards main only when the verify
passed; a rebase conflict is resolved by the merger in that tree (sonnet, opus for a conflict predicted by
`python3 "${CLAUDE_PLUGIN_ROOT}/skills/worktree-merge/scripts/merge.py" --name <plan> --assess`), then close
runs again. Component mode: the MR from `<plan>`.

`ticket.py move <plan> done` removes the tree and branch after the plan reached main, and
`ticket.py reap --plan <plan>` sweeps any tree left over. If a tree cannot be removed, leave it and name
it: named and stranded beats silently dropped.
