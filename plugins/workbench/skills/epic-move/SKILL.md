---
name: epic-move
description: "Move an epic, with its tasks, to in-progress or to done. Use to claim an epic or close a delivered one."
---

Thin wrapper over `ticket.py`. `<epic>` is the epic slug.

- Claim: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py move <epic> in-progress`
  Needs: epic in todo, blockers done, `check` clean. The move carries `tasks/` and sets every
  todo task to in-progress. Before moving, the claim creates the epic's integration worktree
  (one per repo for component epics, forked from the submodule's tracked branch), or reuses
  it on a repeat claim; if creation fails the epic stays in todo. An epic mixing meta and
  component tasks is refused.
- Close: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py move <epic> done`
  Needs: stage review, last verdict pass, every task done and verified, branches merged.

If the move refuses, show the precondition it names and stop; do not work around it.

After the move report task statuses:
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py tasks <epic>`
