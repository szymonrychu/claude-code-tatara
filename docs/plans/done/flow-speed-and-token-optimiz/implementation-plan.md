# Flow speed and token optimization implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: Cache probe

- Status: done
- Files: `plugins/workbench/workflows/hook-probe.js`, `plugins/workbench/workflows/tests/hook-probe.test.mjs`, `plugins/workbench/scripts/hook-evidence.py`, `plugins/workbench/scripts/tests/test_hook_evidence.py`
- Verify: `cd plugins/workbench && node --test workflows/tests/hook-probe.test.mjs && pytest scripts/tests/test_hook_evidence.py -q && ruff check scripts`
- Verified head: 0a7b69478789916ba7f84cb8d086d3181d16b18d

#### Requirement

Build the measurement that decides the prompt-cache change (design D6). The probe runs before any prompt is reordered.

- `plugins/workbench/workflows/hook-probe.js`: with `args.probe === 'cache'` it skips the four hook probes and the `args.worktree` check and runs two phases. `Cache static-first`: three agents dispatched one after another (`agentType: 'workbench:implementer'`, model sonnet, effort low), whose prompts share an identical static block of at least 4000 characters and differ only in a last line `Probe <n>: reply with ok true`. `Cache task-first`: the same three with the varying line first. Labels `probe:cache:static#1` to `#3` and `probe:cache:task#1` to `#3`. It returns `{probe: 'cache', labels: [...]}`. Without `args.probe` the existing behaviour is unchanged.
- `plugins/workbench/scripts/hook-evidence.py --cache <run dir> [--json]`: reads `journal.jsonl` labels and each `agent-<id>.jsonl`, takes the first assistant message's `usage.cache_creation_input_tokens` and `usage.cache_read_input_tokens` and the transcript `cwd`, prints one line per label, then a verdict line: `CACHE saving static=<n2>,<n3> task=<m2>,<m3>` when the second and third static-first agents each created fewer than 5000 tokens, else `CACHE none static=... task=...`. `--json` prints `{agents: [{label, cacheCreation, cacheRead, cwd}], verdict}`. The existing hook counting is unchanged.

#### Acceptance conditions

- AC1: cache mode dispatches three static-first agents then three task-first agents, one at a time [evidence: test:plugins/workbench/workflows/tests/hook-probe.test.mjs::cache-probe-runs-six-serial-agents-without-worktree]
- AC2: the static-first prompts share an identical block of at least 4000 characters [evidence: test:plugins/workbench/workflows/tests/hook-probe.test.mjs::cache-probe-prompts-share-a-static-block]
- AC3: hook-evidence prints CACHE saving when the second and third static-first agents create under 5000 tokens [evidence: test:plugins/workbench/scripts/tests/test_hook_evidence.py::test_cache_saving_verdict]
- AC4: hook-evidence prints CACHE none otherwise [evidence: test:plugins/workbench/scripts/tests/test_hook_evidence.py::test_cache_none_verdict_and_json]
- AC5: the JSON output lists creation, read and cwd per agent [evidence: test:plugins/workbench/scripts/tests/test_hook_evidence.py::test_cache_none_verdict_and_json]
- AC6: the existing hook-probe and hook-evidence tests still pass [evidence: command:cd plugins/workbench && node --test workflows/tests/hook-probe.test.mjs && pytest scripts/tests/test_hook_evidence.py -q]

#### Files

- `plugins/workbench/workflows/hook-probe.js`
- `plugins/workbench/workflows/tests/hook-probe.test.mjs`
- `plugins/workbench/scripts/hook-evidence.py`
- `plugins/workbench/scripts/tests/test_hook_evidence.py`

#### Interfaces

- Owns `cache-probe-verdict`: the `CACHE saving|none` line and the `--json` shape of `hook-evidence.py --cache`, in `plugins/workbench/scripts/hook-evidence.py`. cache-prefix-change acts on the verdict the orchestrator records.

#### Expected outcome

One Workflow run plus one command says whether static-first prompts make the second and later agents read the cache instead of writing it.

#### Steps

- Red: add AC1-AC2 to `workflows/tests/hook-probe.test.mjs` and AC3-AC5 to `scripts/tests/test_hook_evidence.py` (fixture run dirs with fake journal and transcript rows); run `cd plugins/workbench && node --test workflows/tests/hook-probe.test.mjs && pytest scripts/tests/test_hook_evidence.py -q`; expect failures.
- Green: the cache mode and `--cache`.
- Run the task verify; expect all green.

#### Notes

- After this task lands on the epic branch, the orchestrator runs `Workflow({scriptPath: '<integration tree>/plugins/workbench/workflows/hook-probe.js', args: {probe: 'cache'}})`, then `hook-evidence.py --cache <run dir> --json`, and records the JSON and the verdict in design.md under `## Cache probe result` (D6).
- Measured: per-agent cache writes are 17k to 28k and cross-agent sharing is near zero, even for the static-first reviewPrompt (brief (a) Cache); the probe separates prompt order from launch concurrency by dispatching serially.
- Node test titles are single kebab tokens.

### S2: Continue launch

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py`, `plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py`
- Verify: `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_continue_launch.py skills/start-development/tests/test_ticket_continue.py -q && ruff check skills`
- Verified head: e5ec85e53c596b77938b213c41f305bbfa2b2520

#### Requirement

Make `ticket.py continue` a one-shot relaunch and auto-accept the findings that need no judgement (design D3, D8).

- Auto-accept: after the return is applied, every task the return marks `verified: true` and either `processOnly: true` with `stopped` other than `review-shallow`, or `triageRejected: true`, whose status is not `done`, is accepted exactly as `--accept` does, with reason `auto-accepted: processOnly` or `auto-accepted: triageRejected`, and printed `<task>: auto-accepted (<why>)`. Rerunning continue records nothing twice. An unverified task is never auto-accepted.
- `--launch`: for each task the merge gate would print a `MERGE` line for (every done task not yet contained in `<epic>`), run `merge.py --name <recorded tree name> --base <epic> [--repo <repo>] --keep --no-suites --verify '<task verify>'` from the main checkout as a subprocess (`skills/worktree-merge/scripts/merge.py`). Exit 0 is a landing. A non-zero exit keeps that task's `MERGE` line; when any line remains, continue prints them and exits 2 exactly as today, leaving both trees as merge.py left them.
- With nothing left to land, `--launch` finishes the existing steps (worktrees refresh, facts, args and named copy) and prints exactly two final lines: `LAUNCH <named copy script path> <args json path>` and `ARM python3 <plugin root>/skills/heartbeat/scripts/heartbeat.py --run <runId> --total <open task count>`.
- Without `--launch`, output and exit codes are unchanged apart from the auto-accept lines.
- Relaunch scope: the args continue writes never contain a done task; they hold every escalated, blocked, dependency-failed (reset to todo) and unstarted task.

#### Acceptance conditions

- AC1: continue auto-accepts a verified processOnly task with a ruling and prints the line once across reruns [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_continue_auto_accepts_process_only]
- AC2: continue auto-accepts a verified triageRejected task and never an unverified or review-shallow one [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_continue_auto_accepts_triage_rejected_only_when_verified]
- AC3: --launch lands each clean done task through merge.py and prints no MERGE line for it [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_launch_uses_task_verify]
- AC4: a failed landing keeps its MERGE line, exits 2 and leaves the task tree and the epic branch intact [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_launch_keeps_merge_line_on_failure]
- AC5: --launch ends with one LAUNCH line and one ARM line [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_launch_prints_launch_and_arm_lines]
- AC6: the relaunch args hold no done task and every escalated, dependency-failed and unstarted one [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_relaunch_args_hold_only_open_tasks]
- AC7: the existing continue tests still pass [evidence: command:cd plugins/workbench && pytest skills/start-development/tests/test_ticket_continue.py -q]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py`

#### Interfaces

- Owns `continue-launch-lines`: the auto-accept lines and the `LAUNCH` and `ARM` lines, defined in `ticket_cmds/continue_cmd.py`.
- Uses `merge-target-worktree` (epic integration worktrees): merge.py's CLI `--name --base --repo --keep --no-suites --verify`, exit 0 merged, 1 error or conflict, 4 verify or suite failure.

#### Expected outcome

After a run returns, one command applies it, accepts what needs no judgement, lands what is clean and prints the one Workflow launch and the one heartbeat arm; only a conflict or a red verify still needs a worktree-merger.

#### Steps

- Red: write `skills/start-development/tests/test_ticket_continue_launch.py` with AC1-AC6 on the real-git fixtures of `ticket_repo_helpers.py` (an epic branch, task trees, a return JSON); run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_continue_launch.py -q`; expect failures.
- Green: auto-accept after `_apply`, the `--launch` flag, the merge.py subprocess per gate line, the two final lines.
- Run the task verify; expect all passed.

#### Notes

- continue_cmd.py was changed by epic integration worktrees (epic-base-wiring, epic-close-command): the merge gate lists every done task not on `<epic>` and the base is the epic branch. Read the landed code first.
- The recorded tree name is the last path component of the task's `worktree` (strip a trailing `/<repo>` in component mode), the rule the land step uses.
- Use the existing `_rule` path for auto-accepts so rulings.json and the task body match manual accepts.

### S3: Estimator model

- Status: done
- Files: `plugins/workbench/scripts/lib/estimator.json`, `plugins/workbench/scripts/lib/estimator.py`, `plugins/workbench/scripts/tests/test_estimator.py`, `plugins/workbench/scripts/tests/fixtures/estimator_tasks.json`
- Verify: `cd plugins/workbench && pytest scripts/tests/test_estimator.py -q && ruff check scripts`
- Verified head: 3a1ea040255888a4a4e5e17169fbb748951481d4

#### Requirement

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

#### Acceptance conditions

- AC1: full_suite is true for every full-suite example and false for every targeted example in the requirement [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_full_suite_patterns]
- AC2: a command equal to a repo suites entry counts as the full suite [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_full_suite_matches_repo_suites]
- AC3: task_minutes gives 6 for 4 files targeted, 39 for 4 files full suite and 4 for 0 files targeted [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_task_minutes_formula]
- AC4: epic_estimate on epic A's numbers (sum 1341, critical path 325, 62 open tasks) gives p 3.0, runWall 447 and epicWall 894 [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_epic_estimate_epic_a]
- AC5: parallelism is 1.5 at 10 tasks, 1.6 at 16 and 3.0 at 40 [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_parallelism_interpolates]
- AC6: the shipped parameters have MdAPE under 0.5 on the 94-task fixture [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_fixture_mdape_under_half]
- AC7: refit over the fixture reproduces intercept 4.0 within 0.2, exponent 0.22 within 0.03 and full-suite factor 6.9 within 0.5 [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_refit_reproduces_params]
- AC8: every parameter is read from estimator.json: a temp copy with another intercept changes task_minutes [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_params_come_from_json]
- AC9: the refit CLI with --write replaces only the task block of the JSON [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_refit_cli_writes_task_params]

#### Files

- `plugins/workbench/scripts/lib/estimator.json`
- `plugins/workbench/scripts/lib/estimator.py`
- `plugins/workbench/scripts/tests/test_estimator.py`
- `plugins/workbench/scripts/tests/fixtures/estimator_tasks.json`

#### Interfaces

- Owns `estimator-params`: `plugins/workbench/scripts/lib/estimator.json` and the functions `load`, `full_suite`, `task_minutes`, `parallelism`, `epic_estimate`, `refit`, `mdape` in `plugins/workbench/scripts/lib/estimator.py`. estimate-and-actuals imports the module; planner-sizing-rule reads `fullSuitePatterns` from the JSON in node.

#### Expected outcome

One JSON holds every estimator number and the full-suite patterns; the formula, the epic line and the refit are tested against the 94 measured tasks of the 2026-10-20/21 session.

#### Steps

- Red: write `plugins/workbench/scripts/tests/test_estimator.py` with AC1-AC9 and the fixture; run `cd plugins/workbench && pytest scripts/tests/test_estimator.py -q`; expect failures (no module).
- Green: write estimator.json, then estimator.py.
- Run `cd plugins/workbench && pytest scripts/tests/test_estimator.py -q && ruff check scripts`; expect all passed and `All checks passed!`.

#### Notes

- Measured data: `/Users/szymonri/Documents/workbench/docs/research/flow-token-optimization/data/F/task_actuals.json (local-only research copy, never commit docs/research)` (94 rows; use `task`, `files`, `full`, `agent_min`). If it is missing, return `blocked` with whoCanClear "orchestrator: regenerate it with docs/research/flow-token-optimization/parse_agents.py".
- The brief's fit (numpy, same data) gave intercept 3.996, exponent 0.2203, factor 6.865 and in-sample MdAPE 0.443 with the rounded parameters.
- Floor minutes at 1 before the log, as the brief's fit did.
- Import ticket.py's `load` by path with `importlib` (see how `ticket_cmds/args.py` loads `scripts/lib/workbench.py`); do not copy the frontmatter parser.

### S4: Heartbeat quiet

- Status: done
- Files: `plugins/workbench/skills/heartbeat/scripts/heartbeat.py`, `plugins/workbench/skills/heartbeat/SKILL.md`, `plugins/workbench/skills/heartbeat/tests/test_heartbeat.py`, `plugins/workbench/skills/heartbeat/tests/test_heartbeat_run.py`, `AGENTS.md`
- Verify: `bash mise-tasks/lint/agents-md && python3 scripts/harness/setup.py --check && cd plugins/workbench && bash scripts/run-tests.sh --only heartbeat && ruff check skills`
- Verified head: b28fd1767a9f721420d0ebba9a14678a8e68a12d

#### Requirement

Make the heartbeat quiet by default (design D3, gate question Q1).

- heartbeat.py keeps polling every `--interval` seconds (default 600). New `--report-every` seconds (default 1800): a progress line prints only when the journal digest differs from the digest last printed and at least report-every seconds passed since the last printed line (the first changed beat after arming prints). An unchanged digest prints nothing.
- STALL (journal size unchanged for `--stall-beats` polls, default 3) and END print at once, whatever the report interval. `waiting for run <id>` prints at most once per report interval.
- The haiku ETA runs only with the new `--eta` flag; `--no-eta` is still accepted and changes nothing; by default no `claude` process is started.
- `--keepalive` (5-minute cache) prints every beat as today, because its purpose is the wake.
- `skills/heartbeat/SKILL.md`: the description, the arm command and a new `## Quiet by default` section state the default: silent while nothing changes, a progress line at most every 30 minutes, STALL and END at once, ETA opt-in with `--eta`.
- Root `AGENTS.md` ground rule 4 gets one sentence: the heartbeat of a plan-execute run is the bounded watcher for that wait; it prints END and STALL at once and progress at most every 30 minutes, so silence between its lines is not a broken watcher.

#### Acceptance conditions

- AC1: a beat with an unchanged digest prints nothing [evidence: test:plugins/workbench/skills/heartbeat/tests/test_heartbeat_run.py::test_unchanged_digest_prints_nothing]
- AC2: a changed digest prints at most once per report interval [evidence: test:plugins/workbench/skills/heartbeat/tests/test_heartbeat_run.py::test_progress_line_at_most_every_report_interval]
- AC3: STALL and END print at once [evidence: test:plugins/workbench/skills/heartbeat/tests/test_heartbeat_run.py::test_stall_and_end_print_immediately]
- AC4: no claude call by default; --eta makes it [evidence: test:plugins/workbench/skills/heartbeat/tests/test_heartbeat.py::test_eta_is_opt_in]
- AC5: --keepalive still prints every beat [evidence: test:plugins/workbench/skills/heartbeat/tests/test_heartbeat_run.py::test_keepalive_still_prints_every_beat]
- AC6: the skill documents the quiet default [evidence: doc-section:plugins/workbench/skills/heartbeat/SKILL.md#Quiet by default]
- AC7: AGENTS.md names the heartbeat bound and stays under its size limit [evidence: command:grep -q 'progress at most every 30 minutes' AGENTS.md && bash mise-tasks/lint/agents-md && python3 scripts/harness/setup.py --check]

#### Files

- `plugins/workbench/skills/heartbeat/scripts/heartbeat.py`
- `plugins/workbench/skills/heartbeat/SKILL.md`
- `plugins/workbench/skills/heartbeat/tests/test_heartbeat.py`
- `plugins/workbench/skills/heartbeat/tests/test_heartbeat_run.py`
- `AGENTS.md`

#### Interfaces

- CLI: `heartbeat.py (--run <id> | --journal <path>) [--interval S] [--report-every S] [--stall-beats N] [--eta] [--no-eta] [--keepalive] ...`; the line formats (`~<pct>% done...`, `STALL <n>m no journal change`, `END ...`) are unchanged.

#### Expected outcome

A waiting orchestrator wakes when a run ends or stalls and otherwise at most twice an hour, with no haiku call per beat.

#### Steps

- Red: add AC1-AC5 to `skills/heartbeat/tests/test_heartbeat_run.py` and `test_heartbeat.py` (inject the clock and sleep as the existing tests do); run `cd plugins/workbench && bash scripts/run-tests.sh --only heartbeat`; expect failures.
- Green: the report gate in `main`, the `--eta` flag, the SKILL.md section, the AGENTS.md sentence.
- Run the task verify; expect green.

#### Notes

- If the user answers no to Q1, the orchestrator amends this task to `--report-every 600` before the run; nothing else changes.
- AGENTS.md line 87 (ground rule 4) is outside the generated `workbench:rules` block; edit only that rule's text.
- Keep the STALL arithmetic on polls, not on printed lines.

### S5: Verify task bounded runs

- Status: done
- Files: `plugins/workbench/scripts/verify-task.py`, `plugins/workbench/scripts/tests/test_verify_bounded.py`, `plugins/workbench/scripts/tests/test_verify_tdd_revert_dirs.py`, `plugins/workbench/scripts/tests/test_verify_task.py`, `plugins/workbench/agents/verifier.md`
- Verify: `cd plugins/workbench && pytest scripts/tests/test_verify_bounded.py scripts/tests/test_verify_tdd_revert_dirs.py scripts/tests/test_verify_task.py scripts/tests/test_verify_ref_runner.py scripts/tests/test_verify_command_tail.py -q && ruff check scripts`
- Verified head: d7962ed841c161d2f01d674424f7baf11361abd7

#### Requirement

Bound every run verify-task makes and stop the third suite run (design D1). `plugins/workbench/scripts/verify-task.py` only, plus the verifier agent's Bash timeout.

- `run_shell` and `run_argv` take a timeout. New `--timeout` seconds per command (default 480, so two runs plus triage fit the verifier's 600 s Bash call). On expiry the process group is killed and the result carries `timeout: {command, seconds}`, `exit: 124`, `passed: false` and the output tail captured so far as `evidence`. The limit applies to the main command, each `command:` AC, each `test:` ref re-run, each install step and the TDD-revert base run.
- `--prev-head` that does not match `^[0-9a-f]{7,40}$` yields one JSON result with `passed: false` and `error: "prev-head is not a sha: <first 40 chars>"` and exit 2, never an argparse usage error. A valid sha keeps `changedSincePrevious`.
- `--tdd-revert`: on the reverted base, run only the runner commands of the AC `test:` refs (one per ref file, built with the runner resolution check_ac already uses) when the task has any, else the command. `passedOnHead` reuses the main run's exit code instead of running again, so one verify-task call runs the command at most twice. `tdd.baseCommand` records what ran on base.
- `--cmd` becomes optional. `--targeted`, or no `--cmd`, builds the command from the runner of each AC `test:` ref file and of each changed test file (matched by `--test-re`), deduplicated, joined with ` && `. The result's `command` is the built command and `commandScope` is `"targeted"`; with no refs and no changed test files the result is `passed: false` with `error: "no targeted tests"`.
- `plugins/workbench/agents/verifier.md`: the one Bash call that runs verify-task sets `timeout: 600000`.

#### Acceptance conditions

- AC1: a command that outlives --timeout yields a timeout field, exit 124 and passed false in one JSON result [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_command_timeout_reports_timeout_field]
- AC2: a non-sha --prev-head yields a JSON error result, not an argparse failure [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_non_sha_prev_head_is_a_json_error]
- AC3: --tdd-revert runs the command at most twice and only the AC-referenced tests on base [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_tdd_revert_runs_at_most_twice]
- AC4: --targeted builds the command from the AC test refs and the changed test files [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_targeted_builds_command_from_refs_and_changed_tests]
- AC5: --targeted with no tests to run fails with error no targeted tests [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_targeted_without_tests_fails_with_error]
- AC6: the existing verify-task tests still pass [evidence: command:cd plugins/workbench && pytest scripts/tests/test_verify_tdd_revert_dirs.py scripts/tests/test_verify_task.py scripts/tests/test_verify_ref_runner.py scripts/tests/test_verify_command_tail.py -q]
- AC7: the verifier agent sets the 600000 ms Bash timeout [evidence: command:grep -q 'timeout: 600000' plugins/workbench/agents/verifier.md]

#### Files

- `plugins/workbench/scripts/verify-task.py`
- `plugins/workbench/scripts/tests/test_verify_bounded.py`
- `plugins/workbench/scripts/tests/test_verify_tdd_revert_dirs.py`
- `plugins/workbench/scripts/tests/test_verify_task.py`
- `plugins/workbench/agents/verifier.md`

#### Interfaces

- Owns `verify-task-cli`: the flags `--timeout`, `--targeted`, optional `--cmd`, the sha rule for `--prev-head`, and the result fields `timeout`, `error`, `commandScope`, `tdd.baseCommand`, all in `plugins/workbench/scripts/verify-task.py`. verify-scope-wiring passes them from plan-execute.

#### Expected outcome

No verifier dies at the Bash cap, no orchestrator prose reaches argparse, and a TDD-revert check costs one extra run of the referenced tests instead of two runs of the whole command.

#### Steps

- Red: write `scripts/tests/test_verify_bounded.py` with AC1-AC5 on throwaway git repos (a `sleep` command for the timeout, a pytest file with a renamed test for the targeted build); run `cd plugins/workbench && pytest scripts/tests/test_verify_bounded.py -q`; expect failures.
- Green: timeouts, the sha check, the revert change, `--targeted`; update `test_verify_tdd_revert_dirs.py` where it pinned the third run; the verifier.md line.
- Run the task verify; expect all passed.

#### Notes

- Use `subprocess.run(..., timeout=..., start_new_session=True)` and kill the group on `TimeoutExpired` so a child pytest does not survive.
- The runner resolution for a ref is the one `check_ac` uses (`_runner_cmd`, refRunners via `.claude/workbench.json`); reuse it, do not write a second resolver.
- Measured: 46 verify-task calls hit the 600 s cap, 4 verifiers died, 5 argparse failures from prose passed as `--prev-head` (brief failure mode 3).

### S6: Estimate and actuals

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket_cmds/estimate.py`, `plugins/workbench/skills/start-development/scripts/ticket.py`, `plugins/workbench/skills/start-development/scripts/ticket_cmds/roadmap.py`, `plugins/workbench/skills/start-development/templates/task.md`, `plugins/workbench/skills/start-development/tests/test_ticket_estimate.py`, `plugins/workbench/skills/start-development/tests/test_ticket_run.py`, `plugins/workbench/skills/start-development/tests/test_ticket_roadmap.py`
- Verify: `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_estimate.py skills/start-development/tests/test_ticket_run.py skills/start-development/tests/test_ticket_roadmap.py skills/start-development/tests/test_templates.py skills/start-development/tests/test_ticket_cmd_modules.py -q && ruff check scripts skills`
- Verified head: 65c5cb826ba0b06ee7a1101715827f8d252b4c4b

#### Requirement

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

#### Acceptance conditions

- AC1: estimate writes formula minutes and estimate_by formula to every task not marked override and keeps an override untouched [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_estimate.py::test_estimate_writes_formula_minutes_and_keeps_overrides]
- AC2: the README Time line shows sum, critical path, expected wall at P with k, actual and remaining [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_estimate.py::test_time_line_shows_critical_path_and_expected_wall]
- AC3: estimate prints the three longest-path tasks and --json prints the estimate dict [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_estimate.py::test_estimate_prints_three_longest_path_tasks]
- AC4: new-task records estimate_by formula without --estimate and override with it [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_estimate.py::test_new_task_estimate_by]
- AC5: run-dir labels ending in #n or +n map to their task [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_estimate.py::test_run_dir_matches_hash_n_labels]
- AC6: apply-run with a run dir writes actual as summed agent minutes and actual_roles per role [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_estimate.py::test_apply_run_writes_actual_and_roles]
- AC7: roadmap reads the sum from the new Time line [evidence: command:cd plugins/workbench && pytest skills/start-development/tests/test_ticket_roadmap.py -q]
- AC8: the updated run tests pass [evidence: command:cd plugins/workbench && pytest skills/start-development/tests/test_ticket_run.py skills/start-development/tests/test_templates.py -q]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/estimate.py`
- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/roadmap.py`
- `plugins/workbench/skills/start-development/templates/task.md`
- `plugins/workbench/skills/start-development/tests/test_ticket_estimate.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_run.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_roadmap.py`

#### Interfaces

- Uses `estimator-params` (estimator-model): `estimator.task_minutes`, `estimator.epic_estimate`, imported by path from `plugins/workbench/scripts/lib/estimator.py`.
- Owns `epic-time-line`: the Time line format and the `estimate` subcommand output, defined in `ticket_cmds/estimate.py` (time_summary in ticket.py calls it).
- Task frontmatter keys `estimate_by` (`formula` or `override`) and `actual_roles` (quoted scalar).

#### Expected outcome

`ticket.py estimate <epic>` gives every task realistic agent minutes and the README shows the epic's critical path and expected wall; after a run, `continue --run` fills `actual` and the role split, so the record compares estimate and actual per task.

#### Steps

- Red: write `skills/start-development/tests/test_ticket_estimate.py` with AC1-AC6 (fixture epics via `ticket_repo_helpers.py`; a fake run dir with `journal.jsonl` and `agent-<id>.jsonl` rows carrying labels like `<epic>:verify:<task>#2`); run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_estimate.py -q`; expect failures.
- Green: estimate.py, time_summary, new-task, `_run_dir_durations`, `_actual_update`, roadmap.py; update the old-format assertions in test_ticket_run.py and test_ticket_roadmap.py.
- Run the task verify; expect all passed.

#### Notes

- The Workflow runtime forbids the clock in scripts (`workflows/tests/harness.mjs` CLOCK_ERROR, pinned by `plan-execute-duration.test.mjs`), so actuals come from transcript timestamps after the run, never from plan-execute.
- `heartbeat.py --remaining-min` and the SKILL text read "Remaining estimate"; keep that field name.
- The command module pattern is `register(sub, t)` (see `ticket_cmds/contract.py`); `test_ticket_cmd_modules.py` checks module loading.
- ticket.py was reworked by epic integration worktrees (blocker); read the landed code before editing.

### S7: Planner sizing rule

- Status: done
- Files: `plugins/workbench/workflows/validate-tasks.mjs`, `plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs`, `plugins/workbench/skills/start-development/references/phases-1-3.md`, `plugins/workbench/agents/planner.md`, `plugins/workbench/skills/start-development/tests/test_planner_agent.py`, `plugins/workbench/skills/start-development/tests/test_review_flow_docs.py`
- Verify: `cd plugins/workbench && pytest skills/start-development/tests/test_planner_agent.py skills/start-development/tests/test_review_flow_docs.py -q && bash scripts/run-tests.sh --only workflows`
- Verified head: b90c434c154199a211e1c0523f47a0634be517f6

#### Requirement

Size tasks by test files and verify runtime and enforce targeted verifies at plan time (design D10, D11, D13).

- `plugins/workbench/workflows/validate-tasks.mjs`: read `fullSuitePatterns` from `plugins/workbench/scripts/lib/estimator.json` (path relative to the script) and the repo's workbench.json `suites` (through `scripts/lib/workbench.py config`). A task with status `todo` whose `verify` is the full suite (a part matching a pattern, after a leading `cd <dir>` part, or equal to a `suites` entry) fails with `task <id>: verify '<cmd>' runs the full suite; name the test files or the component suite (run-tests.sh --only <component>) plus lint, and split the task if that is not enough`. A task in any other status gets the same text as a warning only. The over-90 estimate warning and `MAX_ESTIMATE_MIN` are removed.
- `skills/start-development/references/phases-1-3.md`, phase 3: replace "size each task to about an hour, split it when it runs over 90" with: one test file's worth of behaviour, at most 8 files; a targeted verify (named test files or a component suite plus lint, never the full suite); sibling tasks under 3 files that share a test file are merged into one; estimates come from `ticket.py estimate <epic>` and `--estimate` is only an override.
- `plugins/workbench/agents/planner.md`: the same sizing rule, and "read each brief by its heading index: grep its `^#` headings first, then read only the sections the plan needs".
- `test_review_flow_docs.py`'s "about an hour" needle becomes the new rule's needle; `test_planner_agent.py` pins the planner's sizing and heading-index lines.

#### Acceptance conditions

- AC1: a full-suite verify on a todo task fails the lint with the split hint [evidence: test:plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs::full-suite-verify-on-todo-task-fails]
- AC2: a full-suite verify on a started task is a warning only [evidence: test:plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs::full-suite-verify-on-started-task-warns]
- AC3: targeted verifies pass [evidence: test:plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs::targeted-verify-passes]
- AC4: an estimate over 90 no longer warns [evidence: test:plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs::no-estimate-warning]
- AC5: a verify equal to a repo suites entry counts as the full suite [evidence: test:plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs::repo-suites-entry-counts-as-full]
- AC6: the planner agent carries the sizing rule and the heading-index reading [evidence: test:plugins/workbench/skills/start-development/tests/test_planner_agent.py::test_planner_sizing_and_heading_index]
- AC7: phases-1-3.md states the sizing rule by test files and verify runtime [evidence: test:plugins/workbench/skills/start-development/tests/test_review_flow_docs.py::test_phase3_sizing_by_test_files_and_verify_runtime]

#### Files

- `plugins/workbench/workflows/validate-tasks.mjs`
- `plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs`
- `plugins/workbench/skills/start-development/references/phases-1-3.md`
- `plugins/workbench/agents/planner.md`
- `plugins/workbench/skills/start-development/tests/test_planner_agent.py`
- `plugins/workbench/skills/start-development/tests/test_review_flow_docs.py`

#### Interfaces

- Uses `estimator-params` (estimator-model): `fullSuitePatterns` in `plugins/workbench/scripts/lib/estimator.json`, the same list estimator.py reads.

#### Expected outcome

A new plan cannot schedule a full-suite verify inside the task loop, and planners size tasks by what their verify costs, not by a guessed hour.

#### Steps

- Red: write `workflows/tests/validate-tasks-sizing.test.mjs` (AC1-AC5, fixture epics as the other validate-tasks tests build them) and the two doc tests; run `cd plugins/workbench && node --test workflows/tests/validate-tasks-sizing.test.mjs && pytest skills/start-development/tests/test_planner_agent.py skills/start-development/tests/test_review_flow_docs.py -q`; expect failures.
- Green: the lint rule, the two docs, the test needles.
- Run the task verify; expect all green.

#### Notes

- Measured: full-suite tasks were 32% of tasks and 71% of agent-minutes; 1-3 file tasks take 3-7 minutes with about 150k cost-weighted tokens of fixed cost each (brief items 1 and 9).
- In-progress epics keep their full-suite verifies as warnings, so `ticket.py amend` and `decide` (which run this lint) still work on them.
- test_review_flow_docs.py was changed by epic integration worktrees (docs-readmes-fallback); read the landed file first.

### S8: Verify scope wiring

- Status: done
- Files: `plugins/workbench/workflows/plan-execute.js`, `plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs`, `plugins/workbench/workflows/tests/plan-execute-verify.test.mjs`
- Verify: `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`
- Verified head: 3653ea8845aa1a8819f00579e2d6227811a44daf

#### Requirement

Wire plan-execute to the bounded verifier and schedule verifies (design D1, D12). `plugins/workbench/workflows/plan-execute.js`.

- `verifyCommand(t)` is `t.verify` and never `impl.verification.command`. With no `t.verify` the verifier prompt passes `--targeted` and no `--cmd`. The forward-merge prompt's verify step follows the same rule (with no `t.verify` it runs the verifier's verify-task `--targeted` invocation).
- `--prev-head` is passed only when the previous head matches `/^[0-9a-f]{7,40}$/`, quoted with `shq`; otherwise it is omitted.
- verifyPrompt tells the agent to run the command in ONE Bash call with `timeout: 600000`.
- At most 2 verifier agents run at once per repo: `independentVerify` waits on a per-repo FIFO queue and the next queued verify starts the moment one ends. Other roles are not limited. A queued verify always starts eventually (no deadlock when tasks of one repo wait on each other).
- When several tasks become ready in the same pump, they begin in descending order of their count of transitive dependents, ties in input order (plan-execute reads no estimate).
- The land step keeps `--no-suites --verify <task verify>`: the full suite runs once at epic close (blocker D5), never per task. A test pins the land command.
- Existing tests that expected the implementer-command fallback are updated.

#### Acceptance conditions

- AC1: the verifier never runs the implementer's own command [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs::verify-never-uses-implementer-command]
- AC2: a task without verify gets --targeted and no --cmd [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs::verify-without-task-verify-passes-targeted]
- AC3: --prev-head is passed only as a quoted sha [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs::prev-head-passed-only-as-quoted-sha]
- AC4: the verifier prompt sets the 600000 ms Bash timeout [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs::verify-prompt-sets-bash-timeout]
- AC5: at most two verifiers run at once per repo and every queued one starts [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs::at-most-two-verifies-per-repo]
- AC6: ready tasks start in descending order of transitive dependents [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs::ready-tasks-start-in-critical-path-order]
- AC7: the land command keeps the task verify and --no-suites [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs::land-command-keeps-task-verify-and-no-suites]
- AC8: the workflows suite is green [evidence: command:cd plugins/workbench && bash scripts/run-tests.sh --only workflows]

#### Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs`
- `plugins/workbench/workflows/tests/plan-execute-verify.test.mjs`

#### Interfaces

- Uses `verify-task-cli` (verify-task-bounded-runs): `--targeted`, optional `--cmd`, sha-only `--prev-head`.
- Uses `land-step` (epic integration worktrees): the land command line built in plan-execute.js.

#### Expected outcome

Every verify in the loop runs targeted tests inside the Bash cap, at most two suites contend per repo, and the longest dependency chains start first.

#### Steps

- Red: write `workflows/tests/plan-execute-verify-scope.test.mjs` on `workflows/tests/harness.mjs` with AC1-AC7 (fake agents with delays for the concurrency count); run `cd plugins/workbench && node --test workflows/tests/plan-execute-verify-scope.test.mjs`; expect failures.
- Green: verifyCommand, the prev-head guard, the prompt line, the per-repo queue, the start order; update `plan-execute-verify.test.mjs`.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`; expect all green.

#### Notes

- The script cannot read a clock or a file; the queue is promise-based (see `runTasks` and `pump`).
- Measured: full-suite verifies were 57 of 206 and 636 agent-minutes; 3-4 concurrent suites are what pinned verifies at 600 s (brief items 1 and 11).
- plan-execute.js was reworked by epic integration worktrees (land-in-run, fork-point-diffs); read the landed code first.

### S9: AC evidence map

- Status: done
- Files: `plugins/workbench/workflows/plan-execute.js`, `plugins/workbench/scripts/verify-task.py`, `plugins/workbench/agents/implementer.md`, `plugins/workbench/agents/scope-auditor.md`, `plugins/workbench/scripts/tests/test_verify_ac_evidence.py`, `plugins/workbench/workflows/tests/plan-execute-ac-evidence.test.mjs`
- Verify: `cd plugins/workbench && pytest scripts/tests/test_verify_ac_evidence.py scripts/tests/test_verify_task.py scripts/tests/test_verify_ref_runner.py -q && ruff check scripts && bash scripts/run-tests.sh --only workflows`
- Verified head: 1f6bbfba60932838ccffaaca3eeee056ee46cefb

#### Requirement

Carry acceptance conditions to the implementer and resolve renamed test refs by evidence (design D2). The harness-config-migrate#1 case (AC3-AC5 ref-missing although the tests existed under other names) must not recur.

- `implPrompt` and `fixPrompt` include, when `t.ac` exists, a block `Acceptance conditions (prove each; return acEvidence):` with one line per AC: `<id>: <text> [<kind>: <ref>]`.
- The implementer and fixer result schema gains optional `acEvidence`: an object mapping AC id to the final `file::name` of the test that proves it.
- `verifyPrompt`: when the latest implementer or fixer result has `acEvidence`, the agent writes it as JSON to a second temp file and passes `--ac-evidence "$ACE"`.
- `verify-task.py --ac-evidence <file>`: a `test:` AC resolves in this order: (1) the acEvidence entry for its id, when that file exists and defines that name; (2) the exact ref (today's lookup); (3) the single test in the ref's file (after the existing basename lookup) whose name contains the ref's name or is contained in it. Each AC result carries `matchedBy: acEvidence|exact|substring` and `resolvedRef`. Zero or several substring candidates keep today's ref-missing result.
- An AC resolved by `substring` is listed in the task's `acsForAudit`, so the audit shows it `open: judge it`.
- `plugins/workbench/agents/implementer.md`: return `acEvidence` naming the final test of every `test:` AC. `plugins/workbench/agents/scope-auditor.md`: an AC row with `matchedBy: substring` is judged by reading the test.

#### Acceptance conditions

- AC1: impl and fix prompts carry the AC list [evidence: test:plugins/workbench/workflows/tests/plan-execute-ac-evidence.test.mjs::impl-and-fix-prompts-carry-the-ac-list]
- AC2: the verifier passes the implementer's acEvidence as --ac-evidence [evidence: test:plugins/workbench/workflows/tests/plan-execute-ac-evidence.test.mjs::verify-passes-ac-evidence-file]
- AC3: an AC matched by substring is open for the audit [evidence: test:plugins/workbench/workflows/tests/plan-execute-ac-evidence.test.mjs::substring-match-is-open-for-audit]
- AC4: verify-task resolves acEvidence, then exact, then substring, and records matchedBy [evidence: test:plugins/workbench/scripts/tests/test_verify_ac_evidence.py::test_resolution_order_and_matched_by]
- AC5: a fixture modelled on harness-config-migrate#1 (refs naming tests later renamed) yields no ref-missing [evidence: test:plugins/workbench/scripts/tests/test_verify_ac_evidence.py::test_renamed_tests_fixture_has_no_ref_missing]
- AC6: an ambiguous substring match stays ref-missing [evidence: test:plugins/workbench/scripts/tests/test_verify_ac_evidence.py::test_ambiguous_substring_stays_ref_missing]
- AC7: the implementer and scope-auditor agents name acEvidence and matchedBy [evidence: command:grep -q acEvidence plugins/workbench/agents/implementer.md && grep -q matchedBy plugins/workbench/agents/scope-auditor.md]

#### Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/scripts/verify-task.py`
- `plugins/workbench/agents/implementer.md`
- `plugins/workbench/agents/scope-auditor.md`
- `plugins/workbench/scripts/tests/test_verify_ac_evidence.py`
- `plugins/workbench/workflows/tests/plan-execute-ac-evidence.test.mjs`

#### Interfaces

- Owns `ac-evidence`: the `acEvidence` result field (AC id to `file::name`) in plan-execute.js's implementer schema, and verify-task's `matchedBy` and `resolvedRef` per AC. audit-context-and-models reads `matchedBy` to decide which rows the verifier settled.
- verify-task flag `--ac-evidence <json file>`.

#### Expected outcome

An AC whose test was renamed resolves on the first verify instead of costing a fix round; a loose match is visible to the auditor.

#### Steps

- Red: write `scripts/tests/test_verify_ac_evidence.py` (AC4-AC6, throwaway git repos with pytest files) and `workflows/tests/plan-execute-ac-evidence.test.mjs` (AC1-AC3); run `cd plugins/workbench && pytest scripts/tests/test_verify_ac_evidence.py -q && node --test workflows/tests/plan-execute-ac-evidence.test.mjs`; expect failures.
- Green: prompts and schema, verifyPrompt, `_test_name_missing` and `check_ac` in verify-task.py, the two agent docs.
- Run the task verify; expect all green.

#### Notes

- Measured: 58 of 104 fix rounds carried a ref-missing finding; implPrompt and fixPrompt never received `t.ac` although implementer.md asks for exact refs (brief item 2).
- Keep exact before substring; the substring step looks only inside the ref's file.
- Node test titles are single kebab tokens (refRunners `--test-name-pattern {name}`).

### S10: Gate provenance

- Status: done
- Files: `plugins/workbench/scripts/verify-task.py`, `plugins/workbench/workflows/plan-execute.js`, `plugins/workbench/scripts/tests/test_verify_provenance.py`, `plugins/workbench/workflows/tests/plan-execute-provenance.test.mjs`
- Verify: `cd plugins/workbench && pytest scripts/tests/test_verify_provenance.py scripts/tests/test_verify_task.py -q && ruff check scripts && bash scripts/run-tests.sh --only workflows`
- Verified head: 5af4a66c1a5f15553932f603c678b34af113427a

#### Requirement

Stop the parking and debt gates from reporting text a merged dependency added (design D7). The init-engine-new case (AGENTS.md placeholders added by its dependency agents-md, reported against the dependent) must not recur.

- `verify-task.py --exclude-ref <ref>` (repeatable): compute the lines `<ref>` adds relative to `merge-base(<ref>, <base>)`, normalised the way `added_lines` and `drop_moved` normalise, and drop every added line of HEAD whose (file, text) is in that set before `find_debt` and `parking_candidates` run. The result carries `excludedByRef` (the count of dropped lines).
- plan-execute.js: in a run without `args.epic`, verifyPrompt adds `--exclude-ref <branch>` (quoted) for every same-repo dependency branch the task merged (the branches `dependencyLines` names). An epic run adds none, because its diff base is the epic branch or the recorded fork point.
- A line the dependent itself adds is still gated.

#### Acceptance conditions

- AC1: with --exclude-ref, lines added by a merged dependency branch are not gated [evidence: test:plugins/workbench/scripts/tests/test_verify_provenance.py::test_dependency_lines_are_not_gated_with_exclude_ref]
- AC2: without --exclude-ref the same lines are still reported [evidence: test:plugins/workbench/scripts/tests/test_verify_provenance.py::test_without_exclude_ref_dependency_lines_are_gated]
- AC3: a debt marker the dependent adds itself is still reported [evidence: test:plugins/workbench/scripts/tests/test_verify_provenance.py::test_own_debt_is_still_reported]
- AC4: a non-epic run passes each merged same-repo dependency branch as --exclude-ref [evidence: test:plugins/workbench/workflows/tests/plan-execute-provenance.test.mjs::non-epic-verify-excludes-dependency-branches]
- AC5: an epic run passes no --exclude-ref [evidence: test:plugins/workbench/workflows/tests/plan-execute-provenance.test.mjs::epic-verify-passes-no-exclude-ref]

#### Files

- `plugins/workbench/scripts/verify-task.py`
- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/scripts/tests/test_verify_provenance.py`
- `plugins/workbench/workflows/tests/plan-execute-provenance.test.mjs`

#### Interfaces

- Uses `fork-point` (epic integration worktrees): in epic runs the verifier `--base` and the diff base already come from the epic branch or `diffBase(t)`, so no exclusion is needed there.
- verify-task flag `--exclude-ref <ref>` (repeatable) and result field `excludedByRef`.

#### Expected outcome

A dependent is judged only on the lines it wrote, in every run mode.

#### Steps

- Red: write `scripts/tests/test_verify_provenance.py` (a repo where branch `dep` adds `AGENTS.md` placeholder lines with a TODO and a parking phrase, branch `task` merges `dep` and adds clean code) and `workflows/tests/plan-execute-provenance.test.mjs`; run both; expect failures.
- Green: `--exclude-ref` in verify-task.py, the flag in verifyPrompt for non-epic runs.
- Run the task verify; expect all green.

#### Notes

- Measured: 9 of 19 root escalations and 2.0M to 4.0M tokens came from gates on forward-merged dependency text (brief failure mode 1).
- Use `--no-triage` in the tests so no haiku call runs; parking candidates are visible before triage.

### S11: Review tiering

- Status: done
- Files: `plugins/workbench/workflows/plan-execute.js`, `plugins/workbench/workflows/tests/plan-execute-tier-scope.test.mjs`, `plugins/workbench/workflows/tests/plan-execute-tier.test.mjs`, `plugins/workbench/workflows/tests/plan-execute-gate-only-rounds.test.mjs`
- Verify: `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`
- Verified head: e621a7d184cfee12ee4dd472fb3d83eb299fd325

#### Requirement

Make review tiers see the task and skip reviews that add nothing (design D9). `plugins/workbench/workflows/plan-execute.js`.

- verifyPrompt passes `--requirement <shq(t.requirement)>` on every verify that runs the tier call (the first verify of a task), so the tier hint sees the requirement instead of an empty string.
- `reviewTier`: `skip` also applies when every changed file is a doc (`*.md`) or every changed file is a test file (`TEST_FILE_RE`), every AC is met with test, symbol, command or doc-section evidence, the verifier reported no findings, and no changed path matches `RISK_PATH`, whatever the diff size. An explicit `review` value still wins; the verifier's tierHint can still raise the tier.
- Light tier: when a light-tier fixer changed files to fix reviewer findings (the files named by reviewer findings, not gate findings), the loop runs one scoped re-review (effort medium) of the diff `prev..head` over only those files before the task settles. Its findings follow the light rule: one fixer and its verifier, no further review.
- A changed path matching RISK_PATH keeps tier `full`, including doc-only and test-only diffs.

#### Acceptance conditions

- AC1: the first verify passes the task requirement to verify-task [evidence: test:plugins/workbench/workflows/tests/plan-execute-tier-scope.test.mjs::first-verify-passes-the-requirement]
- AC2: a doc-only diff with every AC met skips review [evidence: test:plugins/workbench/workflows/tests/plan-execute-tier-scope.test.mjs::doc-only-diff-with-acs-met-skips-review]
- AC3: a test-only diff with every AC met skips review [evidence: test:plugins/workbench/workflows/tests/plan-execute-tier-scope.test.mjs::test-only-diff-with-acs-met-skips-review]
- AC4: a doc-only diff on a RISK_PATH stays full [evidence: test:plugins/workbench/workflows/tests/plan-execute-tier-scope.test.mjs::risk-path-doc-diff-stays-full]
- AC5: a light-tier fix to reviewer findings gets one scoped re-review of those files [evidence: test:plugins/workbench/workflows/tests/plan-execute-tier-scope.test.mjs::light-fix-to-reviewer-findings-gets-scoped-re-review]
- AC6: the existing tier and gate-only round tests still pass [evidence: command:cd plugins/workbench && node --test workflows/tests/plan-execute-tier.test.mjs workflows/tests/plan-execute-gate-only-rounds.test.mjs]

#### Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-tier-scope.test.mjs`
- `plugins/workbench/workflows/tests/plan-execute-tier.test.mjs`
- `plugins/workbench/workflows/tests/plan-execute-gate-only-rounds.test.mjs`

#### Interfaces

- `reviewTier(t, impl, v, pre)` and the light branch of `reviewUntilClean` in plan-execute.js; verify-task's existing `--requirement` flag.

#### Expected outcome

About a third of first reviews are skipped where the evidence already settles the task, and a light-tier fix is never left unreviewed.

#### Steps

- Red: write `workflows/tests/plan-execute-tier-scope.test.mjs` with AC1-AC5; run `cd plugins/workbench && node --test workflows/tests/plan-execute-tier-scope.test.mjs`; expect failures.
- Green: the flag, the skip rule, the scoped re-review; update `plan-execute-tier.test.mjs` and `plan-execute-gate-only-rounds.test.mjs` where they pinned the old rule.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`; expect all green.

#### Notes

- Today `changedOutside` (plan-execute.js) counts reviewer-finding files as named, so a light-tier fix to them is never re-reviewed (brief flow map section 1).
- `--requirement` is never passed today, so the tier classifier sees "" (verify-task.py `--requirement`).

### S12: Triage one call

- Status: done
- Files: `plugins/workbench/scripts/verify-task.py`, `plugins/workbench/scripts/triage.py`, `plugins/workbench/scripts/tests/test_triage.py`, `plugins/workbench/scripts/tests/test_verify_triage_one_call.py`
- Verify: `cd plugins/workbench && pytest scripts/tests/test_verify_triage_one_call.py scripts/tests/test_triage.py scripts/tests/test_triage_false_finding.py scripts/tests/test_verify_task.py -q && ruff check scripts`
- Verified head: 4e33d73c22ccb4c07e6b9d9c1c74edeb770ed6bc

#### Requirement

Fold verify-task's three haiku calls into one (design D12).

- `plugins/workbench/scripts/triage.py` gains a mode `verify` that takes `{parking: [candidates], acs: [ac plausibility items], tier: {requirement, files, diffstat}}`, every part optional, and returns `{parking: [...], acs: [...], classifierTier}` from ONE `claude -p` haiku call whose schema covers the parts present. The existing modes stay for their other callers.
- `verify-task.py` makes at most one triage call per run: `verify` mode with the parts it needs, and no call at all when no part is needed. Its results fill the same result fields as today (`parking`, `acs[].plausible` and the per-AC notes, `tierHint`). `--no-triage` and `--no-tier` keep their meaning. A failed call falls back as today: a note naming the failure, empty parking, `plausible: null`, `tierHint: null`.
- `triageUsage` counts the one call.

#### Acceptance conditions

- AC1: one verify-task run makes at most one triage call carrying parking, AC plausibility and tier together [evidence: test:plugins/workbench/scripts/tests/test_verify_triage_one_call.py::test_one_triage_call_per_verify]
- AC2: no triage call is made when there is nothing to triage [evidence: test:plugins/workbench/scripts/tests/test_verify_triage_one_call.py::test_no_call_when_nothing_to_triage]
- AC3: a failed verify-mode call falls back with a note and empty results [evidence: test:plugins/workbench/scripts/tests/test_verify_triage_one_call.py::test_verify_mode_failure_falls_back_with_note]
- AC4: triage verify mode answers all three parts from one call [evidence: test:plugins/workbench/scripts/tests/test_triage.py::test_verify_mode_answers_all_three_parts]
- AC5: the existing triage and verify-task tests still pass [evidence: command:cd plugins/workbench && pytest scripts/tests/test_triage.py scripts/tests/test_triage_false_finding.py scripts/tests/test_verify_task.py -q]

#### Files

- `plugins/workbench/scripts/verify-task.py`
- `plugins/workbench/scripts/triage.py`
- `plugins/workbench/scripts/tests/test_triage.py`
- `plugins/workbench/scripts/tests/test_verify_triage_one_call.py`

#### Interfaces

- `triage.run("verify", data, ...)` in `plugins/workbench/scripts/triage.py`; verify-task's `triage_run` injection point (`build(argv, triage_run=...)`) stays the test seam.

#### Expected outcome

Each verify spends one haiku round trip instead of up to three, about a minute less per verify, with the same result fields.

#### Steps

- Red: write `scripts/tests/test_verify_triage_one_call.py` with a counting fake `triage_run` (AC1-AC3) and add AC4 to `test_triage.py` with a fake runner; run `cd plugins/workbench && pytest scripts/tests/test_verify_triage_one_call.py scripts/tests/test_triage.py -q`; expect failures.
- Green: the `verify` mode and the single call site in `build`.
- Run the task verify; expect all passed.

#### Notes

- Today `build` calls `triage_run` for `parking`, `ac-plausible` (through `add_plausibility`) and `tier`, each with a 120 s timeout (`lib/claude_json.py`).
- `add_plausibility` keeps its shortcut that answers obvious matches without a call; only the remaining items go into the combined call.

### S13: Cascade release

- Status: done
- Files: `plugins/workbench/workflows/plan-execute.js`, `plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs`
- Verify: `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`
- Verified head: bae1f364c7672d48a9c8d4e2826d3431f0902c83

#### Requirement

Release dependents of a task whose only open findings are medium (design D8). `plugins/workbench/workflows/plan-execute.js`.

- `mediumOnly(impl, findings)`: verified, not blocked, at least one open finding, and every open finding has severity `medium` and no `gate`.
- `released(d)` in `runTasks` is also true for a mediumOnly result, so its dependents start in this run. In an epic run the task lands on the epic branch like any released task (the land step).
- The mediumOnly task still escalates: it is listed in `escalated` with its reason and findings, its return entry carries `mediumOnly: true`, and its approval status stays `escalated` until a ruling; `finished` is unchanged.
- A high or critical finding, any gate finding, a blocked task or an unverified task never releases dependents through this rule.

#### Acceptance conditions

- AC1: a dependency verified with only medium findings releases its dependents in the same run [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs::medium-only-dependency-releases-dependents]
- AC2: the medium-only task still escalates and its return entry carries mediumOnly true [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs::medium-only-task-still-escalates-with-flag]
- AC3: a high or gate finding never releases dependents [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs::high-or-gate-finding-never-releases]
- AC4: an unverified or blocked task with medium findings never releases [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs::unverified-medium-only-never-releases]
- AC5: in an epic run a medium-only task releases its dependents and is not landed until a ruling accepts it (D8 as amended 2026-10-22, delivered by medium-only-hold) [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs::medium-only-task-releases-but-does-not-land-in-epic-run]
- AC6: the existing release tests still pass [evidence: command:cd plugins/workbench && node --test workflows/tests/plan-execute-triage-release.test.mjs workflows/tests/plan-execute-process-only.test.mjs]

#### Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs`

#### Interfaces

- Uses `land-step` (epic integration worktrees): a released task is landed before its dependents begin.
- Return task field `mediumOnly` (boolean), next to `processOnly` and `triageRejected`.

#### Expected outcome

One medium finding at the top of the DAG no longer fails every dependent: the run continues and the orchestrator rules on the finding afterwards.

#### Steps

- Red: write `workflows/tests/plan-execute-medium-release.test.mjs` with AC1-AC5; run `cd plugins/workbench && node --test workflows/tests/plan-execute-medium-release.test.mjs`; expect failures.
- Green: `mediumOnly`, the `released` rule, the return field.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`; expect all green.

#### Notes

- Measured: 19 root escalations caused 183 dependency-failed task-runs; runs 2 and 3 each ran one task and blocked 61 and 60 (brief failure mode 2).
- Severity enum is `critical`, `high`, `medium` (the review schema in plan-execute.js); every script-made gate finding is `high` and carries `gate`.
- A dependent built on a later-fixed dependency is handled by the blocker's forward-merge via the epic branch and its re-verify.

### S14: Audit context and models

- Status: done
- Files: `plugins/workbench/workflows/plan-execute.js`, `plugins/workbench/skills/start-development/scripts/ticket_cmds/args.py`, `plugins/workbench/skills/start-development/tests/test_ticket_args.py`, `plugins/workbench/agents/scope-auditor.md`, `plugins/workbench/workflows/tests/plan-execute-audit-context.test.mjs`, `plugins/workbench/workflows/tests/plan-execute-epic-audit.test.mjs`
- Verify: `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_args.py -q && ruff check skills && bash scripts/run-tests.sh --only workflows`
- Verified head: f26be92333627e003c2aa0514252c6630d7e9dc0

#### Requirement

Give the audit task files instead of inlined requirements and move mechanical roles to haiku (design D11, D12).

- `ticket_cmds/args.py`: every task entry gets `taskFile`, the absolute path of its task file.
- `auditPrompt` and `epicAuditPrompt` in plan-execute.js: when every task has `taskFile`, list per task `- <id>: <title> | tree <worktree> | task file <taskFile>` with the instruction to read each task file's `## Requirement` and `## Acceptance conditions` sections, and inline no requirement text (PLAN_TEXT and the ledger stay). Without `taskFile` the prompts are unchanged. For a 21-task fixture with 900-character requirements the sonnet epic audit prompt is under 10,000 characters.
- Audit split: AC table rows the verifier settled (every AC of the task met with test, symbol, command or doc-section evidence, none with `matchedBy: substring`, the task not in `acsForAudit`) go to one haiku scope-auditor call (`model: 'haiku'`, label `<name>:audit:settled`) that only confirms each row's evidence exists at the landed head. Every other row, the ledger, the ancestry pairs and the duplicate sweep go to the sonnet call. Both results merge (missing lists concatenated, `complete` true only when both are) before `splitAudit`. With no settled rows no haiku call is made.
- `forwardMerge`'s merge agent runs on `model: 'haiku'`.
- The land agent runs on `model: 'haiku'`; a land result that reports a conflict is re-dispatched once on `model: 'sonnet'` before the task ends `land-failed`.
- `plugins/workbench/agents/scope-auditor.md`: a `## Reading task files` section (read the named sections of each task file, never the whole tree of docs) and the settled-rows mode.
- Existing audit tests are updated where they pinned the inlined requirement.

#### Acceptance conditions

- AC1: args task entries carry their absolute taskFile path [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_args.py::test_args_tasks_carry_task_file]
- AC2: the epic audit prompt for a 21-task fixture is under 10000 characters [evidence: test:plugins/workbench/workflows/tests/plan-execute-audit-context.test.mjs::epic-audit-prompt-under-10k-for-21-tasks]
- AC3: with task files the audit prompts name the files and inline no requirement [evidence: test:plugins/workbench/workflows/tests/plan-execute-audit-context.test.mjs::audit-reads-task-files-not-inlined-requirements]
- AC4: verifier-settled rows go to one haiku audit call and the rest to sonnet, merged before splitAudit [evidence: test:plugins/workbench/workflows/tests/plan-execute-audit-context.test.mjs::settled-rows-go-to-one-haiku-audit]
- AC5: the forward-merge agent runs on haiku [evidence: test:plugins/workbench/workflows/tests/plan-execute-audit-context.test.mjs::forward-merge-runs-on-haiku]
- AC6: the land agent runs on haiku and a conflict is retried once on sonnet [evidence: test:plugins/workbench/workflows/tests/plan-execute-audit-context.test.mjs::land-runs-on-haiku-and-retries-conflict-on-sonnet]
- AC7: the scope auditor documents reading task files [evidence: doc-section:plugins/workbench/agents/scope-auditor.md#Reading task files]

#### Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/args.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_args.py`
- `plugins/workbench/agents/scope-auditor.md`
- `plugins/workbench/workflows/tests/plan-execute-audit-context.test.mjs`
- `plugins/workbench/workflows/tests/plan-execute-epic-audit.test.mjs`

#### Interfaces

- Uses `ac-evidence` (ac-evidence-map): `matchedBy` per AC decides a settled row.
- Uses `land-step` (epic integration worktrees): the land agent dispatch whose model changes.
- Uses `epic-run-args` (epic integration worktrees): `build_args` in `ticket_cmds/args.py`, which gains `taskFile`.

#### Expected outcome

The epic audit reads a short prompt and the task files it needs, the mechanical checks run on haiku, and review and judgement rows stay on sonnet.

#### Steps

- Red: write `workflows/tests/plan-execute-audit-context.test.mjs` (AC2-AC6) and add AC1 to `skills/start-development/tests/test_ticket_args.py`; run both; expect failures.
- Green: `taskFile` in args.py, the audit prompts and split, the two model changes, the scope-auditor section; update `plan-execute-epic-audit.test.mjs`.
- Run the task verify; expect all green.

#### Notes

- Measured: one epic audit was 7.5M raw tokens with every requirement inlined (brief item 10).
- `acTable()` already marks rows `verifier settled` or `open: judge it`; reuse that split.
- args.py and the land step were changed by epic integration worktrees; read the landed code first.

### S15: Flow docs update

- Status: done
- Files: `plugins/workbench/skills/start-development/references/task-fields.md`, `plugins/workbench/skills/start-development/references/tickets.md`, `plugins/workbench/skills/start-development/references/run-handback.md`, `plugins/workbench/skills/start-development/references/phase-4-execute.md`, `plugins/workbench/skills/start-development/SKILL.md`, `plugins/workbench/skills/start-development/templates/epic.md`, `plugins/workbench/skills/start-development/templates/record.md`, `plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py`
- Verify: `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_flow_docs.py skills/start-development/tests/test_skill_size.py skills/start-development/tests/test_templates.py skills/start-development/tests/test_start_development_generic.py skills/start-development/tests/test_flow_references_remarks.py -q`
- Verified head: cdc932494d88d916a5632a42e06af2454233e5c9

#### Requirement

Document the new estimates, actuals, relaunch and release rules in the flow references (design D3, D4, D5, D8, D9).

- `references/task-fields.md`: the `estimate` row (formula minutes from `scripts/lib/estimator.json` written by `ticket.py estimate`, `estimate_by: formula|override`, report only); the `actual` row (agent-minutes stamped from the run dir by `apply-run --run-dir` and `continue --run`, because the Workflow runtime gives scripts no clock; remove the `Date.now()` claim) and `actual_roles`; the `verify` row (targeted, a full-suite verify fails the lint on a todo task); the `review` row (doc-only and test-only skip, scoped re-review of light-tier fixes).
- `references/tickets.md`: the `estimate` subcommand, `continue --launch` (auto-accept, self-landing, `LAUNCH` and `ARM` lines) and the new Time line.
- `references/run-handback.md`: the heartbeat wakes on END and STALL; on END run `ticket.py continue <epic> --run <id> --out-dir <dir> --launch`, then the one Workflow call from the `LAUNCH` line and the one Monitor from the `ARM` line; auto-accepted processOnly and triageRejected tasks are not judged again; mediumOnly escalations are ruled like any escalation, their dependents already ran.
- `references/phase-4-execute.md`: the release rule (clean, processOnly, triageRejected, mediumOnly, ruled accept) and the relaunch scope (never a done task).
- `skills/start-development/SKILL.md`: gate item 3 shows the epic estimate line from `ticket.py estimate <epic>` and the three longest-path tasks; phase 4 relaunch names `continue --launch`. SKILL.md stays inside its size test.
- `templates/epic.md` Time section names the new line; `templates/record.md` puts `actual_roles` in the estimate-versus-actual table.
- `tests/test_ticket_flow_docs.py` pins each of the above.

#### Acceptance conditions

- AC1: task-fields documents formula estimates and run-dir actuals and no longer claims Date.now [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_task_fields_document_formula_estimates_and_run_dir_actuals]
- AC2: tickets.md documents estimate and continue --launch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_tickets_reference_documents_estimate_and_continue_launch]
- AC3: run-handback covers END with continue --launch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_run_handback_is_end_only_with_continue_launch]
- AC4: phase-4-execute documents the medium-only release and the relaunch scope [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_phase4_documents_medium_only_release_and_relaunch_scope]
- AC5: the gate shows the epic estimate line [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_gate_shows_epic_estimate_line]
- AC6: the skill size, template and generic doc tests still pass [evidence: command:cd plugins/workbench && pytest skills/start-development/tests/test_skill_size.py skills/start-development/tests/test_templates.py skills/start-development/tests/test_start_development_generic.py skills/start-development/tests/test_flow_references_remarks.py -q]

#### Files

- `plugins/workbench/skills/start-development/references/task-fields.md`
- `plugins/workbench/skills/start-development/references/tickets.md`
- `plugins/workbench/skills/start-development/references/run-handback.md`
- `plugins/workbench/skills/start-development/references/phase-4-execute.md`
- `plugins/workbench/skills/start-development/SKILL.md`
- `plugins/workbench/skills/start-development/templates/epic.md`
- `plugins/workbench/skills/start-development/templates/record.md`
- `plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py`

#### Interfaces

- Uses `epic-time-line` (estimate-and-actuals) and `continue-launch-lines` (continue-launch): the docs quote their exact line formats.

#### Expected outcome

An orchestrator reading the references runs the one-command relaunch, shows the epic estimate at the gate, and knows which escalations need a ruling.

#### Steps

- Red: add AC1-AC5 to `skills/start-development/tests/test_ticket_flow_docs.py`; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_flow_docs.py -q`; expect failures.
- Green: edit the seven docs.
- Run the task verify; expect all passed.

#### Notes

- SKILL.md, run-handback.md, phase-4-execute.md and tickets.md were rewritten by epic integration worktrees (docs-flow-phases, docs-worktree-refs); edit the landed text.
- Quote the line formats from the landed estimate.py and continue_cmd.py, not from this task.
- Docs only plus a doc test: the red step is the doc test.

### S16: Cache prefix change

- Status: done
- Files: `plugins/workbench/workflows/plan-execute.js`, `plugins/workbench/workflows/tests/plan-execute-prompt-prefix.test.mjs`, `MEMORY.md`
- Verify: `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`
- Verified head: 0894fff7e69ea51fbcad51628ed425bb531f0465

#### Requirement

Apply or decline the prompt-cache change according to the recorded probe (design D6).

- Precondition: design.md (the run's `designDoc`) has a `## Cache probe result` section with the probe JSON and a verdict line. If it is absent, return `blocked` with reason `cache probe not run` and whoCanClear `orchestrator: run hook-probe.js with args.probe cache, then hook-evidence.py --cache, and record the result in design.md`.
- Verdict `CACHE saving`: reorder `implPrompt` and `verifyPrompt` static-first like `reviewPrompt`: every block identical across tasks first, then a task marker line, then the task-specific lines (worktree, repo, task id, requirement, files, notes, ACs, dependencies). The test pins that the prompts of two different tasks are byte-identical up to the marker and that no line before it names a task.
- Verdict `CACHE none`: change no prompt. The test pins the current order (implPrompt's first line is the worktree line), so a later reorder is a deliberate decision.
- Either way, root `MEMORY.md` gets a dated entry headed `prompt-cache probe` with the measured creation and read numbers per agent, the verdict and the decision taken.

#### Acceptance conditions

- AC1: MEMORY.md records the probe numbers, the verdict and the decision [evidence: command:grep -q 'prompt-cache probe' MEMORY.md]
- AC2: a test pins the prompt order the verdict chose [evidence: test:plugins/workbench/workflows/tests/plan-execute-prompt-prefix.test.mjs::prompt-order-follows-probe-verdict]
- AC3: the prompt change, or its absence, matches the recorded verdict [evidence: judgement:]
- AC4: the workflows suite is green [evidence: command:cd plugins/workbench && bash scripts/run-tests.sh --only workflows]

#### Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-prompt-prefix.test.mjs`
- `MEMORY.md`

#### Interfaces

- Uses `cache-probe-verdict` (cache-probe), as recorded by the orchestrator in design.md `## Cache probe result`.
- `implPrompt(t)` and `verifyPrompt(t, impl, prev)` in plan-execute.js keep their signatures.

#### Expected outcome

The cache lever ships only when measured to save writes; otherwise the measurement and the no-op are on record and pinned.

#### Steps

- Red: read the verdict; write `workflows/tests/plan-execute-prompt-prefix.test.mjs::prompt-order-follows-probe-verdict` for that verdict; run `cd plugins/workbench && node --test workflows/tests/plan-execute-prompt-prefix.test.mjs`; on `saving` expect a failure, on `none` it passes at once (the test pins existing behaviour; say so in `tests.note`).
- Green on `saving`: reorder both prompts. On `none`: no code change.
- Add the MEMORY.md entry; run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`; expect all green.

#### Ruling

- 2026-10-22 accepted: run 2: cache-prefix-change (CACHE none, recorded no-op, pinning test) landed on main at e7533b8; TDD-skipped accepted: no behaviour change. Phase 5 remediation tasks follow.

#### Notes

- The brief estimated -25% to -30% workflow cache-weighted tokens if 60% of each 17-28k prefix became a read; that estimate is the hypothesis the probe tests.
- Workflow agents start in the main conversation's cwd; the probe's `cwd` column confirms it, so no launch option changes.
- On `none` this task is a pinned no-op plus the record; that is the delivery D6 approves.

### S17: Full suite split shared

- Status: done
- Files: `plugins/workbench/workflows/validate-tasks.mjs`, `plugins/workbench/scripts/lib/estimator.py`, `plugins/workbench/scripts/lib/estimator.json`, `plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs`, `plugins/workbench/scripts/tests/test_estimator.py`
- Verify: `cd plugins/workbench && pytest scripts/tests/test_estimator.py -q && node --test workflows/tests/validate-tasks-sizing.test.mjs && ruff check scripts`
- Verified head: 7937ba8d97fa0c985fafd67ce0b116534273578a

#### Requirement

Epic review finding (2026-10-22): D13 says the full-suite predicate has no second copy, but the command splitting is implemented twice and differently: estimator.py:29-39 splits on `&&` and `;` and skips every `cd` part; validate-tasks.mjs:346-351 splits only on `&&` and skips only a leading `cd`. So `a; mise run test` is full-suite for the estimator and passes the lint.

Deliver: both classify a command the same way: split on `&&`, `||` and `;`, skip every part that is a `cd` command, and call the command full-suite when any remaining part matches `fullSuitePatterns` or equals one of the repo's suites. estimator.json gains `fullSuiteExamples`, a list of `{command, full}` pairs covering at least: `mise run test` (full), `cd plugins/x && mise run test` (full), `a; mise run test` (full), `true || mise run test` (full), `cd x; pytest -q tests/test_a.py` (not full), `pytest -q` (full), `bash scripts/run-tests.sh --only workflows` (not full). Both the python and the node test suites assert every example, so a future divergence fails a test.

#### Acceptance conditions

- AC1: estimator.py classifies every fullSuiteExamples entry as listed [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_full_suite_examples]
- AC2: validate-tasks.mjs classifies every fullSuiteExamples entry as listed [evidence: test:plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs]
- AC3: a todo task verifying with `a; mise run test` fails the plan lint [evidence: test:plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs]

#### Files

- `plugins/workbench/workflows/validate-tasks.mjs`
- `plugins/workbench/scripts/lib/estimator.py`
- `plugins/workbench/scripts/lib/estimator.json`
- `plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs`
- `plugins/workbench/scripts/tests/test_estimator.py`

#### Interfaces

- `estimator.json`: new key `fullSuiteExamples: [{command, full}]`; `fullSuitePatterns` unchanged.
- `estimator.full_suite(cmd, suites)` and the validate-tasks.mjs predicate keep their signatures.

#### Expected outcome

One splitting rule in two languages, pinned by one shared example list.

#### Steps

1. Add fullSuiteExamples and the two tests; see the node side fail on the `;` and `||` examples.
2. Align the node splitter (and the python one for `||`).
3. Run the verify command.

#### Ruling

- 2026-10-22 accepted: run 3: verify-shared-deadline, launch-land-verify, full-suite-split-shared and shell-quote-refs verified clean (landing on main via c2-land). medium-only-hold rejected for one fix round: transitive hold through a chain.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S18: Launch land verify

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py`, `plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py`
- Verify: `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_continue_launch.py -q && ruff check skills`
- Verified head: 560074c9936fc356abc5ae8091fa3c6bede921f8

#### Requirement

Epic review finding (2026-10-22): continue_cmd.py:157 passes `--verify`, `m.get("verify") or "true"` to merge.py, so a task with no `verify` field (allowed by D1, targeted verify) lands on the epic branch with no check.

Deliver: `ticket.py continue --launch` never passes `true` as the landing verify. A task with a `verify` field lands with it, as today. A task without one lands with the verified command recorded for it in the run return (`tasks[].verification.command`, the command plan-execute's landVerify uses). When neither exists, the task is not landed by continue: its `MERGE` line is printed for the worktree-merger, as for a failed landing.

#### Acceptance conditions

- AC1: a task without verify whose run return records verification.command lands with that command [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_launch_lands_with_recorded_verification_command]
- AC2: a task with neither verify nor a recorded command is not landed and its MERGE line is printed [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_launch_without_any_verify_prints_merge]
- AC3: a task with verify still lands with its own verify [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_launch_uses_task_verify]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py`

#### Interfaces

- `continue_cmd._land` takes the run return's per-task verification command into account; its output lines (`<task>: landed`, `MERGE ...`) keep their format.

#### Expected outcome

Every landing that continue --launch performs runs a real verify command; tasks it cannot verify go to the worktree-merger.

#### Steps

1. Write the three tests and see AC1 and AC2 fail.
2. Thread the run return's verification.command into _land; print MERGE when there is no command.
3. Run the verify command.

#### Ruling

- 2026-10-22 accepted: run 3: verify-shared-deadline, launch-land-verify, full-suite-split-shared and shell-quote-refs verified clean (landing on main via c2-land). medium-only-hold rejected for one fix round: transitive hold through a chain.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S19: Verify shared deadline

- Status: done
- Files: `plugins/workbench/scripts/verify-task.py`, `plugins/workbench/scripts/tests/test_verify_bounded.py`, `plugins/workbench/agents/verifier.md`, `plugins/workbench/workflows/plan-execute.js`
- Verify: `cd plugins/workbench && pytest scripts/tests/test_verify_bounded.py -q && ruff check scripts`
- Verified head: cc58bb40abfa3b3357b353a66a33926094e99848

#### Requirement

Epic review finding (2026-10-22): verify-task.py gives each command its own 480 s timeout (verify-task.py:49, :801-806, :863, :889, :921), but the design's builder check answer says `--timeout` is ONE shared deadline (default 540 s) across every command a single call runs, so two runs plus triage finish inside the verifier's 600 s Bash call.

Deliver: `--timeout` is one shared deadline, default 540 s, measured from the start of the call, across the main verify run, every AC ref run, the tdd-revert base run and triage. Each command runs with the time remaining; when the deadline is reached the running command's process group is killed, the result carries `timeout: {command, seconds}` and `passed: false`, and every step not yet run is skipped and listed in a `skipped` array in the JSON. The `--timeout` help text, agents/verifier.md and the plan-execute.js comment next to the 600000 ms Bash timeout describe the shared deadline.

#### Acceptance conditions

- AC1: with --timeout 3, a main command sleeping 2 s and a tdd-revert base run sleeping 2 s, the call returns in under 4 s with timeout set and passed false [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_shared_deadline_spans_main_and_tdd_runs]
- AC2: steps not run before the deadline are listed in skipped [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_steps_after_deadline_are_skipped]
- AC3: the default deadline is 540 s and the help text calls it a shared deadline [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_default_shared_deadline_is_540]

#### Files

- `plugins/workbench/scripts/verify-task.py`
- `plugins/workbench/scripts/tests/test_verify_bounded.py`
- `plugins/workbench/agents/verifier.md`
- `plugins/workbench/workflows/plan-execute.js`

#### Interfaces

- `verify-task.py --timeout <seconds>`: shared deadline, default 540.
- Result JSON: `timeout: {command, seconds}` (existing) plus `skipped: [step names]` (new, empty list when nothing was skipped).

#### Expected outcome

One verify-task.py call never runs longer than its --timeout in total, so the verifier's 600 s Bash call always returns a JSON result.

#### Steps

1. Write the three tests in test_verify_bounded.py and see them fail.
2. Replace per-command timeouts with a deadline computed once; pass the remaining seconds to each command.
3. Record skipped steps; update help text, verifier.md and the plan-execute.js comment.
4. Run the verify command.

#### Ruling

- 2026-10-22 accepted: run 3: verify-shared-deadline, launch-land-verify, full-suite-split-shared and shell-quote-refs verified clean (landing on main via c2-land). medium-only-hold rejected for one fix round: transitive hold through a chain.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S20: Shell quote refs

- Status: done
- Files: `plugins/workbench/workflows/plan-execute.js`, `plugins/workbench/workflows/tests/plan-execute-shell-quoting.test.mjs`
- Verify: `cd plugins/workbench && node --test workflows/tests/plan-execute-shell-quoting.test.mjs && bash scripts/run-tests.sh --only workflows`
- Verified head: 4409cc7a71bfda4e014a3fb013684d7ca497ba5f

#### Requirement

Security review finding (2026-10-22, MEDIUM and LOW): plan-execute.js builds verifier shell commands with values that are neither quoted nor validated: `diffBase(t)` returns `forkPointOf(t) || BASE_REF` and is embedded raw as `--base ${diffBase(t, true)}` (plan-execute.js:127, verifyTaskCommand :1119, forward-merge :2607); `forkPoint` comes from ARGS.tasks[].forkPoint (fed from an earlier run's landed return) and BASE_REF from ARGS.baseRef. repoDir (:845-848) embeds t.worktree and t.repo inside double quotes, where `$` and backticks expand.

Deliver: a forkPoint that does not match SHA_RE is ignored (the base ref is used and the run logs `forkPoint ignored: not a sha`); every diffBase value placed in a shell command goes through shq; repoDir quotes the worktree and repo with shq instead of double quotes. Existing prompt text otherwise unchanged.

#### Acceptance conditions

- AC1: a task whose forkPoint is `abc; touch pwned` gets a verify command that uses the quoted base ref and contains no `touch pwned` [evidence: test:plugins/workbench/workflows/tests/plan-execute-shell-quoting.test.mjs]
- AC2: a baseRef containing a space and `$(x)` appears single-quoted in the verify and forward-merge commands [evidence: test:plugins/workbench/workflows/tests/plan-execute-shell-quoting.test.mjs]
- AC3: repoDir output single-quotes a worktree path containing `$HOME` and a backtick [evidence: test:plugins/workbench/workflows/tests/plan-execute-shell-quoting.test.mjs]

#### Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-shell-quoting.test.mjs`

#### Interfaces

- `shq` and `SHA_RE` in plan-execute.js are reused, not redefined.
- `diffBase(t, quoted)` keeps its call sites; quoting happens where the value enters a shell string.

#### Expected outcome

Hostile or malformed refs and paths in args or run data cannot execute in a verifier's shell.

#### Steps

1. Write plan-execute-shell-quoting.test.mjs and see it fail.
2. Validate forkPoint with SHA_RE; shq the base in the three command builders; shq in repoDir.
3. Run the verify command.

#### Ruling

- 2026-10-22 accepted: run 3: verify-shared-deadline, launch-land-verify, full-suite-split-shared and shell-quote-refs verified clean (landing on main via c2-land). medium-only-hold rejected for one fix round: transitive hold through a chain.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S21: Medium only hold

- Status: done
- Files: `plugins/workbench/workflows/plan-execute.js`, `plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs`
- Verify: `cd plugins/workbench && node --test workflows/tests/plan-execute-medium-release.test.mjs && bash scripts/run-tests.sh --only workflows`
- Verified head: 6fe6d7ba001735aa25a4bf1aa9d8f55d1b9d9931

#### Requirement

Epic review finding (2026-10-22): the design's builder check answer says a task released as mediumOnly releases its dependents but does not land on the epic branch until the orchestrator rules; D8's text and the code (plan-execute.js:2249-2252 releasable includes mediumOnly, the landing queue lands every releasable task; :2824-2826) land it. Ruling (orchestrator, 2026-10-22): the builder check answer wins; D8 is amended to match.

Deliver: a mediumOnly task releases its dependents (they merge its task branch, as today) and is NOT landed in-run: it is not queued for landing, the return keeps `mediumOnly: true` and escalates it for a ruling, and it is not reported as landed. A mediumOnly task that is in RULED_ACCEPT lands like any released task.

#### Acceptance conditions

- AC1: a mediumOnly task in a landing run starts its dependents and is not landed [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs]
- AC2: a mediumOnly task listed in ruled-accept lands [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs]
- AC3: the return marks the unlanded mediumOnly task escalated with mediumOnly true [evidence: test:plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs]

#### Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-medium-release.test.mjs`

#### Interfaces

- `releasable(d)` keeps releasing dependents for mediumOnly; landing eligibility excludes mediumOnly unless RULED_ACCEPT has it.

#### Expected outcome

Medium findings never reach the epic branch unruled, while the run still continues past them.

#### Steps

1. Add the AC tests and see AC1 fail.
2. Split release from landing eligibility for mediumOnly.
3. Run the verify command.

#### Ruling

- 2026-10-22 rejected: Fix round (orchestrator, 2026-10-22). The parking flags at plan-execute.js:859,869,2228,2257,2258 are dismissed: they describe current behaviour. One real high finding to fix: mediumHeldDep (plan-execute.js:871-875) checks only the dependency's own mediumOnly flag. In a chain a(held mediumOnly) -> b(clean, released via behindHeld, unlanded) -> c, c is told to merge the epic branch carrying landed b, but neither a nor b is on it, so c builds without b's code. mergedDependencyBranches (:889) has the same gap. Make the hold transitive: a dependency counts as held when it, or any dependency it was released behind, is held and unlanded. A dependent then merges the task branches of every such unlanded ancestor and never relies on the epic branch for them. Add a test for the two-deep chain a -> b -> c, plus a three-deep one if cheap. Keep the existing seven medium-release tests green.

- 2026-10-22 accepted: Accepted 2026-10-22: verified (9/9 medium-release tests incl. transitive chains, workflows 571); open flags are parking-wording false positives on behaviour-describing comments. Landed on main.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none

## Rulings (migrated)

- cache-prefix-change: accept true, at 2026-10-22T07:00:06Z: run 2: cache-prefix-change (CACHE none, recorded no-op, pinning test) landed on main at e7533b8; TDD-skipped accepted: no behaviour change. Phase 5 remediation tasks follow.
- medium-only-hold: accept false, at 2026-10-22T07:36:35Z: Fix round (orchestrator, 2026-10-22). The parking flags at plan-execute.js:859,869,2228,2257,2258 are dismissed: they describe current behaviour. One real high finding to fix: mediumHeldDep (plan-execute.js:871-875) checks only the dependency's own mediumOnly flag. In a chain a(held mediumOnly) -> b(clean, released via behindHeld, unlanded) -> c, c is told to merge the epic branch carrying landed b, but neither a nor b is on it, so c builds without b's code. mergedDependencyBranches (:889) has the same gap. Make the hold transitive: a dependency counts as held when it, or any dependency it was released behind, is held and unlanded. A dependent then merges the task branches of every such unlanded ancestor and never relies on the epic branch for them. Add a test for the two-deep chain a -> b -> c, plus a three-deep one if cheap. Keep the existing seven medium-release tests green.
- verify-shared-deadline: accept true, at 2026-10-22T07:36:35Z: run 3: verify-shared-deadline, launch-land-verify, full-suite-split-shared and shell-quote-refs verified clean (landing on main via c2-land). medium-only-hold rejected for one fix round: transitive hold through a chain.
- launch-land-verify: accept true, at 2026-10-22T07:36:35Z: run 3: verify-shared-deadline, launch-land-verify, full-suite-split-shared and shell-quote-refs verified clean (landing on main via c2-land). medium-only-hold rejected for one fix round: transitive hold through a chain.
- full-suite-split-shared: accept true, at 2026-10-22T07:36:35Z: run 3: verify-shared-deadline, launch-land-verify, full-suite-split-shared and shell-quote-refs verified clean (landing on main via c2-land). medium-only-hold rejected for one fix round: transitive hold through a chain.
- shell-quote-refs: accept true, at 2026-10-22T07:36:35Z: run 3: verify-shared-deadline, launch-land-verify, full-suite-split-shared and shell-quote-refs verified clean (landing on main via c2-land). medium-only-hold rejected for one fix round: transitive hold through a chain.
- medium-only-hold: accept true, at 2026-10-22T07:56:27Z: Accepted 2026-10-22: verified (9/9 medium-release tests incl. transitive chains, workflows 571); open flags are parking-wording false positives on behaviour-describing comments. Landed on main.
