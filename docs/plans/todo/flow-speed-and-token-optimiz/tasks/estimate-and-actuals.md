---
title: Estimate and actuals
status: todo
repo: workbench
value: "Every epic shows its critical path, expected wall and measured actuals per task and role"
files: [plugins/workbench/skills/start-development/scripts/ticket_cmds/estimate.py, plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/scripts/ticket_cmds/roadmap.py, plugins/workbench/skills/start-development/templates/task.md, plugins/workbench/skills/start-development/tests/test_ticket_estimate.py, plugins/workbench/skills/start-development/tests/test_ticket_run.py, plugins/workbench/skills/start-development/tests/test_ticket_roadmap.py]
verify: "cd plugins/workbench && pytest skills/start-development/tests/test_ticket_estimate.py skills/start-development/tests/test_ticket_run.py skills/start-development/tests/test_ticket_roadmap.py skills/start-development/tests/test_templates.py skills/start-development/tests/test_ticket_cmd_modules.py -q && ruff check scripts skills"
depends_on: [estimator-model]
owns: [epic-time-line]
uses: [estimator-params]
model: sonnet
estimate: 6
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Estimate and actuals

## Requirement

Add `ticket.py estimate <epic>` and stamp actuals from the run dir (design D4, D5). Template only.

- New module `plugins/workbench/skills/start-development/scripts/ticket_cmds/estimate.py` registering `estimate <epic> [--json]`:
  - For every task file of the epic whose `estimate_by` is not `override`: set `estimate` to `estimator.task_minutes(len(files), verify, suites)` and `estimate_by: formula`, where `suites` is the repo's workbench.json `suites` (`scripts/lib/workbench.py` `config_for_repo`).
  - Regenerate the README `## Time` section; commit the changed paths as `chore(ticket): <epic> estimate`.
  - Print the Time line, then one line `Longest path: <id> (<m> min), <id> (<m> min), <id> (<m> min)` from `epic_estimate(...)["longest"]`; `--json` prints the `epic_estimate` dict instead.
- `time_summary` in ticket.py returns `Estimate: <sum> agent-min | Critical path: <cp> min | Expected wall at P=<p>: <h> h (k=<k>) | Actual: <a> min | Remaining estimate: <r> min`, with `h` = epicWall / 60 to one decimal, from `estimator.epic_estimate`. `ticket.py tasks` and `apply-run` keep regenerating it.
- `ticket_cmds/roadmap.py` reads the sum from the new line (it parses `Estimate: (\d+) min` today).
- `new-task` without `--estimate` writes the formula minutes and `estimate_by: formula`; with `--estimate` it writes the given minutes and `estimate_by: override`. `templates/task.md` frontmatter gains `estimate_by: ""` and `actual_roles: ""`.
- `_run_dir_durations` returns, per task id, `{durationMs, roleMs}`: the task id is the last label component with a trailing `#<n>` or `+<n>` removed; the role is the second component; `durationMs` is the span from the first to the last transcript timestamp over the task's agents; `roleMs[role]` sums each agent's own first-to-last span.
- `apply-run` (and therefore `continue --run`) writes `actual` as the minutes of the summed `roleMs` (agent-minutes, the estimator's unit; `durationMs` from the return is the fallback when there is no run dir) and `actual_roles` as a quoted scalar `"impl <m>, verify <m>, review <m>, fix <m>"` (roles present only). Both keep today's rule: added across runs, replaced when the same run is applied again.
- Every existing test in `test_ticket_run.py` and `test_ticket_roadmap.py` that pinned the old Time line or the `+N`-only labels is updated to the new behaviour.

## Acceptance conditions

- AC1: estimate writes formula minutes and estimate_by formula to every task not marked override and keeps an override untouched [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_estimate.py::test_estimate_writes_formula_minutes_and_keeps_overrides]
- AC2: the README Time line shows sum, critical path, expected wall at P with k, actual and remaining [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_estimate.py::test_time_line_shows_critical_path_and_expected_wall]
- AC3: estimate prints the three longest-path tasks and --json prints the estimate dict [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_estimate.py::test_estimate_prints_three_longest_path_tasks]
- AC4: new-task records estimate_by formula without --estimate and override with it [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_estimate.py::test_new_task_estimate_by]
- AC5: run-dir labels ending in #n or +n map to their task [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_estimate.py::test_run_dir_matches_hash_n_labels]
- AC6: apply-run with a run dir writes actual as summed agent minutes and actual_roles per role [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_estimate.py::test_apply_run_writes_actual_and_roles]
- AC7: roadmap reads the sum from the new Time line [evidence: command:cd plugins/workbench && pytest skills/start-development/tests/test_ticket_roadmap.py -q]
- AC8: the updated run tests pass [evidence: command:cd plugins/workbench && pytest skills/start-development/tests/test_ticket_run.py skills/start-development/tests/test_templates.py -q]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/estimate.py`
- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/roadmap.py`
- `plugins/workbench/skills/start-development/templates/task.md`
- `plugins/workbench/skills/start-development/tests/test_ticket_estimate.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_run.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_roadmap.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
