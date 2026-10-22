---
title: Estimate and actuals
status: done
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
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/flow-speed-and-token-optimiz--estimate-and-actuals
branch: flow-speed-and-token-optimiz--estimate-and-actuals
verified_head: 65c5cb826ba0b06ee7a1101715827f8d252b4c4b
run: flow-speed-and-token-optimiz
provides: []
acs_for_audit: []
process_gaps: []
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

- Uses `estimator-params` (estimator-model): `estimator.task_minutes`, `estimator.epic_estimate`, imported by path from `plugins/workbench/scripts/lib/estimator.py`.
- Owns `epic-time-line`: the Time line format and the `estimate` subcommand output, defined in `ticket_cmds/estimate.py` (time_summary in ticket.py calls it).
- Task frontmatter keys `estimate_by` (`formula` or `override`) and `actual_roles` (quoted scalar).

## Expected outcome

`ticket.py estimate <epic>` gives every task realistic agent minutes and the README shows the epic's critical path and expected wall; after a run, `continue --run` fills `actual` and the role split, so the record compares estimate and actual per task.

## Steps

- Red: write `skills/start-development/tests/test_ticket_estimate.py` with AC1-AC6 (fixture epics via `ticket_repo_helpers.py`; a fake run dir with `journal.jsonl` and `agent-<id>.jsonl` rows carrying labels like `<epic>:verify:<task>#2`); run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_estimate.py -q`; expect failures.
- Green: estimate.py, time_summary, new-task, `_run_dir_durations`, `_actual_update`, roadmap.py; update the old-format assertions in test_ticket_run.py and test_ticket_roadmap.py.
- Run the task verify; expect all passed.

## Notes

- The Workflow runtime forbids the clock in scripts (`workflows/tests/harness.mjs` CLOCK_ERROR, pinned by `plan-execute-duration.test.mjs`), so actuals come from transcript timestamps after the run, never from plan-execute.
- `heartbeat.py --remaining-min` and the SKILL text read "Remaining estimate"; keep that field name.
- The command module pattern is `register(sub, t)` (see `ticket_cmds/contract.py`); `test_ticket_cmd_modules.py` checks module loading.
- ticket.py was reworked by epic integration worktrees (blocker); read the landed code before editing.
