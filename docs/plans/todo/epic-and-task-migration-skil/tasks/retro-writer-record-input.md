---
title: Retro writer record input
status: todo
repo: workbench
value: retro-writer can write a real retro for epics that have a record but no orchestrator notes
files: [plugins/workbench/agents/retro-writer.md, plugins/workbench/skills/start-development/references/retro.md, plugins/workbench/skills/start-development/tests/test_templates.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 23
expected_tokens: 1500000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Retro writer record input

## Requirement

User request (verbatim, 2026-10-25): "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered."

User decision (verbatim): "Q8 RETRO.md for every old done epic: `ticket.py retro <epic>` for the measured tables, retro-writer (sonnet) fills Retro and Improvements from record.md and the deltas; the skill runs this per epic."

Design D8: RETRO.md for every done epic (Q8) (verbatim):

Migrate writes a done epic's RETRO.md generated block with retro's own functions (`retro._rows`,
`_generated`, `_splice`), creating the file from templates/retro.md when absent and keeping Retro and
Improvements byte for byte when present. It prints `retro-writer: <epic>` for each done epic whose Retro
section is still the template's. The skill then dispatches retro-writer (sonnet) per such epic and reruns
`ticket.py retro <epic>`, which commits the filled file as `chore(ticket): <epic> retro`. Old epics have no
orchestrator notes, so retro-writer gains record.md (and the task Notes) as an input.

Reuse brief fix-as-ac (verbatim): "retro-writer has no record.md input - agents/retro-writer.md:15-22 - add it"

## Acceptance conditions

- AC1: retro-writer's "Inputs you are given" names the epic's record.md as an input and says that for an epic with no orchestrator notes (one migrated by `ticket.py migrate`) record.md and the task files' Notes stand in for them [evidence: test:plugins/workbench/skills/start-development/tests/test_templates.py::test_retro_writer_agent]
- AC2: references/retro.md's Bootstrap section says epics closed before RETRO.md existed get one through the epic-migrate skill: `ticket.py migrate` writes the generated block, retro-writer fills it from record.md, `ticket.py retro <epic>` commits it [evidence: test:plugins/workbench/skills/start-development/tests/test_templates.py::test_retro_reference]
- AC3: both files stay ASCII with no em dash, en dash, smart quote or arrow [evidence: test:plugins/workbench/skills/start-development/tests/test_templates.py::test_plain_ascii_punctuation]
- AC4: the start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

## Files

- `plugins/workbench/agents/retro-writer.md`
- `plugins/workbench/skills/start-development/references/retro.md`
- `plugins/workbench/skills/start-development/tests/test_templates.py`

## Interfaces

- agents/retro-writer.md "## Inputs you are given": a record.md bullet; Limits unchanged (record.md is read with Read, not Bash).
- references/retro.md "## Bootstrap": the migrated-epic path.

## Expected outcome

retro-writer can fill a migrated epic's Retro and Improvements from its record.md when no orchestrator notes exist, and the reference says how old epics get a RETRO.md.

## Steps

1. Read agents/retro-writer.md, references/retro.md and test_templates.py in one pass. Add the needles to test_retro_writer_agent and test_retro_reference; run `cd plugins/workbench && pytest skills/start-development/tests/test_templates.py -q`: they fail.
2. Edit the two docs; run the verify once.
3. `git add`, commit, rerun the verify and quote its summary lines.

## Notes

- Estimate: 2 points: two prose edits pinned by needles in one test file.
- Fix-as-ac (reuse brief): "retro-writer has no record.md input - agents/retro-writer.md:15-22 - add it".
- Old epics have record.md (all five) but no orchestrator notes and no rulings beyond rulings.json; record.md is where their review rounds and rulings were written.
- Keep test_retro_writer_agent's existing needles; add, do not replace.
