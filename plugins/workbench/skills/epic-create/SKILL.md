---
name: epic-create
description: "Create a new epic with its README after a duplicate check. Use to start an epic; stops on a near duplicate unless the user explicitly says to create it anyway."
---

Thin wrapper over `ticket.py`. `<title>` is the epic title.

1. Dedup check, show any near duplicate by slug:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py check --title "<title>"`
2. Create:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py new-epic --title "<title>" --blockers <slugs> --repos <a,b> --what ... --how ... --why ...`
   (omit fields the user did not give; `--description-file`, `--goals-file`, `--non-goals-file` also work).
3. If `new-epic` returns exit 3 (near duplicate): name the duplicate from stderr and STOP.
   Rerun with `--force` only when the user explicitly asks to create it anyway.
4. Report the created epic slug and path.
