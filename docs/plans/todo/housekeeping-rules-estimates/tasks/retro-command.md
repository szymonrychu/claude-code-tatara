---
title: Retro command
status: todo
repo: workbench
value: "Epic close writes RETRO.md's measured tasks table and deltas in delivery order with one command"
files: [plugins/workbench/skills/start-development/scripts/ticket_cmds/retro.py, plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/templates/retro.md, plugins/workbench/skills/start-development/tests/test_ticket_retro.py, plugins/workbench/skills/start-development/tests/test_templates.py, plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py, plugins/workbench/skills/start-development/references/tickets.md]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [stamp-actuals, calibration-lib]
model: opus
review: ""
verified_head: ""
---

# Retro command

## Requirement

User requirement (U3, verbatim): "during epic close, add RETRO.md including: tasks table with task title (in delivery order), post-delivery complexity measure in storypoints, delivery time (start to finish in minutes), tokens used for each task (including implementation + review); retro table with what went well, what went bad / could be improved; list of potential improvements in the code or things that were delivered in a different way than expected (include tech-debt if introduced anyway)"

User requirement (U4, verbatim, part): "Task table will be used for future estimates, retro table will be used to propose improvements for future work (also including workflow improvements)."

Design D12: `templates/retro.md` with exactly the H2s Tasks, Deltas, Retro, Improvements (ASCII only). `ticket.py retro <epic>` (main checkout only; epic in in-progress or done) writes the epic's RETRO.md: the Tasks table in delivery order (the git log of `chore(ticket): <epic> task <slug> done` commits, oldest first; tasks with no such commit follow in dependency order) with columns task title, points (estimate), points (post-delivery), minutes (expected), minutes (actual), tokens (expected), tokens (actual), and a totals line; the Deltas section per task (points difference, minutes and tokens actual over expected) and the MdAPE per metric. Missing values read `not recorded`. The generated parts sit between `<!-- retro:generated:begin -->` and `<!-- retro:generated:end -->` markers; a rerun regenerates them and keeps everything else (the Retro and Improvements sections the retro-writer fills). It commits `chore(ticket): <epic> retro`. `ticket.py path <epic> retro` resolves RETRO.md. `ticket.py retro --history [--limit N]` prints, as JSON, the Retro and Improvements sections of the most recent N (default 5) done epics that have a RETRO.md. KEPT and KEPT_MODULES in the retirement pin gain `retro` and `retro.py`.

## Acceptance conditions

- AC1: RETRO.md lists the tasks in delivery order from the `task <slug> done` commits, not dependency order, with the seven columns and a totals line [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_tasks_in_delivery_order]
- AC2: the Deltas section shows per-task points difference and minutes and tokens ratios and the MdAPE per metric; a task without actuals reads `not recorded` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_deltas_section]
- AC3: a rerun regenerates the generated block and keeps the hand-written Retro and Improvements sections byte for byte [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_rerun_keeps_written_sections]
- AC4: retro commits exactly RETRO.md as `chore(ticket): <epic> retro` and refuses a linked worktree and a todo epic [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_commit_and_refusals]
- AC5: `ticket.py path <epic> retro` prints the RETRO.md path [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_path_retro]
- AC6: `retro --history --limit 2` prints the Retro and Improvements of the two latest done epics with a RETRO.md as JSON [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_history]
- AC7: templates/retro.md has exactly the H2s Tasks, Deltas, Retro, Improvements and is ASCII [evidence: test:plugins/workbench/skills/start-development/tests/test_templates.py::test_retro_template]
- AC8: the retirement pin lists `retro` in KEPT and `retro.py` in KEPT_MODULES and still holds [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py::test_run_loop_commands_retired]
- AC9: start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/retro.py`
- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/templates/retro.md`
- `plugins/workbench/skills/start-development/tests/test_ticket_retro.py`
- `plugins/workbench/skills/start-development/tests/test_templates.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py`
- `plugins/workbench/skills/start-development/references/tickets.md`

## Interfaces

- `ticket_cmds/retro.py`: `register(sub, t)`, `run(a, t) -> int`; `ticket.py retro <epic>` and `ticket.py retro --history [--limit N]`.
- `ticket.py:PATH_KINDS["retro"] = "RETRO.md"`.
- `templates/retro.md` H2s: Tasks, Deltas, Retro, Improvements; markers `<!-- retro:generated:begin -->` / `<!-- retro:generated:end -->`.
- Uses `calibration.mdape`.

## Expected outcome

At close one command writes the measured half of RETRO.md from the task files and the git log, and the history of earlier retros is one command away.

## Steps

1. List the files under Files plus ticket_cmds/close_cmd.py and task_cmd.py, read them in one pass; write test_ticket_retro.py (temp git repo with done commits in non-dependency order) and the template test; run them: they fail.
2. Implement the module, template and path kind; update the retirement pin and tickets.md; run the verify once.
3. Commit; leave the tree clean.

## Notes

- Estimate: 8 points.
- Reuse (brief): ticket_cmds/__init__.py contract and _load_cmd_modules (1546), modelled on task_cmd.py and close_cmd.py; resolve_epic (253), _phase_of (267), scan (444), _sections (692), _section_replace (906), _template (332), _render (326), PATH_KINDS (45) plus cmd_path (1512), commit_ticket_change (295), require_main_checkout (285).
- Adopted (brief): delivery order from the git log of `chore(ticket): <epic> task <slug> done` commits that task_cmd.py:36 writes (verified with `git log --grep`).
- Fix-as-ac (brief): KEPT_MODULES is an exact set; REMOVED contains `estimate` (do not name anything that way); RECORD_H2 stays unchanged, retro.md gets its own exact-H2 test; templates are ASCII (test_templates.py:97-103).
- Fix-as-ac (brief): only RETRO.md (like record.md) is written after `move done`; task files are never touched by retro.
- Bootstrap: this epic's own tasks have no estimate fields (planned before they existed); their rows read `not recorded`, and the points come from each task's Notes line `Estimate: <n> points` (the retro-writer copies them in prose).
