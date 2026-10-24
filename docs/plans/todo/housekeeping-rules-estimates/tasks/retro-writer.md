---
title: Retro writer
status: todo
repo: workbench
value: Every closed epic gets a written retro whose proposals feed the next plan
files: [plugins/workbench/agents/retro-writer.md, plugins/workbench/skills/start-development/SKILL.md, plugins/workbench/skills/start-development/references/retro.md, plugins/workbench/skills/start-development/tests/test_skill_size.py, plugins/workbench/skills/start-development/tests/test_templates.py, plugins/workbench/agents/planner.md, plugins/workbench/skills/start-development/tests/test_planner_agent.py, plugins/workbench/README.md]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-research && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint"
depends_on: [retro-command, planner-points-gate]
model: opus
review: ""
verified_head: ""
---

# Retro writer

## Requirement

User requirement (U3, verbatim): "during epic close, add RETRO.md including: tasks table with task title (in delivery order), post-delivery complexity measure in storypoints, delivery time (start to finish in minutes), tokens used for each task (including implementation + review); retro table with what went well, what went bad / could be improved; list of potential improvements in the code or things that were delivered in a different way than expected (include tech-debt if introduced anyway)"

User requirement (U4, verbatim, part): "retro table will be used to propose improvements for future work (also including workflow improvements). It must be seamless for the agent (taking over most of the estimation from agent's reasoning)."

Design D12: a new `plugins/workbench/agents/retro-writer.md` (model sonnet) runs at start-development phase 7 after `ticket.py retro <epic>`, beside record-writer. Inputs: the epic slug, the orchestrator's notes (per task the review rounds and the reviewer's verification tail, every ruling), and `ticket.py retro --history`. It writes only RETRO.md (`ticket.py path <epic> retro`), keeps the generated block untouched, and fills Retro as a table with the columns "Went well" and "Went bad / could be improved", and Improvements as a list of potential code improvements, things delivered differently than expected, tech debt introduced anyway, and workflow improvement proposals for items that recur in the history. ASCII only, plain hyphens. Phase 7 of start-development/SKILL.md names `ticket.py retro` and retro-writer, with the detail in a new `references/retro.md` (linked from SKILL.md and listed in test_skill_size KEPT), so SKILL.md stays within 150 lines. planner.md reads `ticket.py retro --history` before planning and places the relevant proposals in design.md's Research inputs. The plugin README's phase dispatch table gains the phase 7 retro-writer row.

## Acceptance conditions

- AC1: retro-writer.md has `model: sonnet`, names its inputs, writes only RETRO.md, keeps the generated block, and names "Went well", "Went bad / could be improved", "delivered differently", "tech debt" and "workflow" improvements from the history; it is ASCII [evidence: test:plugins/workbench/skills/start-development/tests/test_templates.py::test_retro_writer_agent]
- AC2: SKILL.md phase 7 names `ticket.py retro` and retro-writer and links references/retro.md, which is listed in KEPT [evidence: test:plugins/workbench/skills/start-development/tests/test_skill_size.py::test_every_kept_reference_is_linked_from_skill]
- AC3: SKILL.md stays within 150 lines [evidence: test:plugins/workbench/skills/start-development/tests/test_skill_size.py::test_skill_md_within_line_cap]
- AC4: planner.md tells the planner to read `ticket.py retro --history` and place relevant proposals in design.md [evidence: test:plugins/workbench/skills/start-development/tests/test_planner_agent.py::test_planner_reads_retro_history]
- AC5: the plugin README dispatch table has a phase 7 retro-writer row matching SKILL.md [evidence: test:plugins/workbench/skills/start-development/tests/test_release.py::test_readme_dispatch_phases_match_skill]
- AC6: start-development, start-review, start-research and scripts suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-research && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

## Files

- `plugins/workbench/agents/retro-writer.md`
- `plugins/workbench/skills/start-development/SKILL.md`
- `plugins/workbench/skills/start-development/references/retro.md`
- `plugins/workbench/skills/start-development/tests/test_skill_size.py`
- `plugins/workbench/skills/start-development/tests/test_templates.py`
- `plugins/workbench/agents/planner.md`
- `plugins/workbench/skills/start-development/tests/test_planner_agent.py`
- `plugins/workbench/README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
