---
name: worktree-create
description: >
  Creates one isolated git worktree for one subagent, at
  <workbench>/.claude/worktrees/<name>, branched from main with the newest
  origin/main and local main merged in. Refuses a name already in use so two
  agents can never share a tree. Use once per implementation or review subagent
  before dispatching it; pair with worktree-merge to land the work and clean up.
---

# worktree-create

One subagent, one worktree. This is the mechanism that stops two agents editing
and committing over each other, which has cost real work twice.

Distinct from `git-worktrees-create`, which makes one worktree per `code/`
submodule for a whole branch. This one makes a single tree for a single agent.

## Procedure

1. **Propose a name.** You (the orchestrator) choose it: short, lowercase. On the
   ticket flow the name is `<epic>-<task>` (epic slug, one hyphen, task slug, at most 57 characters),
   and `ticket.py worktrees` creates it for you. Otherwise name it for the task,
   so a stranded tree is traceable back to its work.

   Check what is taken first:

   ```sh
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/worktree-create/scripts/create.py" --list
   ```

2. **Create it.**

   ```sh
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/worktree-create/scripts/create.py" \
     --name <name> [--base main] [--repo <code/ submodule>]
   ```

   The script refuses a name whose worktree directory or branch already exists,
   and tells you what is in use. A rejection means propose another name, never
   reuse or force.

   It creates the worktree, then merges `origin/<base>` and local `<base>` into
   it so the agent starts from current code rather than from whenever the
   branch was cut. A conflict during that merge leaves the worktree in place and
   fails loudly.

   **Epic integration tree.** `--integration` makes the epic's own tree, the base
   every task tree forks from and lands on:

   ```sh
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/worktree-create/scripts/create.py" \
     --integration --name <epic> [--base main] [--repo <code/ submodule>]
   ```

   The tree and its branch are both named `<epic>`; it prints the path, branch,
   base and verb (`created` or `reused`). An existing tree on branch `<epic>` is
   reused unchanged; any other occupant of the path is refused, and an existing
   `<epic>` branch is checked out rather than recreated. With `--repo` it forks
   from `origin/<base>` when that ref exists. `ticket.py move <epic> in-progress`
   calls it for you; task trees are named `<epic>-<task>`.

3. **Dispatch the subagent against that path.** Give it the path and tell it to
   work only there, by absolute path: every Bash command starts with `cd` into
   the tree, and every Read, Edit and Write uses an absolute path inside it. Do
   NOT have it call the built-in `EnterWorktree`: that relocates the session's
   permission root and prompts for approval on every skill-created tree. The
   skill's tree is the isolation; the harness mechanism is not used.

4. **Land it with `worktree-merge`** when the agent returns.

## Rules

- One worktree per subagent. Never hand the same path to two agents.
- Sub-subagents do NOT get their own worktree. A helper spawned by an
  implementer works inside its parent's tree and inherits its isolation; the
  parent partitions work by file so helpers do not collide.
- Never create a worktree for a read-only agent. Auditors, reviewers that only
  read, and cartographers need no tree.
- The name is the handle for everything afterwards. If the agent dies, the name
  is how you find its work.
