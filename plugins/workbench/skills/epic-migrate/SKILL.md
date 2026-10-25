---
name: epic-migrate
description: "Migrate epics and tasks from the old scheme to the new one: points, usage, RETRO.md for done epics. Use once per workbench after upgrading the plugin."
---

Thin wrapper over `ticket.py` (`python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py`).

1. Dry run: `ticket.py migrate --all --dry-run`. Read the per-task changes and any `partial:`
   lines. If it refuses, show the problems it names and stop; do not work around it.
2. Migrate: `ticket.py migrate --all`. It prints one line per changed epic, writes the
   measured RETRO.md tables of done epics, and prints `retro-writer: <epic>` for each done
   epic whose Retro section is still the template's.
3. For each `retro-writer: <epic>` line: dispatch `workbench:retro-writer` (model sonnet)
   with the epic slug and its `record.md` (`ticket.py path <epic> record`) as the notes, since
   old epics have no orchestrator notes. Then run `ticket.py retro <epic>`, which commits the
   filled file as `chore(ticket): <epic> retro`.
4. Finally run `ticket.py deltas --all --buckets` and report which buckets left the seed.

Use `--transcripts DIR` or `--logs DIR` on migrate only to override the default locations.
