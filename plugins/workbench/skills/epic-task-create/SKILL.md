---
name: epic-task-create
description: "Create a task file inside an existing epic and lint the epic. Use to add a task to an epic."
---

Thin wrapper over `ticket.py`. `<epic>` is the epic slug.

1. Create the task, every required field given:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py new-task --epic <epic> --title "<title>" --repo <repo> --value "<value>" --files "<files>" --verify "<command>"`
   Optional: `--depends-on`, `--owns`, `--uses`, `--model`, `--review`, `--estimate`,
   `--requirement-file`, `--ac-file`.
2. Lint the epic and report its output verbatim:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py lint <epic>`
