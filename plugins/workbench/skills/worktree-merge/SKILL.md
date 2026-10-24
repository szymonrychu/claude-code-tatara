---
name: worktree-merge
description: >
  Rebases one subagent's worktree onto the base branch, optionally verifies the
  rebased tree, fast-forwards it into the worktree that has the base checked out
  (an epic integration tree or the main checkout), verifies every commit landed,
  and only then removes the worktree and its branch. Keeps the worktree intact on any conflict, dirty
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
  --name <name> [--base main|<epic>] [--repo <code/ submodule>] [--keep] [--verify '<cmd>']
```

The **target tree** is the worktree whose checked-out branch is `<base>`, found with
`git worktree list --porcelain`: the integration tree for `--base <epic>`, the main
checkout for `--base main`. The script never runs `git checkout` and never switches the
human's checkout. When `<base>` is checked out in no worktree it raises
`<base> is not checked out in any worktree of <src>; run ticket.py move <epic> in-progress
for an integration branch, or check out <base> in the main checkout`, with nothing
rebased or merged.

Containment: `merged_into` (used by merge_back's post-merge check, the
`ticket.py` move done gate, and the Sweep) first tests ancestry, then falls back to patch equivalence
(`git cherry <target> <head>` printing only `-` lines). This is needed because the epic
close rebases `<epic>` onto a moved main, after which the branch is no longer an ancestor of it.
`git cherry` skips merge commits, so a merge of `<epic>` into a dependent never counts
against it. Otherwise it reports `<n> commit(s) of <head> have no equivalent in <target>`.

**Nothing to merge.** When the named tree's HEAD is already contained in `<base>` (ancestor
or patch-equivalent) nothing is merged, but `--verify <cmd>` still runs, in the target tree
under `suite-lock.sh`. The result carries `merged: 0`, `contained: true`,
`containedBy: ancestor|patch-equivalent`, `verification` and `baseBefore == baseAfter`. A
failing verify exits 4 with the 15-line tail, moves nothing and keeps the tree. Without
`--verify` the path behaves as before, plus `contained` and `containedBy`.

What it does, in order, stopping at the first failure:

1. **Refuses a dirty worktree.** Uncommitted changes mean the agent did not
   finish. Nothing is discarded - commit the work in the worktree, then re-run.
2. **Finds the target tree** (above) or refuses.
3. **Rebases onto local `<base>`** (never `origin/<base>`; `git fetch origin <base>` is
   best effort and fails harmlessly for an epic branch with no remote), so the
   history lands linear on top of whatever else merged meanwhile. A conflict
   in a doc file or a file matching `overlapIgnore` (workbench.json, plus the
   defaults) is union-merged: both sides are kept. Any other conflict aborts the
   rebase and keeps the worktree for resolution. A malformed workbench.json
   prints `[ERR] <message>` and exits 1 before any rebase.
4. **Runs `--verify <cmd>`** in the rebased named tree under `suite-lock.sh`, before
   anything moves. The rebased tree carries exactly the commit the target will have
   after the fast-forward, so this verifies the integration result. A failing verify
   exits 4 with the 15-line tail and never advances `<base>`: the target tree and
   `<base>` stay at their old commit and the named tree keeps its rebased commits.
5. **Fast-forwards `<base>` in the target tree**, only on a green verify. Fast-forward
   only by design. If `<base>` moved after the rebase, it rebases again onto the new
   `<base>` and re-runs `--verify`, up to 3 attempts in all, then raises `WorktreeError`
   naming the attempts. `<base>` never moves onto a tip the last verify did not pass.
6. **Verifies the merge landed** - every commit on the branch is present in
   base. This is a real check against the repo, not an assumption.
7. **Removes the worktree and deletes the branch** with `git branch -d` run from the
   target tree, so a branch merged into a non-checked-out base is deleted although the main
   checkout's HEAD lacks it. A refusal keeps the branch and is reported. Only after
   step 6 passes. `--keep` merges without cleaning up. Directories left empty by the
   merge are pruned in the target tree.
8. **Runs the `suites` from the source checkout's workbench.json** after the fast-forward,
   by default, in the target tree. `--no-suites` skips them. A failing suite exits 4 (exit 4):
   the merge stays in place, it is not undone.

The result carries `baseBefore` (the `<base>` SHA the final rebase was onto, before the
fast-forward), `baseAfter` and `verification: {command, passed, tail}`. `--assess` works
with `--base <epic>`.

## Epic close

The epic close has one entry point, run by the orchestrator: `ticket.py close <epic>
--verify '<full suite and lint>'` (the start-development skill's ticket script). It enforces
the done-task gate and the review gate, rebases `<epic>` onto main inside the
integration tree, runs the full suite and lint there, fast-forwards main, and writes
`close.json`. This skill never fast-forwards main for an epic. The merger is dispatched
only to resolve a rebase conflict of `<epic>` onto main in the integration tree; once
resolved, the orchestrator reruns `ticket.py close`.

## Rules

- Do not run this until the agent's task is review-clean and verified. Merging
  unfinished work is how the remainder gets forgotten.
- Merge in plan order when several agents ran in parallel. A conflict between
  two agents' branches is information: they were probably one task.
- Never `git worktree remove --force` around a failure. The failure is the
  signal; forcing past it discards the work the check just protected.
- If a merge fails and you cannot resolve it, leave the worktree and surface the
  name. Named and stranded beats silently dropped.
