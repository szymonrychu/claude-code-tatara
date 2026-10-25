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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
