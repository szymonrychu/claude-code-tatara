---
title: Epic and task migration skill
blockers: ["Housekeeping rules, estimates and retrospectives"]
stage: build
owner: ""
repos: [workbench]
created: 2026-10-25
---

# Epic and task migration skill

## Project brief

What: `ticket.py migrate` and a thin `epic-migrate` skill that rewrite every epic's task files from the old ticket scheme (minutes estimate, run-loop keys) to the points scheme, fill actuals from legacy numbers and the transcripts still on disk, and give every done epic a RETRO.md; then this repository's six done epics are migrated for real.
How: A new ticket_cmds module reusing ticket.py's frontmatter I/O and commit helper, retro's generated block, calibration's seed table (plus a minutes-to-points inverse) and agent_usage's backfill (plus a legacy transcript matcher and one transcript pass per epic); one `chore(ticket): <epic> migrate` commit per epic, idempotent, with a dry run.
Why: Calibration reads only done tasks with points and both actuals, and no done task has points today, so every estimate bucket is still on the seed table and only one epic has a retro.

## Description

Requested 2026-10-25: "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered." The new scheme is the one epic housekeeping-rules-estimates defined (design D7-D16). The mapping is in design.md: points from the legacy minutes estimate (nearest seed bucket) or the Notes line "Estimate: N points", expected values from the legacy estimate or the seed, actuals from legacy numbers or matched transcripts and never invented, legacy keys dropped. The retro delivery order falls back to verified_head commit dates, the deltas legacy rows retire, and retro-writer reads record.md for epics with no orchestrator notes.

## Goals

- G1: `ticket.py migrate [<epic> | --all] [--dry-run]` rewrites every old-scheme task file in todo, in-progress and done epics to the 18 template keys in template order, with points, expected values and actuals per the design, never inventing a value.
- G2: Each done epic gets a RETRO.md: migrate writes its generated block in the epic's one `chore(ticket): <epic> migrate` commit, and retro-writer fills Retro and Improvements from record.md.
- G3: A second run changes nothing (idempotent), and a dry run changes no tracked file and commits nothing.
- G4: A thin `epic-migrate` skill (at most 45 lines) wraps the commands, and the plugin README, the flow docs and references/tickets.md name it and `migrate`.
- G5: This repository's six done epics are migrated: `ticket.py lint` prints `lint: ok`, `ticket.py deltas --all --buckets` shows at least one bucket with source history or refit, and every done epic has a tracked RETRO.md with a filled Retro section.

## Non-goals

- Rewriting approvals.json, rulings.json, record.md, close.json, README.md or design.md of any epic.
- Re-estimating old tasks by judgement, or changing the calibration formula or seed table.
- A backward compatible reader for the old keys: the deltas legacy rows are removed.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
