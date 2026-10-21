---
name: epic-worktrees-remove
description: "Remove the git worktrees of one done epic. Use after an epic is delivered; never touches other epics or unmerged or dirty trees."
---

Thin wrapper over `ticket.py`. `<epic>` is the epic slug.

1. Dry run first and show the list:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py reap --epic <epic> --dry-run`
2. Remove:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py reap --epic <epic>`

`reap --epic` refuses an epic that is not done, never removes another epic's trees, and keeps
any unmerged or dirty tree. Report what was removed and what was kept.

One merged task mid-epic: `ticket.py reap --epic <epic> --task <id>` removes only that task's worktree.
