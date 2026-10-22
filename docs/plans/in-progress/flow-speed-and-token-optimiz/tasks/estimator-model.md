---
title: Estimator model
status: done
repo: workbench
value: "Realistic agent-minute estimates from one fitted, refittable parameter file"
files: [plugins/workbench/scripts/lib/estimator.json, plugins/workbench/scripts/lib/estimator.py, plugins/workbench/scripts/tests/test_estimator.py, plugins/workbench/scripts/tests/fixtures/estimator_tasks.json]
verify: "cd plugins/workbench && pytest scripts/tests/test_estimator.py -q && ruff check scripts"
depends_on: []
owns: [estimator-params]
uses: []
model: sonnet
estimate: 6
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/flow-speed-and-token-optimiz--estimator-model
branch: worktree-flow-speed-and-token-optimiz--estimator-model
verified_head: 3a1ea040255888a4a4e5e17169fbb748951481d4
run: flow-speed-and-token-optimiz
provides: [estimator-params]
acs_for_audit: []
process_gaps: []
---

# Estimator model

## Requirement

Build the estimator's one parameter file and its library (design D4, D13). Every number the estimator uses comes from the JSON; nothing is hard-coded twice.

- `plugins/workbench/scripts/lib/estimator.json`: `{"task": {"intercept": 4.0, "exponent": 0.22, "fullSuiteFactor": 6.9}, "epic": {"parallelism": {"low": {"tasks": 15, "p": 1.5}, "high": {"tasks": 30, "p": 3.0}}, "k": 2.0}, "fullSuitePatterns": [<regexes>]}`.
- `plugins/workbench/scripts/lib/estimator.py`, stdlib only:
  - `load(path=None) -> dict` reads estimator.json (default: beside the module).
  - `full_suite(cmd, suites=()) -> bool`: true when any `&&`- or `;`-separated part of `cmd` (a leading `cd <dir>` part ignored) matches a `fullSuitePatterns` regex, or equals an entry of `suites` after whitespace normalisation. True for: `mise run test`, `mise run test && mise run lint`, `make test`, `npm test`, `pnpm test`, `yarn test`, `go test ./...`, `cargo test`, `pytest`, `pytest -q`, `uv run pytest`, `bash scripts/run-tests.sh`, `cd plugins/workbench && bash scripts/run-tests.sh`. False for: `pytest tests/test_x.py -q`, `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`, `node --test workflows/tests/a.test.mjs`, `cargo test parser::`, `go test ./pkg/x -run TestY`, `ruff check scripts`.
  - `task_minutes(files, verify, suites=(), params=None) -> int`: `round(intercept * (files + 1) ** exponent * (fullSuiteFactor if full_suite(verify, suites) else 1))`, at least 1.
  - `parallelism(open_tasks, params=None) -> float`: `low.p` at or below `low.tasks`, `high.p` at or above `high.tasks`, linear between, rounded to one decimal.
  - `epic_estimate(tasks, params=None) -> dict` over `[{id, minutes, depends_on, status}]`: `sum` (all tasks), `remaining` (tasks not done), `cp` (longest `depends_on` path by minutes) and `path` (its ids in order), `p` = parallelism(number of tasks not done), `runWall = max(cp, sum / p)`, `epicWall = k * runWall`, `longest` (the three tasks on the critical path with the most minutes, as `[{id, minutes}]`).
  - `refit(rows) -> dict` over `[{files, full, minutes}]`: ordinary least squares of `ln(max(minutes, 1))` on `[1, ln(files + 1), full]` solved with the 3x3 normal equations in pure Python; returns `{intercept: e^b0, exponent: b1, fullSuiteFactor: e^b2}` rounded to 3 decimals.
  - `mdape(rows, params) -> float`: median of `|predicted - minutes| / minutes`.
  - CLI `python3 estimator.py refit (--fixture <json> | --plans-root <docs/plans>) [--write]`: prints the refitted task parameters and their MdAPE as one JSON object; `--plans-root` reads every task file under `done/` and `in-progress/` with a positive `actual` (files = length of `files`, full = full_suite(verify)); task frontmatter is read with ticket.py's `load`, imported by path; `--write` replaces only the `task` block of estimator.json and keeps every other key.
- `plugins/workbench/scripts/tests/fixtures/estimator_tasks.json`: the 94 measured tasks as `[{task, files, full, minutes}]`, copied from the `task`, `files`, `full` and `agent_min` fields of the measured data file named in Notes.

## Acceptance conditions

- AC1: full_suite is true for every full-suite example and false for every targeted example in the requirement [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_full_suite_patterns]
- AC2: a command equal to a repo suites entry counts as the full suite [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_full_suite_matches_repo_suites]
- AC3: task_minutes gives 6 for 4 files targeted, 39 for 4 files full suite and 4 for 0 files targeted [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_task_minutes_formula]
- AC4: epic_estimate on epic A's numbers (sum 1341, critical path 325, 62 open tasks) gives p 3.0, runWall 447 and epicWall 894 [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_epic_estimate_epic_a]
- AC5: parallelism is 1.5 at 10 tasks, 1.6 at 16 and 3.0 at 40 [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_parallelism_interpolates]
- AC6: the shipped parameters have MdAPE under 0.5 on the 94-task fixture [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_fixture_mdape_under_half]
- AC7: refit over the fixture reproduces intercept 4.0 within 0.2, exponent 0.22 within 0.03 and full-suite factor 6.9 within 0.5 [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_refit_reproduces_params]
- AC8: every parameter is read from estimator.json: a temp copy with another intercept changes task_minutes [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_params_come_from_json]
- AC9: the refit CLI with --write replaces only the task block of the JSON [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_refit_cli_writes_task_params]

## Files

- `plugins/workbench/scripts/lib/estimator.json`
- `plugins/workbench/scripts/lib/estimator.py`
- `plugins/workbench/scripts/tests/test_estimator.py`
- `plugins/workbench/scripts/tests/fixtures/estimator_tasks.json`

## Interfaces

- Owns `estimator-params`: `plugins/workbench/scripts/lib/estimator.json` and the functions `load`, `full_suite`, `task_minutes`, `parallelism`, `epic_estimate`, `refit`, `mdape` in `plugins/workbench/scripts/lib/estimator.py`. estimate-and-actuals imports the module; planner-sizing-rule reads `fullSuitePatterns` from the JSON in node.

## Expected outcome

One JSON holds every estimator number and the full-suite patterns; the formula, the epic line and the refit are tested against the 94 measured tasks of the 2026-10-20/21 session.

## Steps

- Red: write `plugins/workbench/scripts/tests/test_estimator.py` with AC1-AC9 and the fixture; run `cd plugins/workbench && pytest scripts/tests/test_estimator.py -q`; expect failures (no module).
- Green: write estimator.json, then estimator.py.
- Run `cd plugins/workbench && pytest scripts/tests/test_estimator.py -q && ruff check scripts`; expect all passed and `All checks passed!`.

## Notes

- Measured data: `/Users/szymonri/Documents/workbench/docs/research/flow-token-optimization/data/F/task_actuals.json (local-only research copy, never commit docs/research)` (94 rows; use `task`, `files`, `full`, `agent_min`). If it is missing, return `blocked` with whoCanClear "orchestrator: regenerate it with docs/research/flow-token-optimization/parse_agents.py".
- The brief's fit (numpy, same data) gave intercept 3.996, exponent 0.2203, factor 6.865 and in-sample MdAPE 0.443 with the rounded parameters.
- Floor minutes at 1 before the log, as the brief's fit did.
- Import ticket.py's `load` by path with `importlib` (see how `ticket_cmds/args.py` loads `scripts/lib/workbench.py`); do not copy the frontmatter parser.
