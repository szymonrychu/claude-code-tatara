---
name: epic-worktrees-remove
description: "Remove the git worktrees of one done epic. Use after an epic is delivered; never touches other epics or unmerged or dirty trees."
---

Thin wrapper over `ticket.py`. `<epic>` is the epic slug.

1. Dry run first and show the list:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py reap --epic <epic> --dry-run`
2. Remove:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py reap --epic <epic>`

`reap --epic` refuses an epic that is not done and never removes another epic's trees. It removes
the integration tree at `<configdir>/worktrees/<epic>[/<repo>]` (and a legacy
`.worktrees/<epic>/<repo>`) with the `<epic>` branch. The integration branch must be contained in
the trunk: local `--base` (default `main`) in meta mode, `origin/<tracked branch>` after a fetch in
component mode. "Contained" is ancestry, else patch equivalence (`git cherry` all `-`), so it
survives the close rebasing `<epic>` onto a moved main. A branch is deleted with `git branch -D`
only after that check passed; no worktree is ever force-removed. A dirty or not-contained tree
stays with its branch and is listed under `left` with the reason. The JSON summary lists every
removed tree (`removed`), every deleted branch (`branches`) and every `left` item. Report all three.
