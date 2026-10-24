# Worktrees: one integration tree per epic

Read from phase 4 of `start-development`. One integration tree per epic; every task of the epic runs in
it, sequential, in `ticket.py tasks <epic>` order.

## The integration tree

`ticket.py move <epic> in-progress` creates the epic's tree at `<configdir>/worktrees/<epic>[/<repo>]` on
branch `<epic>`, with the newest `origin/main` and local `main` merged in, through `worktree-create`. An
epic claimed before its tree existed gets it through `ticket.py worktrees <epic>`, which creates or reuses
the tree. `ticket.py worktrees <epic> --refresh` fast-forwards a clean tree with nothing ahead of the
base, so it picks up what merged since.

Every role on a task (implementer, reviewer) works in that one tree; the scope auditor reads it at phase
5. Each task commits on `<epic>`, so a dependent task starts on top of its dependencies' commits and the
epic is one tested unit. Tasks never run in parallel inside one tree: they share files and tests, and two
agents in one tree overwrite each other. Parallelism is across epics, each in its own tree.

## Rules for every agent in the tree

- The orchestrator passes the absolute tree path, and the agent works in it by absolute path.
  It never calls the built-in `EnterWorktree`, which relocates the permission root and prompts on
  every skill-created tree. Every tree is plain `git worktree` made by `worktree-create`.
- `git commit` runs only inside the tree; never in the main checkout or another tree. Before its first
  commit the implementer checks that `git rev-parse --show-toplevel` prints the tree it was given.
- Nobody resets, amends, rebases or stashes on `<epic>`: the commits are the hand-off between tasks.
- `ticket.py` never runs in the tree; the orchestrator records task outcomes from the main checkout.

**Helpers.** A helper spawned by an implementer works inside its parent's tree; the parent partitions the
helpers' work by file and stays accountable for what they return. A helper spawned by a review or audit
role is read-only like its parent: it reads, greps and runs commands, never edits or commits. A merge
helper works in its epic's tree and never in another.

**Both layouts are supported.** A workbench worktree holds the repo at `<worktree>/<repo>`; on a plain
(non-workbench) repo the worktree is the repo root. Agents cd into `<worktree>/<repo>` when that directory
exists, else into `<worktree>`.

## Closing

Never merge a worktree yourself. Meta mode: `ticket.py close <epic> --verify <cmd>` rebases `<epic>` onto
main in the tree and fast-forwards main only when the verify passed. A rebase conflict goes to a
`worktree-merger` agent in that tree, sized by `python3
"${CLAUDE_PLUGIN_ROOT}/skills/worktree-merge/scripts/merge.py" --name <epic> --assess` (sonnet, opus for a
predicted conflict); then run close again. Component mode: the MR from `<epic>`.

`ticket.py move <epic> done` removes the integration tree and branch after the epic reached main, and
`ticket.py reap --epic <epic>` sweeps any tree left over. If a tree cannot be removed, leave it and name
it: named and stranded beats silently dropped.
