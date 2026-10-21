# Worktrees: one per subagent, created before dispatch

Read from Phase 4 of `start-development`. Isolation is enforced by this flow,
not left to the agents:

1. Name every task tree `<epic>--<task>`: the epic slug, two dashes, the task slug
   (`cost-and-ticketing--ticket-run`). Branch and directory carry the same name, so
   one tree maps to exactly one task. On the ticket flow, `ticket.py worktrees <epic>
   [--base main]` creates the trees: it calls `worktree-create` for every task without a
   live tree, writes `worktree` and `branch` into the task file, sets `status:
   in-progress` (a no-op after `move in-progress`, which already did it), and reuses a tree that already exists. Off the ticket flow, invoke
   `worktree-create` yourself with the same `<epic>--<task>` name. It refuses a name
   already in use and tells you what is taken; on a rejection fix the cause, never
   reuse or force. The tree lands at `<workbench>/.claude/worktrees/<name>` with the
   newest `origin/main` and local `main` merged in, so the agent starts from current code.
   `ticket.py worktrees <epic> --refresh` fast-forwards each live, clean tree with nothing ahead of the base,
   so a tree created earlier picks up what merged since. `ticket.py reap --epic <epic> --task <task>` removes
   one task's merged, clean tree without waiting for the epic to close.
2. Pass that path as the task's `worktree`. The agent works in it by absolute
   path and never calls the built-in `EnterWorktree`, which relocates the
   permission root and prompts on every skill-created tree.
3. When the task is review-clean and verified, **dispatch a `worktree-merger`
   subagent to land it. You never run the merge yourself.** A merge reads
   diffs, resolves conflicts, and reruns tests - all of it expensive, and none
   of it something you need to be holding at the merge phase.

   Size the agent from evidence, not from a guess:

   ```sh
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/worktree-merge/scripts/merge.py" \
     --name <name> --assess
   ```

   That reports commits, files, and whether git predicts a conflict, then names
   a model. Pass it through: `sonnet` for every case except a predicted
   conflict, which is the problematic one and gets `opus`. It returns a
   summary, never a diff - deciding who merges should not cost you the changes
   themselves.

   Merge in plan order, one agent per worktree. The merge script prunes empty directories left under
   paths the merge deleted, union-merges conflicts in doc files (the `overlapIgnore` globs) and reports them,
   and runs the repo's `suites` from `.claude/workbench.json` under the suite lock (`workbench-config.md`).

Never hand one path to two agents. Never merge a task that is not both clean and
verified - merging unfinished work is how the remainder gets forgotten. If a
merge fails and you cannot resolve it, leave the worktree and surface its name:
named and stranded beats silently dropped.

**Sub-subagents do not get worktrees.** A helper spawned by an implementer works
inside its parent's tree and inherits its isolation. The parent partitions the
helpers' work by file, because within one tree they can still overwrite each
other, and the parent stays accountable for verifying what they return. A
helper spawned by a review, verify or audit role is read-only like its parent:
it reads, greps and runs commands, never edits or commits. A merge helper works
in its task's tree and never in another.

Nesting is allowed and encouraged where it genuinely delivers faster at the same
quality. It is only the per-agent worktree that stops at the first level.

**Both worktree layouts are supported.** A workbench worktree holds the repo at
`<worktree>/<repo>`; with worktree-create on a plain (non-workbench) repo the
worktree IS the repo root. `repoDir(t)` in `workflows/plan-execute.js` is the only
place the two are joined: the emitted shell cds into `<worktree>/<repo>` when that
directory exists, else into `<worktree>`, and asserts `git rev-parse --show-toplevel`
equals it before any `git merge`. On mismatch the agent stops and reports. Dependency
merges, forward merges, implementers and fixers run `git merge`, `git commit` and
`git reset` only inside the task's own checkout, never in the main checkout.
