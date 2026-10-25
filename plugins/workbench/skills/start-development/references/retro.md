# Retro: RETRO.md at phase 7

Every closed epic gets a RETRO.md (`ticket.py path <epic> retro`) from `templates/retro.md`. Its
proposals feed the next plan.

## When it runs

At phase 7, after `ticket.py move <epic> done` and beside `record-writer`:

1. `ticket.py retro <epic>` writes the generated block (Tasks in delivery order, Deltas) and commits
   RETRO.md as `chore(ticket): <epic> retro`.
2. Dispatch `retro-writer` (sonnet) with the epic slug and your notes: per task the review rounds and
   the reviewer's verification tail, and every ruling (escalation judged, finding dropped, gap placed).
   It runs `ticket.py retro --history` itself when the prompt does not carry it. It edits only RETRO.md's
   Retro and Improvements sections and never the generated block.
3. Run `ticket.py retro <epic>` again: it regenerates the same block, keeps the filled sections and
   commits the file.

## What retro-writer fills

- `## Retro`: a table with the columns "Went well" and "Went bad / could be improved", one row per
  point, each cell with its evidence.
- `## Improvements`: potential improvements in the code, things delivered differently than expected,
  tech debt introduced anyway, and workflow improvement proposals.

## How the history feeds proposals

`ticket.py retro --history` returns the Retro and Improvements sections of the most recently done
epics. A point that recurs there becomes a workflow proposal marked `recurring`, naming the earlier
epics and the change to the flow. The `planner` reads the same history before planning and places the
proposals that bear on the new epic in design.md's Research inputs; it never edits ROADMAP.md, which is
human-owned.

## Bootstrap

Epics closed before RETRO.md existed have none, so the history starts empty and stays short for the
first epics. With no history, retro-writer proposes from this epic's evidence alone, marks nothing
`recurring`, and says "no history yet" under the workflow proposals.

Epics closed before RETRO.md existed get one through the epic-migrate skill: `ticket.py migrate` writes
the generated block, retro-writer fills it from record.md, and `ticket.py retro <epic>` commits it.
