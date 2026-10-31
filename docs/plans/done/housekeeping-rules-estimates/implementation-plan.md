# Housekeeping rules, estimates and retrospectives implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: Calibration lib

- Status: done
- Files: `plugins/workbench/scripts/lib/calibration.py`, `plugins/workbench/scripts/tests/test_calibration.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: 297bdf4

#### Requirement

User requirement (U4, verbatim): "scripting support getting deltas between complexity/time of delivery/tokens usage per task. New tools are meant to make the estimates more precise with time. Task table will be used for future estimates, retro table will be used to propose improvements for future work (also including workflow improvements). It must be seamless for the agent (taking over most of the estimation from agent's reasoning)."

Design D8: a stdlib module `plugins/workbench/scripts/lib/calibration.py` restores `_solve`, `refit` and `mdape` from `git show 7b187e8^:plugins/workbench/scripts/lib/estimator.py`, with storypoints as the regressor. `POINTS = (1, 2, 3, 5, 8, 13)`. Rows are plain dicts (`points`, `actual_minutes`, `actual_tokens`, optionally `expected_minutes`, `expected_tokens`, `points_actual`) as ints; rows missing points or either actual are ignored. `expected(points, rows) -> (minutes, tokens)`: the median of rows with that `points` when there are at least 3; else the least-squares line over all usable rows evaluated at `points` (rounded, at least 1) when there are at least 5; else the seed table. `bucket_table(rows)` returns, per points value, `minutes`, `tokens`, `n` and `source` (`history`, `refit` or `seed`). Design D15: the seed table is `SEED = {1: (11, 750000), 2: (23, 1500000), 3: (34, 2250000), 5: (57, 3750000), 8: (91, 6000000), 13: (147, 9750000)}` (probe of this machine's transcripts, a median task taken as 3 points, scaled linearly), unless the gate answer to Q2 changes it. The module name must not contain "estimator" (retirement pin).

#### Acceptance conditions

- AC1: `_solve`, `refit` and `mdape` reproduce the restored behaviour: an exact line is recovered, a singular system returns None, MdAPE of known pairs matches, zero actuals are skipped [evidence: test:plugins/workbench/scripts/tests/test_calibration.py::test_refit_and_mdape]
- AC2: with 3 or more rows for a points value, `expected` returns their median minutes and tokens [evidence: test:plugins/workbench/scripts/tests/test_calibration.py::test_expected_uses_bucket_median]
- AC3: with fewer than 3 rows in the bucket and 5 or more usable rows, `expected` uses the refit line, rounded and at least 1 [evidence: test:plugins/workbench/scripts/tests/test_calibration.py::test_expected_falls_back_to_refit]
- AC4: with fewer than 5 usable rows, `expected` returns the seed values, and SEED equals the D15 table [evidence: test:plugins/workbench/scripts/tests/test_calibration.py::test_expected_falls_back_to_seed]
- AC5: `bucket_table` reports minutes, tokens, n and source for every points value; rows with missing or non-integer fields are ignored [evidence: test:plugins/workbench/scripts/tests/test_calibration.py::test_bucket_table_sources]
- AC6: no tracked file name contains "estimator" and the retirement pins hold [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py::test_run_loop_commands_retired]
- AC7: scripts and start-development suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

#### Files

- `plugins/workbench/scripts/lib/calibration.py`
- `plugins/workbench/scripts/tests/test_calibration.py`

#### Interfaces

- `calibration.POINTS: tuple[int, ...]`, `calibration.SEED: dict[int, tuple[int, int]]`
- `calibration._solve(a, b)`, `calibration.refit(rows, target: str) -> tuple[float, float] | None` (intercept, slope over `points`), `calibration.mdape(pairs) -> float | None`
- `calibration.expected(points: int, rows: list[dict]) -> tuple[int, int]`
- `calibration.bucket_table(rows: list[dict]) -> dict[int, dict]` with keys `minutes`, `tokens`, `n`, `source`
- Constants `MIN_BUCKET = 3`, `MIN_REFIT = 5`.

#### Expected outcome

One stdlib module turns done-task actuals into expected minutes and tokens per storypoint, used by new-task (estimate-fields) and the deltas report (deltas-command).

#### Steps

1. List the files under Files and read `git show 7b187e8^:plugins/workbench/scripts/lib/estimator.py` in one pass; write test_calibration.py and run `pytest scripts/tests/test_calibration.py -q` from plugins/workbench: it fails on the missing module.
2. Implement; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 5 points.
- Reuse (brief): restore estimator.py `_solve`, `refit`, `mdape` as logic; drop `task_minutes`, `epic_estimate` and parallelism (retired Time line); `rows_from_plans` is replaced by ticket.py collecting rows (no import of ticket.py here, ticket.py imports this module).
- Do-not-build: a new regression solver.
- Fix-as-ac (brief, retirement pins): test_ticket_retired_run_loop.py fails on any tracked file under scripts/lib with "estimator" in its name; this module is `calibration.py`.
- Legacy done tasks carry `estimate`/`actual` in minutes with no points; they are not rows here (deltas-command reads them as minutes-only rows).
- Python 3.9 safe (`from __future__ import annotations`): the agent-usage hook path may import scripts/lib modules.

- 2026-10-24 done

- 2026-10-25 done

### S2: Em dash lint

- Status: done
- Files: `scripts/check_em_dash.py`, `mise-tasks/lint/em-dash`, `scripts/tests/test_check_em_dash.py`, `scripts/tests/test_agents_md.py`
- Verify: `mise run test:scripts && mise run lint`
- Verified head: a2950c7

#### Requirement

User requirement (U1, verbatim): "no em dash characters in any code, comment, commit, message, or content of any kind".

Design D3: a thin entry point `scripts/check_em_dash.py` over `scripts/check_personal.py`'s `_tracked` and `_text` helpers reports `path:line` for every U+2014 in any tracked text file of the repo, with no allow list and no exempt path, and exits 1 on any hit, else 0. `mise-tasks/lint/em-dash` (executable, `#MISE description=...`) runs it, so `mise run lint` picks it up through `lint:*`. The one tracked literal today, in `scripts/tests/test_agents_md.py` (`test_no_personal_or_stale_content`, the banned tuple), becomes the escape `"\u2014"` so the tree passes. Binary files and untracked files are skipped, exactly as check_personal does.

#### Acceptance conditions

- AC1: a tracked file containing U+2014 is reported as `path:line` and the checker exits 1; a clean repo exits 0 [evidence: test:scripts/tests/test_check_em_dash.py::test_reports_tracked_em_dash]
- AC2: untracked files and binary files (a NUL in the first 8192 bytes) are not reported [evidence: test:scripts/tests/test_check_em_dash.py::test_ignores_untracked_and_binary]
- AC3: no path is exempt: a hit under `docs/plans/` and under `scripts/init_engine/` is reported [evidence: test:scripts/tests/test_check_em_dash.py::test_no_path_is_exempt]
- AC4: `mise-tasks/lint/em-dash` is executable and runs the checker against the repo root [evidence: test:scripts/tests/test_check_em_dash.py::test_lint_task_runs_checker]
- AC5: the tree is clean: `python3 scripts/check_em_dash.py` exits 0 [evidence: command:python3 scripts/check_em_dash.py]
- AC6: test_agents_md.py still bans the em dash in AGENTS.md, now written as an escape [evidence: test:scripts/tests/test_agents_md.py::test_no_personal_or_stale_content]
- AC7: `mise run lint` passes with the new task included [evidence: command:mise run lint]

#### Files

- `scripts/check_em_dash.py`
- `mise-tasks/lint/em-dash`
- `scripts/tests/test_check_em_dash.py`
- `scripts/tests/test_agents_md.py`

#### Interfaces

- `scripts/check_em_dash.py`: `scan(root: Path) -> list[str]` (hits as `path:line: em dash`), `main() -> int`, `--root DIR` like check_personal.
- Reuses `scripts/check_personal.py:_tracked` and `:_text`; no new walker.

#### Expected outcome

`mise run lint` fails on any tracked U+2014 anywhere in the repo and passes on the current tree.

#### Steps

1. List every file under Files, read them all in one pass (and check_personal.py), then write test_check_em_dash.py with a temp git repo fixture; run `pytest scripts/tests/test_check_em_dash.py -q` and watch it fail on the missing module.
2. Add check_em_dash.py and mise-tasks/lint/em-dash; replace the literal in test_agents_md.py with `"\u2014"`; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 2 points.
- Reuse (brief): check_personal.py `_tracked` (82), `_text` (89), `scan` (106) - import them, do not copy. Do-not-build: a new tracked-file walker.
- Rejected: a denylist entry in personal-denylist.json (its whole-file allows would exempt docs/plans/** and init_engine).
- Fix-as-ac: the literal em dash at scripts/tests/test_agents_md.py:107 is the only tracked hit (AC5, AC6).
- No allow list: tests that need the character write the escape `\u2014`.

- 2026-10-24 done

- 2026-10-25 done

### S3: Workbench dirs

- Status: done
- Files: `plugins/workbench/scripts/lib/workbench.py`, `plugins/workbench/scripts/tests/test_workbench_root.py`, `.gitignore`, `scripts/tests/test_root_config.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only hooks && mise run test:scripts && mise run lint`
- Verified head: 35f1ce0

#### Requirement

User requirement (U1, verbatim):

- all scratchpads edits land under `.scratchpad` in workbench root, use it as the only scratchpad dir
- all logs land in gitignored `.logs` in workbench root

Design D6: `plugins/workbench/scripts/lib/workbench.py` gains `main_checkout(start)`: the `WORKBENCH_ROOT` env dir, then `CLAUDE_PROJECT_DIR`, else the parent of the absolute `git rev-parse --git-common-dir` of `start` (for a submodule checkout, the superproject's main checkout); never an integration tree or other linked worktree; None outside git. `scratchpad_dir(start)` and `logs_dir(start)` return `<main checkout>/.scratchpad` and `<main checkout>/.logs`, created on demand. CLI actions `workbench.py scratchpad` and `workbench.py logs` print (and create) the directory, work in an uninitialised template tree (they do not need `find_root`), and exit 1 with a message when no main checkout is found. `.gitignore` gains `.scratchpad/` beside `.logs/`, pinned in scripts/tests/test_root_config.py.

#### Acceptance conditions

- AC1: from a linked worktree of a repo (an integration tree), `main_checkout` returns the main checkout, never the worktree [evidence: test:plugins/workbench/scripts/tests/test_workbench_root.py::test_main_checkout_from_linked_worktree]
- AC2: WORKBENCH_ROOT wins over CLAUDE_PROJECT_DIR, which wins over git; a subdirectory resolves to the toplevel; outside git it is None [evidence: test:plugins/workbench/scripts/tests/test_workbench_root.py::test_main_checkout_precedence]
- AC3: `workbench.py scratchpad` and `workbench.py logs` print `<main>/.scratchpad` and `<main>/.logs`, create them, work from a linked worktree and in a tree with no .gitmodules, and exit 1 outside git [evidence: test:plugins/workbench/scripts/tests/test_workbench_root.py::test_scratchpad_and_logs_cli]
- AC4: `.gitignore` lists `.scratchpad/` and `.logs/`, pinned [evidence: test:scripts/tests/test_root_config.py::test_gitignore_base_entries]
- AC5: scripts, hooks and root scripts suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only hooks && mise run test:scripts && mise run lint]

#### Files

- `plugins/workbench/scripts/lib/workbench.py`
- `plugins/workbench/scripts/tests/test_workbench_root.py`
- `.gitignore`
- `scripts/tests/test_root_config.py`

#### Interfaces

- `workbench.main_checkout(start: Path | None = None) -> Path | None`
- `workbench.scratchpad_dir(start: Path | None = None) -> Path | None`, `workbench.logs_dir(start: Path | None = None) -> Path | None` (mkdir parents, exist_ok)
- CLI: `python3 plugins/workbench/scripts/lib/workbench.py scratchpad|logs [--from DIR]`

#### Expected outcome

Every caller (hooks, ticket.py, scripts, skills) resolves the one `.scratchpad` and `.logs` of the main checkout from anywhere, including an integration tree.

#### Steps

1. List the files under Files, read them in one pass; write AC1-AC4 tests (clear WORKBENCH_ROOT and CLAUDE_PROJECT_DIR with monkeypatch in every test, the suite may run inside a Claude session) and run them: they fail.
2. Implement; add `.scratchpad/` to .gitignore; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 3 points.
- Reuse (brief): workbench.py:find_root (65) honours WORKBENCH_ROOT and CLAUDE_PROJECT_DIR first; hooks import workbench through hooks/worktree_lib.py:16. Do-not-build: a new root resolver in hooks.
- Fix-as-ac (brief): an integration tree is a superrepo checkout, so it can pass `_is_metarepo` (workbench.py:45) and find_root(cwd) would return the tree; `main_checkout` uses the git common dir instead (AC1).
- Do-not-build: a new `.logs/` ignore entry; .gitignore:18 already has it, pinned by test_root_config.py:40. Only `.scratchpad/` is new.
- This template repo is uninitialised (`workbench.py root` prints "kind: none"), so `main_checkout` must not depend on detect_kind.

- 2026-10-24 done

- 2026-10-25 done

### S4: Em dash edit guard

- Status: done
- Files: `plugins/workbench/hooks/lib/core.py`, `plugins/workbench/hooks/lib/harness_io.py`, `plugins/workbench/hooks/lib/apply_patch.py`, `plugins/workbench/hooks/tests/test_protect_files.py`, `plugins/workbench/hooks/tests/test_adapter.py`, `plugins/workbench/skills/start-development/references/hooks.md`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run test:scripts && mise run lint`
- Verified head: f45010f

#### Requirement

User requirement (U1, verbatim): "no em dash characters in any code, comment, commit, message, or content of any kind".

Design D4: `core.protect_files` also denies an edit or write whose new content contains U+2014: Write `content`, Edit `new_string`, MultiEdit `edits[].new_string`, NotebookEdit `new_source`, and the added lines (`+` lines and Add File bodies) of a Codex `apply_patch` envelope. The content is read from `event.raw["tool_input"]`; `harness_io.normalize` stores the normalised tool input under that Claude-named key so every harness that already emits protect-files (copilot, codex, gemini, cursor, antigravity) gets the guard with no new allowlist entry. Removing an em dash (it appears only in `old_string` or a `-` patch line) is allowed. The deny reason names U+2014 and tells the agent to use a plain hyphen. protect_files.py stays fail-closed. Design D14: the guard applies in every harness through protect-files.

#### Acceptance conditions

- AC1: a Write whose `content` holds U+2014 is denied with exit 2 and a reason naming U+2014 and a plain hyphen [evidence: test:plugins/workbench/hooks/tests/test_protect_files.py::test_em_dash_in_write_content_denied]
- AC2: an Edit whose `new_string` holds U+2014 is denied [evidence: test:plugins/workbench/hooks/tests/test_protect_files.py::test_em_dash_in_edit_new_string_denied]
- AC3: a MultiEdit with U+2014 in any `edits[].new_string` is denied [evidence: test:plugins/workbench/hooks/tests/test_protect_files.py::test_em_dash_in_multiedit_denied]
- AC4: a NotebookEdit whose `new_source` holds U+2014 is denied [evidence: test:plugins/workbench/hooks/tests/test_protect_files.py::test_em_dash_in_notebook_edit_denied]
- AC5: an Edit that removes an em dash (only `old_string` holds it) is allowed [evidence: test:plugins/workbench/hooks/tests/test_protect_files.py::test_removing_an_em_dash_is_allowed]
- AC6: a Codex `apply_patch` adding a line with U+2014 is denied and one removing it is allowed, through the adapter [evidence: test:plugins/workbench/hooks/tests/test_adapter.py::test_apply_patch_em_dash_added_line_denied]
- AC7: a Copilot `toolArgs` JSON string Write with U+2014 is denied through the adapter [evidence: test:plugins/workbench/hooks/tests/test_adapter.py::test_copilot_write_em_dash_denied]
- AC8: references/hooks.md documents the em dash check under protect-files [evidence: command:grep -n "U+2014" plugins/workbench/skills/start-development/references/hooks.md]
- AC9: hooks, start-development and root scripts suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run test:scripts && mise run lint]

#### Files

- `plugins/workbench/hooks/lib/core.py`
- `plugins/workbench/hooks/lib/harness_io.py`
- `plugins/workbench/hooks/lib/apply_patch.py`
- `plugins/workbench/hooks/tests/test_protect_files.py`
- `plugins/workbench/hooks/tests/test_adapter.py`
- `plugins/workbench/skills/start-development/references/hooks.md`

#### Interfaces

- `hooks/lib/core.py:protect_files(event) -> Decision` - path check first, then content check.
- `hooks/lib/core.py` new helper: the new content strings of an edit or write from `event.raw["tool_input"]` (Write, Edit, MultiEdit, NotebookEdit, apply_patch).
- `hooks/lib/apply_patch.py` new helper: the added lines of a patch envelope (header recognition as `patch_paths`).
- `hooks/lib/harness_io.py:normalize` - sets `raw["tool_input"]` to the normalised dict from `_tool_input` when the payload has no Claude `tool_input`.

#### Expected outcome

No agent in any harness can write an em dash into a file through an edit tool.

#### Steps

1. List the files under Files, read them in one pass with hooks/protect_files.py and hooks/tests/harness_payloads.py; write the AC1-AC7 tests and run `pytest hooks/tests/test_protect_files.py hooks/tests/test_adapter.py -q` from plugins/workbench: they fail.
2. Implement the content check, the apply_patch added-lines helper and the normalize key; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 5 points.
- Fix-as-ac (brief): NormalizedEvent (core.py:38) carries only paths and command, not content; read `event.raw` tool_input, with a test per tool shape (AC1-AC4, AC6, AC7).
- Fix-as-ac (brief, other harnesses): targets keep explicit hook allowlists (copilot.py:36-40, codex.py:20-21, gemini.py:20-23, cursor.py:17-18, antigravity.py:23-27); riding protect-files means no target change (D14).
- Reuse: harness_io._tool_input / _TOOL_INPUT_KEYS (Copilot sends toolArgs as a JSON string), apply_patch.patch_paths header rules.
- protect_files.py denies on any internal error (exit 2); keep the content check inside `decide` so that holds.
- Test data writes the character as the escape `"\u2014"` (the em dash lint scans tests too).

- 2026-10-24 done

- 2026-10-25 done

### S5: Estimate fields

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket.py`, `plugins/workbench/skills/start-development/templates/task.md`, `plugins/workbench/skills/start-development/tests/test_ticket_files.py`, `plugins/workbench/skills/start-development/tests/test_ticket_lint.py`, `plugins/workbench/skills/start-development/references/tickets.md`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: fb13db0

#### Requirement

User requirement (U2, verbatim): "each task consists also of: complexity estimate in storypoints; expected time; expected tokens"

User requirement (U4, verbatim, the seamless part): "It must be seamless for the agent (taking over most of the estimation from agent's reasoning)."

Design D7: task frontmatter appends, after `verified_head`, in this order: `points`, `expected_minutes`, `expected_tokens`, `points_actual`, `actual_minutes`, `actual_tokens`, `actual_roles`, `actual_role_tokens` (templates/task.md and the LEAN_KEYS pin change together). `ticket.py new-task --points N` takes Fibonacci storypoints (1, 2, 3, 5, 8, 13; anything else exits 1 naming the allowed values) and fills `expected_minutes` and `expected_tokens` from `calibration.expected(points, rows)`, where ticket.py collects the rows from every done task with integer `points`, `actual_minutes` and `actual_tokens`; the actual fields start empty. `ticket.py lint` checks, for tasks of todo and in-progress epics, that `points` and `points_actual` are Fibonacci and `expected_minutes`, `expected_tokens`, `actual_minutes` and `actual_tokens` are non-negative integers when set (values load as strings), and that `actual_roles` and `actual_role_tokens` match `impl N, review N` when set. `ticket.py tasks` JSON carries `points`, `expected_minutes` and `expected_tokens`. references/tickets.md documents the fields. No key or subcommand is named `estimate` (retirement pin). In this task `--points` is optional at the CLI (points-required makes it required with its callers).

#### Acceptance conditions

- AC1: `new-task --points 5` with no history writes `points: 5` and the seed minutes and tokens for 5 [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_new_task_points_fill_expected]
- AC2: with 3 done tasks of 3 points carrying actuals, `new-task --points 3` writes their median minutes and tokens [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_new_task_expected_from_history]
- AC3: `--points 4` exits 1 naming the Fibonacci values and writes nothing [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_new_task_rejects_non_fibonacci_points]
- AC4: LEAN_KEYS is the ten old keys plus the eight new ones in order, for new-task output and templates/task.md [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_task_frontmatter_is_lean]
- AC5: lint reports a non-integer `expected_minutes`, a negative `actual_tokens`, a non-Fibonacci `points_actual` and a malformed `actual_roles` on an in-progress epic, and ignores a done epic [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_lint.py::test_lint_numeric_estimate_fields]
- AC6: `ticket.py tasks <epic>` JSON carries points, expected_minutes and expected_tokens per task [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_tasks_json_carries_estimates]
- AC7: references/tickets.md lists the eight new keys [evidence: command:grep -n "expected_tokens" plugins/workbench/skills/start-development/references/tickets.md]
- AC8: start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/templates/task.md`
- `plugins/workbench/skills/start-development/tests/test_ticket_files.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_lint.py`
- `plugins/workbench/skills/start-development/references/tickets.md`

#### Interfaces

- `ticket.py:cmd_new_task` - new `--points` option; `ticket.py` new helper collecting calibration rows from done tasks (through `scan`), and a numeric field validator (restored `_minutes` from 7b187e8).
- `ticket.py:lint_problems` / `_task_problems` - numeric checks for non-done epics.
- `ticket.py:derive_tasks` - three more keys in each task dict.
- `calibration.expected`, `calibration.POINTS` from calibration-lib.

#### Expected outcome

A planner passes one number; every new task file carries points plus expected minutes and tokens from history or the seed table.

#### Steps

1. List the files under Files plus calibration.py, read them in one pass; write AC1-AC6 tests and run `pytest skills/start-development/tests/test_ticket_files.py skills/start-development/tests/test_ticket_lint.py -q` from plugins/workbench: they fail.
2. Implement; update the template and tickets.md; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 5 points.
- Reuse (brief): ticket.py:load/dump/_write_task (values are strings: digits dump bare and load back as "3"), `scan` (444) and `_tasks_of` (933) for history, `_template` (332). Do-not-build: a new frontmatter parser or writer.
- Restore (brief): the removed `_minutes` whole-minute validator and `_parse_roles`/`_format_roles` from `git show 7b187e8 -- plugins/workbench/skills/start-development/scripts/ticket.py`.
- Fix-as-ac (brief): LEAN_KEYS (test_ticket_files.py:161-172) is exact and asserted on new-task output (:194) and templates/task.md (:252); append together with cmd_new_task (ticket.py:400-410) and the CLI flags (ticket.py:1591-1595).
- Fix-as-ac (brief): lint cannot validate numbers today; lint_problems (1453) checks them; done-epic task problems stay skipped (:1489).
- Retirement pins: no `estimate` subcommand or key; the legacy `estimate` key of done tasks stays readable and is never written.

- 2026-10-24 done

- 2026-10-25 done

### S6: Housekeeping rules

- Status: done
- Files: `plugins/workbench/rules/housekeeping.md`, `scripts/harness/agents_md.py`, `AGENTS.md`, `scripts/tests/test_agents_md.py`, `scripts/tests/harness/test_agents_md_block.py`, `plugins/workbench/skills/start-development/references/non-negotiables.md`
- Verify: `mise run test:scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: bb010ff

#### Requirement

User requirement (U1, verbatim):

- the agent I interact with never writes code, or builds anything- it's supervisor only, who is responsible and accountable for any and all work done by other subagents
- don't edit/delete/xfail tests to make them pass, unless the test itself is no longer accurate- tests are here to make the code repeatable and ensure lack of regressions
- implementing/reviewing subagents must (before changing anything) list all files, then read them in one pass, only then make all edits, then run tests once
- no backward compatibility unless I explicitely ask for it
- no em dash characters in any code, comment, commit, message, or content of any kind
- do not guess (at any level)- it's better to ask either me or fable architect if unsure
- always aim for the full scope of the improvement- never cut corners, or reduce scope
- all scratchpads edits land under `.scratchpad` in workbench root, use it as the only scratchpad dir
- all logs land in gitignored `.logs` in workbench root

Design D1: the rules live in a new `plugins/workbench/rules/housekeeping.md` (heading `# Housekeeping rules`, frontmatter like the other rule files) that states every rule above; `scripts/harness/agents_md.py:RULE_FILES` gains it, and `mise run harness-setup` regenerates AGENTS.md in this task. The "run tests once" rule is stated as reconciled with TDD (D2): list every file, read all in one pass, make all edits for the step, run the targeted verify once per red or green step. Existing statements are amended for consistency, not duplicated: AGENTS.md ground rule 3 ("Finish the whole scope") and "Writing and working conventions" (no em dashes) point at or agree with the new rules, and `references/non-negotiables.md` "Orchestrate. Do not implement." states that the orchestrator is the supervisor, accountable for all subagent work, and never writes code or builds anything.

#### Acceptance conditions

- AC1: housekeeping.md states all nine rules: the test checks the phrases "supervisor", "accountable", "xfail", "no longer accurate", "list every file", "one pass", "backward compatibility", "em dash", "fable", "full scope", ".scratchpad" and ".logs" in the rule file and in AGENTS.md, and AGENTS.md has exactly one "## Housekeeping rules" heading [evidence: test:scripts/tests/test_agents_md.py::test_housekeeping_rules]
- AC2: RULE_FILES names housekeeping.md and the rendered rules block contains its heading [evidence: test:scripts/tests/harness/test_agents_md_block.py::test_rules_block_includes_housekeeping]
- AC3: AGENTS.md is regenerated and has no drift [evidence: command:python3 scripts/harness/setup.py --check]
- AC4: AGENTS.md stays under the byte caps [evidence: command:bash mise-tasks/lint/agents-md]
- AC5: non-negotiables.md "Orchestrate. Do not implement." names the orchestrator as supervisor, accountable for all subagent work [evidence: command:grep -n "accountable" plugins/workbench/skills/start-development/references/non-negotiables.md]
- AC6: the root scripts suite, the start-development suite and lint pass [evidence: command:mise run test:scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

#### Files

- `plugins/workbench/rules/housekeeping.md`
- `scripts/harness/agents_md.py`
- `AGENTS.md`
- `scripts/tests/test_agents_md.py`
- `scripts/tests/harness/test_agents_md_block.py`
- `plugins/workbench/skills/start-development/references/non-negotiables.md`

#### Interfaces

- `scripts/harness/agents_md.py:RULE_FILES` - tuple order decides block order; append `housekeeping.md`.
- `plugins/workbench/rules/housekeeping.md` - same frontmatter shape as rules/tdd.md (parsed by `harness.sources.parse_frontmatter`).

#### Expected outcome

Every workbench AGENTS.md (through `mise run harness-setup`) carries the housekeeping rules; this repo's AGENTS.md is regenerated and lint:harness is clean.

#### Steps

1. List every file under Files plus rules/tdd.md and AGENTS.md's ground rules, read them in one pass; write the two tests (AC1, AC2) and run them: they fail on the missing rule file.
2. Write housekeeping.md, add it to RULE_FILES, amend AGENTS.md ground rule 3 and the writing conventions and non-negotiables.md for consistency, run `mise run harness-setup`, then the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 3 points.
- Do-not-build (brief): separate "never weaken or delete a test", "orchestrator never implements", "full scope" and "no em dashes" statements already exist (implementer.md:59,90, reviewer.md:40-41, non-negotiables.md:8-12, SKILL.md:104,146, AGENTS.md ground rule 3 and Writing conventions, pinned by scripts/tests/test_agents_md.py:90); the rule file restates them consistently and the others are amended, never duplicated.
- Fix-as-ac: AGENTS.md byte cap (mise-tasks/lint/agents-md, under 24000, 11184 now) and harness-setup drift (lint:harness) - AC3, AC4. Never edit the generated block by hand.
- The TDD reconciliation wording is D2 (gate Q1); the implementer and reviewer texts follow in agent-discipline.
- AGENTS.md and rule text are ASCII only; the em dash lint from em-dash-lint now runs on them.

- 2026-10-24 done

- 2026-10-25 done

### S7: Test logs dir

- Status: done
- Files: `plugins/workbench/scripts/run-tests.sh`, `plugins/workbench/scripts/flake-hunt.sh`, `plugins/workbench/scripts/tests/test_run_tests.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint`
- Verified head: 11f9442

#### Requirement

User requirement (U1, verbatim): "all logs land in gitignored `.logs` in workbench root".

Design D6: `plugins/workbench/scripts/run-tests.sh` keeps a failing component's full output in `<main checkout>/.logs/run-tests/<UTC timestamp>-<pid>/` by default (resolved with `python3 <plugin>/scripts/lib/workbench.py logs`), falling back to a mktemp dir under TMPDIR only when no main checkout is found; `RUN_TESTS_LOG_DIR` still overrides, and the directory is still removed when everything passes. `flake-hunt.sh` keeps its run logs in `<main checkout>/.logs/flake-hunt/<UTC timestamp>-<pid>/` with the same fallback. Script headers name the new locations.

#### Acceptance conditions

- AC1: a failing run keeps its logs under `<main checkout>/.logs/run-tests/` and prints that path [evidence: test:plugins/workbench/scripts/tests/test_run_tests.py::test_failing_component_keeps_full_output]
- AC2: RUN_TESTS_LOG_DIR still overrides the default, and with no main checkout the logs fall back to TMPDIR [evidence: test:plugins/workbench/scripts/tests/test_run_tests.py::test_log_dir_override_and_fallback]
- AC3: a green run leaves nothing behind [evidence: test:plugins/workbench/scripts/tests/test_run_tests.py::test_green_run_leaves_nothing]
- AC4: flake-hunt keeps its logs under `<main checkout>/.logs/flake-hunt/` [evidence: test:plugins/workbench/scripts/tests/test_run_tests.py::test_flake_hunt_reports_failures_and_keeps_logs]
- AC5: the scripts suite and lint (shellcheck) pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

#### Files

- `plugins/workbench/scripts/run-tests.sh`
- `plugins/workbench/scripts/flake-hunt.sh`
- `plugins/workbench/scripts/tests/test_run_tests.py`

#### Interfaces

- `run-tests.sh [--only <component>]`, env `RUN_TESTS_LOG_DIR` - unchanged contract, new default.
- `flake-hunt.sh <component> <runs> [parallel]` - unchanged contract, new log location.

#### Expected outcome

Test and flake-hunt logs an agent reads after a failure sit in the gitignored `.logs` of the main checkout.

#### Steps

1. List the files under Files, read them in one pass; adjust the existing log-location tests and add AC2; run `pytest scripts/tests/test_run_tests.py -q` from plugins/workbench: they fail.
2. Implement in both scripts; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 2 points.
- The test fixture `tree` copies the scripts into a temp tree; give it a temp main checkout (git init) or set WORKBENCH_ROOT, and clear CLAUDE_PROJECT_DIR.
- Keep the per-pytest `--basetemp` under the log dir.
- Depends on workbench-dirs for `workbench.py logs`.

- 2026-10-24 done

- 2026-10-25 done

### S8: Agent discipline

- Status: done
- Files: `plugins/workbench/agents/implementer.md`, `plugins/workbench/agents/reviewer.md`, `plugins/workbench/skills/start-review/tests/test_agents_lean.py`, `plugins/workbench/agents/planner.md`, `plugins/workbench/skills/start-development/tests/test_planner_agent.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-research && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint`
- Verified head: b9ee9ba

#### Requirement

User requirement (U1, verbatim, the parts addressed to implementing and reviewing subagents):

- don't edit/delete/xfail tests to make them pass, unless the test itself is no longer accurate- tests are here to make the code repeatable and ensure lack of regressions
- implementing/reviewing subagents must (before changing anything) list all files, then read them in one pass, only then make all edits, then run tests once
- no backward compatibility unless I explicitely ask for it
- do not guess (at any level)- it's better to ask either me or fable architect if unsure
- always aim for the full scope of the improvement- never cut corners, or reduce scope

Design D2: implementer.md and reviewer.md carry the discipline reconciled with TDD: list every file the step touches, read them all in one pass, make all edits for the step, then run the targeted verify once per red or green step, never an edit-run-edit-run dribble; this agrees with rules/tdd.md (red, then green, then refactor). The test-tampering rule reads: never edit, delete, skip or xfail a test to make it pass, unless the test itself is no longer accurate, and then say which test and why. The reviewer treats an added skip or xfail, a weakened test, and a backward compatibility shim the requirement did not ask for as high findings. An implementer unsure of a fact does not guess: it returns the question in a new report field `questions` (the orchestrator asks the user or fable). Existing pinned wording (`undelivered`, `discovered`, `tests.red`, `handoff`, the reviewer's step order and output fields, the word caps) stays.

README goal G3 names the planner too: planner.md carries the same discipline for its own work (list every file the plan touches, read them in one pass before writing tasks) and the no-tampering rule for what it plans: it never plans a task that edits, deletes, skips or xfails a test to make it pass unless the test itself is no longer accurate, and it states that a requirement it is unsure of is asked (open question), never guessed.

#### Acceptance conditions

- AC1: implementer.md and reviewer.md state "list every file", "one pass" and "once per red or green step" [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_agents_list_read_once_edit_once]
- AC2: implementer.md and reviewer.md forbid editing, deleting, skipping or xfailing a test to make it pass, with the "no longer accurate" exception named [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_no_test_tampering]
- AC3: reviewer.md makes an added skip or xfail and an unrequested backward compatibility shim high findings [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_reviewer_flags_xfail_and_compat_shims]
- AC4: implementer.md's Report section has a `questions` field and says to ask instead of guessing [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_implementer_asks_instead_of_guessing]
- AC5: the existing pins hold (lean implementer, reviewer order) [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_reviewer_verifies_then_reviews]
- AC6: the agent-text suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-research && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]
- AC7: planner.md states "list every file", "one pass", the no-tampering rule with the "no longer accurate" exception, and asks instead of guessing [evidence: test:plugins/workbench/skills/start-development/tests/test_planner_agent.py::test_planner_discipline]

#### Files

- `plugins/workbench/agents/implementer.md`
- `plugins/workbench/agents/reviewer.md`
- `plugins/workbench/skills/start-review/tests/test_agents_lean.py`
- `plugins/workbench/agents/planner.md`
- `plugins/workbench/skills/start-development/tests/test_planner_agent.py`

#### Interfaces

- implementer report fields: existing `complete`, `summary`, `commits`, `acEvidence`, `undelivered`, `discovered`, `tests`, `verification`, plus `questions` (list of strings).
- reviewer output fields unchanged: `head`, `verifyPassed`, `unmetAcs`, `findings`, `declined`, `cannotVerify`.

#### Expected outcome

The implementer, reviewer and planner texts carry the list, read once, edit all, verify once per step discipline, the no-tampering rule with its exception, the no-compat-shim rule and the ask-do-not-guess rule, consistent with rules/tdd.md and rules/housekeeping.md.

#### Steps

1. List the files under Files plus rules/tdd.md and rules/housekeeping.md, read them in one pass; add the four new tests and run `pytest skills/start-review/tests/test_agents_lean.py -q` from plugins/workbench: they fail.
2. Amend implementer.md and reviewer.md (amend the existing lines at implementer.md "Never weaken or delete" and reviewer.md step 4, do not add parallel statements); run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 2 points.
- Do-not-build (brief): a separate "never weaken or delete a test" rule; amend implementer.md:59,90 and reviewer.md:40-41.
- Fix-as-ac (brief, conflict with TDD): the discipline reads "list, read all, edit all, run verify once per red/green step" and must agree with tdd.md and implementer.md:52-57.
- Agent files are pinned by test_epic_skills_structure.py (word caps, `acEvidence`) and test_start_skills_structure.py; keep those phrases.
- `pointsActual` for the reviewer is added later by run-marker-points; do not add it here.

- 2026-10-24 done

- 2026-10-25 done

### S9: Em dash commit guard

- Status: done
- Files: `plugins/workbench/hooks/lib/core.py`, `plugins/workbench/hooks/tests/test_guard_bash.py`, `plugins/workbench/skills/start-development/references/hooks.md`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: cea87f1

#### Requirement

User requirement (U1, verbatim): "no em dash characters in any code, comment, commit, message, or content of any kind".

Design D5: guard-bash denies a `git commit` whose message carries U+2014. When any normalised segment of the command (after `_normalize`, so `git -C <dir> commit` counts) matches `^git\s+commit\b` and the whole command contains U+2014, deny; this covers `-m`, a heredoc and `$(cat <<EOF ... EOF)` because heredoc lines are segments of the same command. For `-F <file>`, `-F<file>`, `--file <file>` and `--file=<file>`, the guard reads the file (relative to the event cwd) when it exists and denies when it contains U+2014; a missing or unreadable file is not a deny. The reason names U+2014 and tells the agent to use a plain hyphen.

#### Acceptance conditions

- AC1: `git commit -m "<text with U+2014>"` is denied, and `git -C repo commit -m ...` too [evidence: test:plugins/workbench/hooks/tests/test_guard_bash.py::test_commit_message_em_dash_denied]
- AC2: a heredoc message and a `$(cat <<'EOF' ... EOF)` message holding U+2014 are denied [evidence: test:plugins/workbench/hooks/tests/test_guard_bash.py::test_commit_heredoc_em_dash_denied]
- AC3: `git commit -F msg.txt` and `--file=msg.txt` are denied when the file holds U+2014, allowed when it does not, and allowed when the file is missing [evidence: test:plugins/workbench/hooks/tests/test_guard_bash.py::test_commit_message_file_em_dash]
- AC4: a commit with a plain-hyphen message and a non-commit command are not denied by this rule [evidence: test:plugins/workbench/hooks/tests/test_guard_bash.py::test_commit_without_em_dash_allowed]
- AC5: references/hooks.md documents the commit check under guard-bash [evidence: command:grep -n "git commit" plugins/workbench/skills/start-development/references/hooks.md]
- AC6: hooks and start-development suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

#### Files

- `plugins/workbench/hooks/lib/core.py`
- `plugins/workbench/hooks/tests/test_guard_bash.py`
- `plugins/workbench/skills/start-development/references/hooks.md`

#### Interfaces

- `hooks/lib/core.py:guard_bash(event) -> Decision` - adds the commit-message check after the RULES loop and before the idle no-op check.
- Reuses `guard_segments`, `_normalize` (`_GIT_GLOBALS` strips `-C <dir>`), `segments`.

#### Expected outcome

No agent commits a message with an em dash through Bash, in any harness that emits guard-bash.

#### Steps

1. List the files under Files, read them in one pass; write AC1-AC4 tests and run `pytest hooks/tests/test_guard_bash.py -q` from plugins/workbench: they fail.
2. Implement the check; document it; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 3 points.
- Fix-as-ac (brief): guard_segments splits on newlines (core.py SEPARATORS 214, segments 230), so heredoc lines are separate segments: match the commit segment, then test the whole command for U+2014. -F <file> is handled by reading the file (D5), not left as a gap.
- Test data writes the character as the escape `"\u2014"`.
- Depends on em-dash-edit-guard only because both edit core.py and hooks.md.

- 2026-10-24 done

- 2026-10-25 done

### S10: Plugin readme rules

- Status: done
- Files: `plugins/workbench/README.md`, `plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: 1dc8d46

#### Requirement

Discovered by the housekeeping-rules implementer: `plugins/workbench/README.md` lines 287-289 list the plugin's cross-cutting rules (tdd, boy-scout, concise-orchestrator) without the new `housekeeping.md`. Add housekeeping to that list with a one-line description matching the rule file's frontmatter description, keep the list's existing format, ASCII only, no em dash. Add a test in `plugins/workbench/skills/start-development/tests/` (or extend the existing README-rules test if one exists) that asserts every file in `plugins/workbench/rules/` named in `scripts/harness/agents_md.py` RULE_FILES is named in the plugin README's rules list.

#### Acceptance conditions

- AC1: the plugin README names housekeeping among the cross-cutting rules [evidence: command:grep -n "housekeeping" plugins/workbench/README.md]
- AC2: a test pins that every RULE_FILES entry is named in the plugin README [evidence: test:plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py::test_readme_lists_every_rules_block_file]

#### Files

- `plugins/workbench/README.md`
- `plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

1. Read `plugins/workbench/README.md` (the rules list near lines 287-289), `plugins/workbench/rules/housekeeping.md` (its frontmatter description) and `scripts/harness/agents_md.py` (RULE_FILES).
2. Write `test_plugin_readme_rules.py::test_readme_lists_every_rules_block_file` first; run `pytest plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py -q` and see it fail because housekeeping is missing from the README.
3. Add the housekeeping line to the README list in the existing format; run the verify once and see it green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Estimate: 1 points

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-24 todo: Estimate: 1 points

- 2026-10-24 done

- 2026-10-25 done

### S11: Points required

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket.py`, `plugins/workbench/skills/start-development/tests/ticket_repo_helpers.py`, `plugins/workbench/skills/start-development/tests/test_ticket_overlap_ignore.py`, `plugins/workbench/skills/start-development/tests/test_ticket_check.py`, `plugins/workbench/skills/start-development/tests/test_ticket_naming.py`, `plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py`, `plugins/workbench/skills/start-development/tests/test_ticket_files.py`, `plugins/workbench/skills/start-development/tests/test_ticket_lint.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: e73b57b

#### Requirement

User requirement (U2, verbatim): "each task consists also of: complexity estimate in storypoints; expected time; expected tokens"

Design D7: `new-task --points` is required (argparse exits 2 naming `--points` when it is missing), and `ticket.py lint` reports every task of a todo or in-progress epic that has no `points`. Every test that creates a task through `new-task` passes `--points`; no compatibility default is added (U1: no backward compatibility unless asked).

#### Acceptance conditions

- AC1: `new-task` without `--points` exits 2 and names `--points` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_new_task_requires_points]
- AC2: lint reports a task of a todo epic with no points and passes once points are set [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_lint.py::test_lint_requires_points]
- AC3: every test helper and call that runs `new-task` passes `--points` (no default added in ticket.py) [evidence: command:! grep -n "default=.*points\|points.*default=" plugins/workbench/skills/start-development/scripts/ticket.py]
- AC4: start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/ticket_repo_helpers.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_overlap_ignore.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_check.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_naming.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_files.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_lint.py`

#### Interfaces

- `ticket.py` new-task parser: `--points` required, `type=int`.
- `ticket.py:_task_problems` - "task <slug> has no points" for non-done epics.

#### Expected outcome

No task can be created or pass lint without storypoints.

#### Steps

1. List the files under Files, read them in one pass; write AC1 and AC2 and run them: they fail.
2. Make the flag required, add the lint check, add `--points` to every new-task call in the listed tests and helpers; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 3 points.
- The callers are the `"new-task"` invocations in test_ticket_overlap_ignore.py, test_ticket_check.py, test_ticket_naming.py (helper), ticket_repo_helpers.py, test_ticket_worktrees_refresh.py and test_ticket_files.py (helper). If a caller outside Files turns up, report it in `discovered`.
- Splitting this from estimate-fields keeps each task at most 8 files; the two land in order.

- 2026-10-25 done

- 2026-10-25 done

### S12: Output spill to logs

- Status: done
- Files: `plugins/workbench/hooks/worktree_lib.py`, `plugins/workbench/hooks/bash-output-filter.py`, `plugins/workbench/hooks/tests/test_bash_output_filter.py`, `plugins/workbench/hooks/tests/test_output_filter_unwrap.py`, `plugins/workbench/skills/start-development/references/hooks.md`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: 303f638

#### Requirement

User requirement (U1, verbatim): "all logs land in gitignored `.logs` in workbench root".

Design D6: the bash-output-filter spill file (the full output of a capped command, whose path the agent is told to read) is a log, so it lands in `<main checkout>/.logs/bash-output/` instead of `$TMPDIR`. `worktree_lib.wrap_output_filter` builds the wrapper with the spill directory resolved at hook time through `workbench.logs_dir` (cwd of the hook event), falling back to `${TMPDIR:-/tmp}` only when no main checkout is found; `unwrap_output_filter` recognises the wrapper for any spill directory, so verify-recorder and the commit guard still see the original command. Small outputs still delete their spill file. The docstrings and references/hooks.md name the new location.

#### Acceptance conditions

- AC1: a capped command's full output is spilled under `<main checkout>/.logs/bash-output/` and the printed path points there [evidence: test:plugins/workbench/hooks/tests/test_bash_output_filter.py::test_spill_lands_in_logs_dir]
- AC2: with no main checkout (cwd outside git, no env) the spill falls back to TMPDIR [evidence: test:plugins/workbench/hooks/tests/test_bash_output_filter.py::test_spill_falls_back_to_tmpdir]
- AC3: a small output leaves no spill file behind [evidence: test:plugins/workbench/hooks/tests/test_bash_output_filter.py::test_small_output_spill_file_is_removed]
- AC4: `unwrap_output_filter(wrap_output_filter(cmd, n))` returns `cmd` for a logs-dir wrapper and a TMPDIR wrapper, and a non-wrapper is returned unchanged [evidence: test:plugins/workbench/hooks/tests/test_output_filter_unwrap.py::test_unwrap_any_spill_dir]
- AC5: hooks and start-development suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

#### Files

- `plugins/workbench/hooks/worktree_lib.py`
- `plugins/workbench/hooks/bash-output-filter.py`
- `plugins/workbench/hooks/tests/test_bash_output_filter.py`
- `plugins/workbench/hooks/tests/test_output_filter_unwrap.py`
- `plugins/workbench/skills/start-development/references/hooks.md`

#### Interfaces

- `hooks/worktree_lib.py:wrap_output_filter(command: str, cap_chars: int, spill_dir: str | None = None) -> str` (or an equivalent that takes the directory), `unwrap_output_filter(command: str) -> str` unchanged in signature.
- `workbench.logs_dir(start)` from workbench-dirs.

#### Expected outcome

Every spilled command output an agent is pointed to sits in the gitignored `.logs/bash-output/` of the main checkout.

#### Steps

1. List the files under Files, read them in one pass; update the spill tests (they set TMPDIR today) and add AC1, AC2, AC4; run `pytest hooks/tests/test_bash_output_filter.py hooks/tests/test_output_filter_unwrap.py -q` from plugins/workbench: they fail.
2. Implement; update the docstrings and hooks.md; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 3 points.
- WRAP_HEAD is a constant today (worktree_lib.py:36) and unwrap matches it literally; make the head a pattern with the directory as the only variable part, keeping "the hook that writes it and the code that unwraps it cannot drift apart".
- Quote the directory safely in the shell snippet (paths with spaces).
- Tests must clear WORKBENCH_ROOT and CLAUDE_PROJECT_DIR, or set them to a temp main checkout.

- 2026-10-25 done

- 2026-10-25 done

### S13: Agent usage lib

- Status: done
- Files: `plugins/workbench/scripts/lib/agent_usage.py`, `plugins/workbench/scripts/tests/test_agent_usage.py`, `plugins/workbench/hooks/lib/core.py`, `plugins/workbench/hooks/tests/test_core_stop.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only hooks && mise run lint`
- Verified head: f34227b

#### Requirement

User requirement (U3, verbatim, the measured part): "delivery time (start to finish in minutes), tokens used for each task (including implementation + review)"

User requirement (U4, verbatim, the seamless part): "It must be seamless for the agent (taking over most of the estimation from agent's reasoning)."

Design D9: `plugins/workbench/scripts/lib/agent_usage.py` (stdlib, Python 3.9 safe) owns the per-agent usage record. `transcript_lines(path)` yields each JSON object of a transcript, skipping unreadable or garbled lines; `core.collect_worktrees` uses it instead of its inline loop. `summarize(path)` returns the first and last `timestamp`, the model of the last assistant line, and tokens summed once per `message.id` (falling back to `requestId`, then the line itself), keeping `input`, `cache_creation`, `cache_read` and `output` and their `total`. `parse_marker(path)` reads the first line of the first user message and matches `[wb <epic>/<task>/<role>]` (role `impl` or `review`). `role_for(marker_role, agent_type)` takes the marker role, else maps `workbench:implementer` to `impl` and `workbench:reviewer` to `review`. `write_record(logs_dir, record)` writes `<logs>/agents/<agentId>.json` as an atomic overwrite (temp file plus os.replace), never an append. `read_records(logs_dir, epic=None, task=None)` returns the matching records, re-summarising each from its `transcript` when that file still exists. Tokens are input + cache_creation + cache_read + output (hooks brief finding 4).

#### Acceptance conditions

- AC1: a transcript fixture with the same message.id on several assistant lines counts its usage once; requestId is the fallback key [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_tokens_summed_once_per_message_id]
- AC2: garbled and non-assistant lines are skipped; start, end and model come from the transcript [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_summarize_tolerates_garbage]
- AC3: the marker is parsed from the first user message's first line, and the role falls back to agentType when the marker is missing [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_marker_and_role]
- AC4: writing the same agent's record twice leaves one file holding the second record [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_write_record_overwrites]
- AC5: read_records filters by epic and task and re-summarises from the transcript when it exists, else keeps the stored totals [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_read_records_resummarises]
- AC6: the commit guard still finds worktrees from the transcript through the shared iterator [evidence: test:plugins/workbench/hooks/tests/test_core_stop.py::test_commit_guard_decisions]
- AC7: scripts and hooks suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only hooks && mise run lint]

#### Files

- `plugins/workbench/scripts/lib/agent_usage.py`
- `plugins/workbench/scripts/tests/test_agent_usage.py`
- `plugins/workbench/hooks/lib/core.py`
- `plugins/workbench/hooks/tests/test_core_stop.py`

#### Interfaces

- `agent_usage.MARKER` (compiled regex), `agent_usage.transcript_lines(path) -> Iterator[dict]`
- `agent_usage.summarize(path) -> dict` keys `start`, `end`, `model`, `tokens` (`input`, `cache_creation`, `cache_read`, `output`, `total`)
- `agent_usage.parse_marker(path) -> tuple[str, str, str] | None`, `agent_usage.role_for(marker_role, agent_type) -> str`
- Record JSON: `agentId`, `agentType`, `model`, `epic`, `task`, `role`, `transcript`, `start`, `end`, `tokens`, `updatedAt`.
- `agent_usage.write_record(logs_dir, record) -> Path`, `agent_usage.read_records(logs_dir, epic=None, task=None) -> list[dict]`

#### Expected outcome

One shared module reads Claude transcripts correctly (no double counting) and owns the record format the hook writes and ticket.py reads.

#### Steps

1. List the files under Files, read them in one pass with hooks/worktree_lib.py (how hooks import scripts/lib); write test_agent_usage.py with transcript fixtures and run `pytest scripts/tests/test_agent_usage.py -q` from plugins/workbench: it fails.
2. Implement; switch core.collect_worktrees to the shared iterator; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 5 points.
- Reuse (brief): the transcript loop in hooks/lib/core.py:collect_worktrees (450-491); factor the line iterator out, do not write a third walker. Do-not-build: a new transcript JSONL walker.
- Fix-as-ac (brief): duplicate usage per message (on-disk check: 5 assistant lines, 4 unique ids) - AC1.
- Hooks brief finding 4: assistant lines carry `timestamp`, `message.model`, `message.usage` with input_tokens, cache_creation_input_tokens, cache_read_input_tokens, output_tokens; keep the four components.
- Do-not-build (hooks brief): per-agent duration from the Agent tool result (no usage for background agents); use transcript timestamps.
- `aggregate` across records for a task is added by stamp-actuals.

- 2026-10-25 done

- 2026-10-25 done

### S14: Scratch locations

- Status: done
- Files: `plugins/workbench/skills/start-debugging/references/loops.md`, `plugins/workbench-observability/skills/kubectl-logs-query/SKILL.md`, `plugins/workbench/agents/planner.md`, `plugins/workbench/skills/start-development/tests/test_planner_agent.py`, `scripts/tests/test_scratch_and_log_dirs.py`
- Verify: `mise run test:scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-debugging && mise run test:pack-observability && mise run lint`
- Verified head: fd6600a

#### Requirement

User requirement (U1, verbatim):

- all scratchpads edits land under `.scratchpad` in workbench root, use it as the only scratchpad dir
- all logs land in gitignored `.logs` in workbench root

Design D6: every skill, agent and script that names a scratch or log location names `<workbench root>/.scratchpad` or `<workbench root>/.logs`: start-debugging's `references/loops.md` pristine copy (`cp f /tmp/pristine-f`) moves to `.scratchpad`, kubectl-logs-query's "to the scratchpad" names `<workbench root>/.scratchpad`, and planner.md's "written under the scratchpad" names `<workbench root>/.scratchpad` (resolved with `workbench.py scratchpad`). A new tree-wide pin test `scripts/tests/test_scratch_and_log_dirs.py` scans the tracked non-test files of plugins/, scripts/ and mise-tasks/ (CHANGELOG excluded) and fails on `/tmp/`, `TMPDIR`, `mktemp` or a bare "the scratchpad" outside an explicit allowlist in the test, each entry with its reason: transient temp files created and removed within one run (suite-lock.sh lock dir, mise-tasks/lint/secrets staging, scripts/probes/claude-plugin-load.sh) and the no-main-checkout fallbacks in run-tests.sh, flake-hunt.sh and worktree_lib.py.

#### Acceptance conditions

- AC1: no tracked non-test file names `/tmp/`, `TMPDIR`, `mktemp` or a bare "the scratchpad" outside the allowlist, and every allowlist entry carries a reason and still matches a real hit [evidence: test:scripts/tests/test_scratch_and_log_dirs.py::test_scratch_and_log_locations]
- AC2: planner.md names `.scratchpad` as where task bodies and input files are written [evidence: test:plugins/workbench/skills/start-development/tests/test_planner_agent.py::test_planner_rules]
- AC3: loops.md and kubectl-logs-query SKILL.md name `.scratchpad` [evidence: command:grep -n "\.scratchpad" plugins/workbench/skills/start-debugging/references/loops.md plugins/workbench-observability/skills/kubectl-logs-query/SKILL.md]
- AC4: root scripts, start-development, start-debugging and observability pack suites and lint pass [evidence: command:mise run test:scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-debugging && mise run test:pack-observability && mise run lint]

#### Files

- `plugins/workbench/skills/start-debugging/references/loops.md`
- `plugins/workbench-observability/skills/kubectl-logs-query/SKILL.md`
- `plugins/workbench/agents/planner.md`
- `plugins/workbench/skills/start-development/tests/test_planner_agent.py`
- `scripts/tests/test_scratch_and_log_dirs.py`

#### Interfaces

- `scripts/tests/test_scratch_and_log_dirs.py`: an `ALLOW` mapping of path to reason; the scan uses `git ls-files` (reuse `scripts/check_personal.py:_tracked`/`_text`).

#### Expected outcome

The only scratch and log locations named anywhere in the tracked tooling are `.scratchpad` and `.logs` of the workbench root, and a test keeps it that way.

#### Steps

1. List the files under Files, read them in one pass; write the pin test and the planner assertion; run `pytest scripts/tests/test_scratch_and_log_dirs.py -q`: it fails on loops.md, kubectl-logs-query and planner.md.
2. Amend the three texts; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 3 points.
- Fix-as-ac (brief): planner.md:67 says "the scratchpad" generically and test_planner_agent.py:74 pins the word "scratchpad"; keep the word, add the location.
- Depends on output-spill-to-logs and test-logs-dir so their fallbacks exist before the allowlist pins them.
- Exclude tests directories (they legitimately use tmp_path and TMPDIR) and CHANGELOG files.

- 2026-10-25 done

- 2026-10-25 done

### S15: Agent usage hook

- Status: done
- Files: `plugins/workbench/hooks/agent-usage-recorder.py`, `plugins/workbench/hooks/tests/test_agent_usage_recorder.py`, `plugins/workbench/hooks/tests/test_py39_safe.py`, `plugins/workbench/.claude-plugin/plugin.json`, `plugins/workbench/skills/start-development/references/hooks.md`, `scripts/tests/harness/test_claude_only_hooks.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run test:scripts && mise run lint`
- Verified head: cec85a7

#### Requirement

User requirement (U3, verbatim, the measured part): "delivery time (start to finish in minutes), tokens used for each task (including implementation + review)"

User requirement (U1, verbatim): "all logs land in gitignored `.logs` in workbench root"

Design D9: a new hook `plugins/workbench/hooks/agent-usage-recorder.py` (Python 3.9 safe, `from __future__ import annotations`) runs on SubagentStart and SubagentStop through two new `.claude-plugin/plugin.json` entries; the subagent-commit-guard entry and its Decision are unchanged. On SubagentStart it writes the record with the start time, `agent_id`, `agent_type`, the agent transcript path derived from `transcript_path` and `session_id` (`<dir>/<session_id>/subagents/agent-<agent_id>.jsonl`) and the marker when readable. On SubagentStop it recomputes the record from the whole `agent_transcript_path` with `agent_usage.summarize`, keeps the earlier start from the SubagentStart record, and overwrites `<main checkout>/.logs/agents/<agentId>.json` (resolved with `workbench.logs_dir` from the event cwd, so a subagent in an integration tree writes to the main checkout). An event with an empty `agent_type` (internal agents) writes nothing. Any error (garbled stdin, missing or garbled transcript, unwritable dir) exits 0 with no output. Design D14: the recorder is Claude-only; no harness target emits it, pinned by a root test.

#### Acceptance conditions

- AC1: a SubagentStop payload with a transcript writes `.logs/agents/<agentId>.json` with agentType, model, epic, task, role, start, end and tokens [evidence: test:plugins/workbench/hooks/tests/test_agent_usage_recorder.py::test_stop_writes_record]
- AC2: stopping the same agent twice (a fix round) overwrites one record recomputed from the whole transcript, tokens not doubled [evidence: test:plugins/workbench/hooks/tests/test_agent_usage_recorder.py::test_second_stop_overwrites]
- AC3: SubagentStart writes the start record and a later stop keeps that start [evidence: test:plugins/workbench/hooks/tests/test_agent_usage_recorder.py::test_start_then_stop_keeps_start]
- AC4: an event with an empty agent_type writes nothing [evidence: test:plugins/workbench/hooks/tests/test_agent_usage_recorder.py::test_internal_agent_writes_nothing]
- AC5: garbled stdin, a missing transcript and a garbled transcript all exit 0 with empty stdout [evidence: test:plugins/workbench/hooks/tests/test_agent_usage_recorder.py::test_fails_open]
- AC6: with cwd inside a linked worktree the record lands under the main checkout's `.logs`, with and without meta.json beside the transcript [evidence: test:plugins/workbench/hooks/tests/test_agent_usage_recorder.py::test_record_lands_in_main_checkout]
- AC7: plugin.json registers the recorder on SubagentStart and SubagentStop and keeps the commit guard entry unchanged [evidence: test:plugins/workbench/hooks/tests/test_agent_usage_recorder.py::test_plugin_json_registers_recorder]
- AC8: the recorder script and agent_usage.py are covered by the Python 3.9 safety tests [evidence: test:plugins/workbench/hooks/tests/test_py39_safe.py::test_every_hook_imports_without_tomllib]
- AC9: no harness target (copilot, codex, gemini, cursor, antigravity) emits agent-usage-recorder from the real plugin [evidence: test:scripts/tests/harness/test_claude_only_hooks.py::test_recorder_is_claude_only]
- AC10: references/hooks.md documents the recorder, its record path and that it is Claude-only [evidence: command:grep -n "agent-usage-recorder" plugins/workbench/skills/start-development/references/hooks.md]
- AC11: hooks, start-development and root scripts suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run test:scripts && mise run lint]

#### Files

- `plugins/workbench/hooks/agent-usage-recorder.py`
- `plugins/workbench/hooks/tests/test_agent_usage_recorder.py`
- `plugins/workbench/hooks/tests/test_py39_safe.py`
- `plugins/workbench/.claude-plugin/plugin.json`
- `plugins/workbench/skills/start-development/references/hooks.md`
- `scripts/tests/harness/test_claude_only_hooks.py`

#### Interfaces

- Entry: `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/agent-usage-recorder.py"`, stdin the Claude hook payload; reads `hook_event_name`, `agent_id`, `agent_type`, `agent_transcript_path`, `transcript_path`, `session_id`, `cwd`.
- Uses `agent_usage.summarize`, `parse_marker`, `role_for`, `write_record` and `workbench.logs_dir`.

#### Expected outcome

Every implementer and reviewer run leaves one accurate, idempotent usage record in the main checkout's `.logs/agents`, without ever blocking or slowing a stop.

#### Steps

1. List the files under Files, read them in one pass with hooks/subagent-commit-guard.py and hooks/tests/test_py39_safe.py; write the AC1-AC9 tests and run `pytest hooks/tests/test_agent_usage_recorder.py -q` from plugins/workbench and `pytest scripts/tests/harness/test_claude_only_hooks.py -q` from the repo root: they fail.
2. Implement the entry script, register it, extend the py39 lists, document it; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 5 points.
- Reuse (brief): hooks/subagent-commit-guard.py stdin parse and fail-open shape (38-43); core.verify_recorder/write_verify_record record-then-write split as the pattern.
- Fix-as-ac (brief): SubagentStop refires after a commit-guard block and every SendMessage round - keyed by agentId, idempotent overwrite (AC2). Fail open, separate plugin.json entry (AC5, AC7). Root resolution from a worktree (AC6). Role from meta.json agentType is unknown at first stop; role comes from the marker, then agentType (AC6 covers both). Python floor: test_py39_safe.py and test_fail_closed.py (the recorder is fail-open, so it is not a deny hook). Other harnesses keep explicit allowlists (D14, AC9).
- Hooks brief: SubagentStart fires on spawn and on resume; SubagentStop fires for internal agents with agent_type "" (AC4); agent transcripts live at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl` with `agent-{agentId}.meta.json` beside.
- Adopted idea (hooks brief): record at SubagentStart and overwrite at every stop, and let the stamp step re-read transcript paths so a missed stop loses nothing (read_records in agent-usage-lib).
- The recorder is not registered in core.HOOKS (brief reuse entry): it makes no allow/deny/block decision and no harness adapter runs it, so the entry script calls agent_usage directly (my call).
- Bootstrap: the plugin loads from the main checkout, so this hook records nothing until the epic merges and `/reload-plugins` runs; runs before that are recovered by actuals-backfill (D16).

- 2026-10-25 done

- 2026-10-25 done

### S16: Planner points gate

- Status: done
- Files: `plugins/workbench/agents/planner.md`, `plugins/workbench/skills/start-development/tests/test_planner_agent.py`, `plugins/workbench/skills/start-development/SKILL.md`, `plugins/workbench/skills/start-development/tests/test_lean_flow_docs.py`, `plugins/workbench/skills/epic-task-create/SKILL.md`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-review && mise run lint`
- Verified head: 3c983ec

#### Requirement

User requirement (U2, verbatim): "each task consists also of: complexity estimate in storypoints; expected time; expected tokens"

User requirement (U4, verbatim, the seamless part): "It must be seamless for the agent (taking over most of the estimation from agent's reasoning)."

Design D7: planner.md tells the planner to give each task Fibonacci storypoints with `ticket.py new-task --points N` and that the tool fills expected minutes and tokens (the planner never estimates time or tokens itself). The gate's task table in start-development/SKILL.md lists `points, expected_minutes, expected_tokens` beside id, title, value, files, depends_on, model (line-neutral: SKILL.md stays at most 150 lines). Every place the flow creates a task (`discovered` in phase 4, epic-run "What comes back", phase 5 gaps) passes `--points`. epic-task-create/SKILL.md names `--points` in its new-task command.

#### Acceptance conditions

- AC1: planner.md names `--points`, the Fibonacci values and that the tool fills expected minutes and tokens, and still never says `ticket.py estimate` [evidence: test:plugins/workbench/skills/start-development/tests/test_planner_agent.py::test_planner_gives_points]
- AC2: the gate's task table line in SKILL.md names points, expected_minutes and expected_tokens, pinned [evidence: test:plugins/workbench/skills/start-development/tests/test_lean_flow_docs.py::test_gate_table_shows_estimates]
- AC3: epic-task-create names `--points` and only flags new-task has [evidence: test:plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py::test_epic_task_create_names_only_flags_new_task_has]
- AC4: SKILL.md stays within 150 lines [evidence: test:plugins/workbench/skills/start-development/tests/test_skill_size.py::test_skill_md_within_line_cap]
- AC5: start-development and start-review suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-review && mise run lint]

#### Files

- `plugins/workbench/agents/planner.md`
- `plugins/workbench/skills/start-development/tests/test_planner_agent.py`
- `plugins/workbench/skills/start-development/SKILL.md`
- `plugins/workbench/skills/start-development/tests/test_lean_flow_docs.py`
- `plugins/workbench/skills/epic-task-create/SKILL.md`

#### Interfaces

- planner.md "Plan" step 2 command line gains `--points <n>`.
- SKILL.md "The gate" item 2 and the phase 4/5 new-task mentions.

#### Expected outcome

The planner gives one number per task; the gate shows the derived minutes and tokens; every task the flow creates carries points.

#### Steps

1. List the files under Files, read them in one pass; write AC1 and AC2 tests (update the pinned gate line in test_lean_flow_docs.py) and run them: they fail.
2. Amend the texts line-neutrally; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 2 points.
- Fix-as-ac (brief): test_planner_agent.py:63 forbids "ticket.py estimate" in planner.md; test_lean_flow_docs.py:100 pins the gate line "id, title, value, files, depends_on, model".
- Fix-as-ac (brief): SKILL.md is at 150 of 150 lines (test_skill_size.py:7); edits are line-neutral.
- Depends on scratch-locations (it edits planner.md first) and points-required (the flag exists and is required).

- 2026-10-25 done

- 2026-10-25 done

### S17: Run marker points

- Status: done
- Files: `plugins/workbench/skills/epic-run/SKILL.md`, `plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py`, `plugins/workbench/agents/reviewer.md`, `plugins/workbench/skills/start-review/tests/test_agents_lean.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only epic-run && bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: f597bdd

#### Requirement

User requirement (U3, verbatim, the per-task part): "tasks table with task title (in delivery order), post-delivery complexity measure in storypoints, delivery time (start to finish in minutes), tokens used for each task (including implementation + review)"

Design D10: epic-run step 2 starts every implementer prompt with the fixed first line `[wb <epic>/<task>/impl]` and every reviewer prompt with `[wb <epic>/<task>/review]`; fix rounds continue the same agents (SendMessage), so they need no new marker. The marker format equals `agent_usage.MARKER`. reviewer.md's Output gains `pointsActual`: the post-delivery complexity of the task in Fibonacci storypoints (1, 2, 3, 5, 8, 13), judged from the diff it reviewed against the requirement, on the same scale the planner uses. epic-run/SKILL.md stays within its line cap.

#### Acceptance conditions

- AC1: epic-run step 2 puts `[wb <epic>/<task>/impl]` first in the implementer prompt and `[wb <epic>/<task>/review]` first in the reviewer prompt [evidence: test:plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py::test_prompt_marker]
- AC2: reviewer.md's Output names `pointsActual` with the Fibonacci scale [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_reviewer_reports_points_actual]
- AC3: the epic skills stay within their line caps and pins [evidence: test:plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py::test_epic_run_skips_done_tasks_and_caps_are_one_number_per_role]
- AC4: epic-run, start-review and start-development suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only epic-run && bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

#### Files

- `plugins/workbench/skills/epic-run/SKILL.md`
- `plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py`
- `plugins/workbench/agents/reviewer.md`
- `plugins/workbench/skills/start-review/tests/test_agents_lean.py`

#### Interfaces

- Prompt marker line: `[wb <epic>/<task>/<role>]`, role `impl` or `review`, first line of the prompt.
- Reviewer output field: `pointsActual` (integer, Fibonacci).

#### Expected outcome

Every implementer and reviewer run is attributable to its epic, task and role, and every review carries a post-delivery storypoint measure.

#### Steps

1. List the files under Files plus scripts/lib/agent_usage.py (MARKER), read them in one pass; write AC1 and AC2 tests and run them: they fail.
2. Amend epic-run/SKILL.md and reviewer.md; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 2 points.
- Fix-as-ac (brief, prompt marker): nothing in epic-run/SKILL.md:23-27 puts epic/task in the prompt today; a structure test pins the marker (AC1).
- Depends on agent-discipline (reviewer.md, test_agents_lean.py) and planner-points-gate (Fibonacci scale wording).

- 2026-10-25 done

- 2026-10-25 done

### S18: Stamp actuals

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket_cmds/task_cmd.py`, `plugins/workbench/skills/start-development/tests/test_ticket_task_status.py`, `plugins/workbench/skills/start-development/references/tickets.md`, `plugins/workbench/scripts/lib/agent_usage.py`, `plugins/workbench/scripts/tests/test_agent_usage.py`, `plugins/workbench/skills/epic-run/SKILL.md`, `plugins/workbench/skills/start-development/SKILL.md`, `plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only epic-run && mise run lint`
- Verified head: fb1bd5b

#### Requirement

User requirement (U3, verbatim, the per-task part): "post-delivery complexity measure in storypoints, delivery time (start to finish in minutes), tokens used for each task (including implementation + review)"

User requirement (U4, verbatim, the seamless part): "It must be seamless for the agent (taking over most of the estimation from agent's reasoning)."

Design D11: `ticket.py task <epic> <task> --status done --points-actual N` (N Fibonacci, required with `--status done`) reads the `.logs/agents` records for that epic and task through `agent_usage.read_records` (re-summarising from transcripts that still exist), and `agent_usage.aggregate` stamps `actual_minutes` (first start to last end across the task's agents, ceiling minutes), `actual_tokens` (all agents, all rounds), `actual_roles` (`impl N, review N`, minutes per role, each the sum of that role's agent spans) and `actual_role_tokens` (`impl N, review N`, tokens per role), plus `points_actual`. With no records it stamps `points_actual` only and appends the dated Notes line `actuals: no agent records` (never a guess). `--logs <dir>` overrides the logs dir (default `workbench.logs_dir` of the main checkout). Statuses other than done stamp nothing new. Done epics stay refused. epic-run step 4 and start-development phase 4 step 4 pass `--points-actual <the reviewer's pointsActual>` (SKILL.md line-neutral, at most 150 lines).

#### Acceptance conditions

- AC1: done with two agents' records (impl with a fix round, review) stamps actual_minutes as the ceiling of first start to last end, actual_tokens as the sum, actual_roles, actual_role_tokens and points_actual, and commits [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_task_status.py::test_done_stamps_actuals]
- AC2: `--status done` without `--points-actual`, or with a non-Fibonacci value, exits non-zero and writes nothing [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_task_status.py::test_done_requires_points_actual]
- AC3: with no records, done stamps points_actual and the Notes line `actuals: no agent records`, and leaves minutes and tokens empty [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_task_status.py::test_done_without_records_notes_it]
- AC4: records of other tasks and epics are ignored; escalated stamps no actuals [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_task_status.py::test_stamp_reads_only_its_task]
- AC5: `aggregate` computes span minutes, total tokens and per-role minutes and tokens [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_aggregate]
- AC6: epic-run step 4 passes `--points-actual` from the reviewer's pointsActual [evidence: test:plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py::test_done_passes_points_actual]
- AC7: SKILL.md stays within 150 lines and names `--points-actual` in phase 4 [evidence: test:plugins/workbench/skills/start-development/tests/test_skill_size.py::test_skill_md_within_line_cap]
- AC8: start-development, scripts and epic-run suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only epic-run && mise run lint]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/task_cmd.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_task_status.py`
- `plugins/workbench/skills/start-development/references/tickets.md`
- `plugins/workbench/scripts/lib/agent_usage.py`
- `plugins/workbench/scripts/tests/test_agent_usage.py`
- `plugins/workbench/skills/epic-run/SKILL.md`
- `plugins/workbench/skills/start-development/SKILL.md`
- `plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py`

#### Interfaces

- `ticket.py task <epic> <task> --status <s> [--verified-head <sha>] [--note <text>] [--points-actual N] [--logs DIR]`
- `agent_usage.aggregate(records) -> dict` keys `minutes`, `tokens`, `roles` (`{"impl": (minutes, tokens), "review": (minutes, tokens)}`)
- Frontmatter written: `points_actual`, `actual_minutes`, `actual_tokens`, `actual_roles`, `actual_role_tokens`.

#### Expected outcome

Marking a task done records its measured time and tokens and its post-delivery points with no arithmetic by the orchestrator.

#### Steps

1. List the files under Files, read them in one pass; write AC1-AC6 tests (records written with agent_usage.write_record into a temp logs dir) and run them: they fail.
2. Implement aggregate and the stamping; amend epic-run step 4 and SKILL.md phase 4 step 4 line-neutrally; document in tickets.md; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 5 points.
- Reuse (brief): ticket_cmds/task_cmd.py:run already appends a dated Notes line; ticket.py:_write_task keeps unknown keys; restore `_format_roles` (`impl 2, review 1`) and the span logic of `_run_dir_durations` from `git show 7b187e8 -- plugins/workbench/skills/start-development/scripts/ticket.py` (its Workflow journal input is gone; the input is now `.logs/agents` records).
- Fix-as-ac (brief): done epics are read-only for task edits (task_cmd.py:23); actuals are stamped at `task --status done`, before `move done`.
- Values load as strings; write integers through dump.
- ticket.py already imports workbench from scripts/lib (ticket.py:28-30); import agent_usage the same way.

- 2026-10-25 done

- 2026-10-25 done

### S19: Actuals backfill

- Status: done
- Files: `plugins/workbench/scripts/lib/agent_usage.py`, `plugins/workbench/scripts/tests/test_agent_usage.py`, `plugins/workbench/skills/start-development/scripts/ticket_cmds/task_cmd.py`, `plugins/workbench/skills/start-development/scripts/ticket_cmds/actuals.py`, `plugins/workbench/skills/start-development/tests/test_ticket_task_status.py`, `plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py`, `plugins/workbench/skills/start-development/references/tickets.md`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: ab86c4b

#### Requirement

User requirement (U3, verbatim, the measured part): "delivery time (start to finish in minutes), tokens used for each task (including implementation + review)"

Gate answer Q3 (approved 2026-10-24): add a backfill so stamp-actuals and retro work for runs the hook did not record, this epic included.

Design D16: `plugins/workbench/scripts/lib/agent_usage.py` gains `backfill(transcripts_dir, logs_dir, refresh=False)`. It scans a harness subagent transcript dir (Claude Code: `~/.claude/projects/<project>/<session>/subagents/agent-*.jsonl`; `<project>` derived from the workbench root the way Claude Code derives it, every character that is not a letter or digit replaced by `-`, or the dir passed explicitly) for transcripts whose first user prompt starts with the `[wb <epic>/<task>/<role>]` marker, and writes the missing `.logs/agents/<agentId>.json` records with the same summariser and record format the hook uses (`summarize`, `parse_marker`, `role_for`, `write_record`; agentType from `agent-<id>.meta.json` when present). It never overwrites a record the hook already wrote unless `refresh` is set. Unmarked transcripts are skipped. It returns the records it wrote. `ticket.py task <epic> <task> --status done` runs the backfill for that epic before stamping when `.logs/agents` has no record for the task. A new subcommand `ticket.py actuals <epic> --backfill [--transcripts <dir>] [--refresh]` runs it by hand and prints one line per record written (agentId, epic/task/role, minutes, tokens). The retirement pin's KEPT and KEPT_MODULES gain `actuals` and its module; references/tickets.md documents the subcommand.

#### Acceptance conditions

- AC1: in a fixture dir with a marked and an unmarked transcript, backfill writes one record for the marked agent, with the hook's fields and once-per-message.id tokens, and none for the unmarked one [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_writes_marked_only]
- AC2: running backfill twice writes nothing the second time and leaves an existing hook record untouched [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_is_idempotent]
- AC3: with refresh set, backfill rewrites an existing record from its transcript [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_refresh_overwrites]
- AC4: the default transcripts dir is `~/.claude/projects/<root with every non-alphanumeric character replaced by ->` (home overridable in the test) [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_default_transcripts_dir]
- AC5: `ticket.py task --status done` with no record for the task backfills from `--transcripts` and stamps the actuals [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_task_status.py::test_done_backfills_before_stamping]
- AC6: `ticket.py actuals <epic> --backfill --transcripts <dir>` prints one line per record written and writes nothing on a rerun [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_task_status.py::test_actuals_backfill_command]
- AC7: the retirement pin lists `actuals` and its module and still holds [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py::test_run_loop_commands_retired]
- AC8: scripts and start-development suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

#### Files

- `plugins/workbench/scripts/lib/agent_usage.py`
- `plugins/workbench/scripts/tests/test_agent_usage.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/task_cmd.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/actuals.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_task_status.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py`
- `plugins/workbench/skills/start-development/references/tickets.md`

#### Interfaces

- `agent_usage.backfill(transcripts_dir: Path, logs_dir: Path, refresh: bool = False) -> list[dict]`
- `agent_usage.default_transcripts_dir(root: Path, home: Path | None = None) -> Path`
- `ticket.py actuals <epic> --backfill [--transcripts DIR] [--refresh] [--logs DIR]` (module `ticket_cmds/actuals.py`)
- `ticket.py task ... --status done [--transcripts DIR]` backfills before stamping when the task has no record.

#### Expected outcome

Marked runs the hook missed (this epic's own runs, a session without the plugin loaded) still produce usage records, so actuals and the retro are measured.

#### Steps

1. List the files under Files, read them in one pass; write AC1-AC7 tests with a fixture transcripts dir and run them: they fail.
2. Implement backfill, the default dir helper, the done-path call and the `actuals` subcommand; update the pin and tickets.md; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 2 points.
- Reuse: everything from agent-usage-lib (`transcript_lines`, `summarize`, `parse_marker`, `role_for`, `write_record`, `read_records`); do-not-build a second transcript walker or record writer.
- Hooks brief finding 3: subagent transcripts live at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl` with `agent-{agentId}.meta.json` beside, deleted after `cleanupPeriodDays` (30): backfill before that.
- Project dir naming checked on disk 2026-10-24: `/Users/x/Documents/workbench` is `-Users-x-Documents-workbench` and `.git` becomes `--git`.
- Fix-as-ac (brief, retirement pins): KEPT_MODULES is exact; the module name must not contain `estimate`.
- Tests must not read the real `~/.claude`: pass `--transcripts` or a fake home.

- 2026-10-25 done

- 2026-10-25 done

### S20: Retro command

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket_cmds/retro.py`, `plugins/workbench/skills/start-development/scripts/ticket.py`, `plugins/workbench/skills/start-development/templates/retro.md`, `plugins/workbench/skills/start-development/tests/test_ticket_retro.py`, `plugins/workbench/skills/start-development/tests/test_templates.py`, `plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py`, `plugins/workbench/skills/start-development/references/tickets.md`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: d257ca1

#### Requirement

User requirement (U3, verbatim): "during epic close, add RETRO.md including: tasks table with task title (in delivery order), post-delivery complexity measure in storypoints, delivery time (start to finish in minutes), tokens used for each task (including implementation + review); retro table with what went well, what went bad / could be improved; list of potential improvements in the code or things that were delivered in a different way than expected (include tech-debt if introduced anyway)"

User requirement (U4, verbatim, part): "Task table will be used for future estimates, retro table will be used to propose improvements for future work (also including workflow improvements)."

Design D12: `templates/retro.md` with exactly the H2s Tasks, Deltas, Retro, Improvements (ASCII only). `ticket.py retro <epic>` (main checkout only; epic in in-progress or done) writes the epic's RETRO.md: the Tasks table in delivery order (the git log of `chore(ticket): <epic> task <slug> done` commits, oldest first; tasks with no such commit follow in dependency order) with columns task title, points (estimate), points (post-delivery), minutes (expected), minutes (actual), tokens (expected), tokens (actual), and a totals line; the Deltas section per task (points difference, minutes and tokens actual over expected) and the MdAPE per metric. Missing values read `not recorded`. The generated parts sit between `<!-- retro:generated:begin -->` and `<!-- retro:generated:end -->` markers; a rerun regenerates them and keeps everything else (the Retro and Improvements sections the retro-writer fills). It commits `chore(ticket): <epic> retro`. `ticket.py path <epic> retro` resolves RETRO.md. `ticket.py retro --history [--limit N]` prints, as JSON, the Retro and Improvements sections of the most recent N (default 5) done epics that have a RETRO.md. KEPT and KEPT_MODULES in the retirement pin gain `retro` and `retro.py`. A task whose frontmatter has no actuals takes its minutes and tokens from the `.logs/agents` records of its epic and task (`agent_usage.read_records` and `aggregate`, after the backfill of D16), and its estimate points from a Notes line `Estimate: <n> points` when the `points` key is absent; only when neither exists does a cell read `not recorded`.

#### Acceptance conditions

- AC1: RETRO.md lists the tasks in delivery order from the `task <slug> done` commits, not dependency order, with the seven columns and a totals line [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_tasks_in_delivery_order]
- AC2: the Deltas section shows per-task points difference and minutes and tokens ratios and the MdAPE per metric; a task without actuals reads `not recorded` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_deltas_section]
- AC3: a rerun regenerates the generated block and keeps the hand-written Retro and Improvements sections byte for byte [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_rerun_keeps_written_sections]
- AC4: retro commits exactly RETRO.md as `chore(ticket): <epic> retro` and refuses a linked worktree and a todo epic [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_commit_and_refusals]
- AC5: `ticket.py path <epic> retro` prints the RETRO.md path [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_path_retro]
- AC6: `retro --history --limit 2` prints the Retro and Improvements of the two latest done epics with a RETRO.md as JSON [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_history]
- AC7: templates/retro.md has exactly the H2s Tasks, Deltas, Retro, Improvements and is ASCII [evidence: test:plugins/workbench/skills/start-development/tests/test_templates.py::test_retro_template]
- AC8: the retirement pin lists `retro` in KEPT and `retro.py` in KEPT_MODULES and still holds [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py::test_run_loop_commands_retired]
- AC10: a done task with empty actual fields gets its minutes and tokens from matching `.logs/agents` records and its points from an `Estimate: <n> points` Notes line [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_falls_back_to_records_and_notes]
- AC9: start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/retro.py`
- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/templates/retro.md`
- `plugins/workbench/skills/start-development/tests/test_ticket_retro.py`
- `plugins/workbench/skills/start-development/tests/test_templates.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py`
- `plugins/workbench/skills/start-development/references/tickets.md`

#### Interfaces

- `ticket_cmds/retro.py`: `register(sub, t)`, `run(a, t) -> int`; `ticket.py retro <epic>` and `ticket.py retro --history [--limit N]`.
- `ticket.py:PATH_KINDS["retro"] = "RETRO.md"`.
- `templates/retro.md` H2s: Tasks, Deltas, Retro, Improvements; markers `<!-- retro:generated:begin -->` / `<!-- retro:generated:end -->`.
- Uses `calibration.mdape`.

#### Expected outcome

At close one command writes the measured half of RETRO.md from the task files and the git log, and the history of earlier retros is one command away.

#### Steps

1. List the files under Files plus ticket_cmds/close_cmd.py and task_cmd.py, read them in one pass; write test_ticket_retro.py (temp git repo with done commits in non-dependency order) and the template test; run them: they fail.
2. Implement the module, template and path kind; update the retirement pin and tickets.md; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 8 points.
- Reuse (brief): ticket_cmds/__init__.py contract and _load_cmd_modules (1546), modelled on task_cmd.py and close_cmd.py; resolve_epic (253), _phase_of (267), scan (444), _sections (692), _section_replace (906), _template (332), _render (326), PATH_KINDS (45) plus cmd_path (1512), commit_ticket_change (295), require_main_checkout (285).
- Adopted (brief): delivery order from the git log of `chore(ticket): <epic> task <slug> done` commits that task_cmd.py:36 writes (verified with `git log --grep`).
- Fix-as-ac (brief): KEPT_MODULES is an exact set; REMOVED contains `estimate` (do not name anything that way); RECORD_H2 stays unchanged, retro.md gets its own exact-H2 test; templates are ASCII (test_templates.py:97-103).
- Fix-as-ac (brief): only RETRO.md (like record.md) is written after `move done`; task files are never touched by retro.
- This epic's own tasks carry points only in their Notes (`Estimate: <n> points`) and were marked done by the ticket.py on main, which does not stamp; AC10 covers them through the backfilled `.logs/agents` records (D16).

- 2026-10-25 done

- 2026-10-25 done

### S21: Deltas command

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py`, `plugins/workbench/skills/start-development/tests/test_ticket_deltas.py`, `plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py`, `plugins/workbench/skills/start-development/references/tickets.md`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint`
- Verified head: 2ddf0d0

#### Requirement

User requirement (U4, verbatim): "scripting support getting deltas between complexity/time of delivery/tokens usage per task. New tools are meant to make the estimates more precise with time. Task table will be used for future estimates, retro table will be used to propose improvements for future work (also including workflow improvements). It must be seamless for the agent (taking over most of the estimation from agent's reasoning)."

Design D13: `ticket.py deltas <epic>` prints, per task, estimate against actual for points (points vs points_actual), minutes (expected_minutes vs actual_minutes) and tokens (expected_tokens vs actual_tokens), the differences and actual-over-expected ratios, and the MdAPE per metric over the epic. `ticket.py deltas --all` covers every done epic and adds legacy done tasks that carry numeric `estimate` and `actual` (minutes) as minutes-only rows marked legacy: they count toward the minutes MdAPE, are never bucketed by points and are never written. `ticket.py deltas --buckets` prints `calibration.bucket_table` over the same rows `new-task` uses (points, minutes, tokens, n, source). `--json` prints machine-readable output for every mode. The command is read-only: it writes no file and makes no commit. KEPT and KEPT_MODULES gain `deltas` and `deltas.py`.

#### Acceptance conditions

- AC1: `deltas <epic>` prints one row per task with points, minutes and tokens estimate, actual, difference and ratio, and the MdAPE per metric [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_deltas.py::test_epic_deltas]
- AC2: `deltas --all` spans done epics and includes legacy `estimate`/`actual` tasks as minutes-only rows that are never bucketed [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_deltas.py::test_all_includes_legacy_minutes]
- AC3: `deltas --buckets --json` equals `calibration.bucket_table` over the rows new-task uses [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_deltas.py::test_buckets_match_new_task]
- AC4: deltas writes nothing and commits nothing [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_deltas.py::test_read_only]
- AC5: references/tickets.md documents `deltas` [evidence: command:grep -n "deltas" plugins/workbench/skills/start-development/references/tickets.md]
- AC6: the retirement pin lists `deltas` and `deltas.py` and still holds [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py::test_run_loop_commands_retired]
- AC7: start-development and scripts suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_deltas.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py`
- `plugins/workbench/skills/start-development/references/tickets.md`

#### Interfaces

- `ticket_cmds/deltas.py`: `register(sub, t)`, `run(a, t) -> int`; `ticket.py deltas [<epic> | --all] [--buckets] [--json]`.
- Uses the ticket.py history-rows helper from estimate-fields and `calibration.bucket_table`, `calibration.mdape`.

#### Expected outcome

One read-only command shows how far estimates were off per task, per epic and overall, and the exact table the next `new-task` will use.

#### Steps

1. List the files under Files, read them in one pass; write test_ticket_deltas.py (done epics with fields, a legacy task) and run it: it fails.
2. Implement; update the pin and tickets.md; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 5 points.
- Reuse (brief): ticket.py:scan / _tasks_of for done tasks; calibration.py from calibration-lib. Do-not-build: a regression solver, a frontmatter parser.
- Fix-as-ac (brief, retirement pins): no subcommand named `estimate`; KEPT_MODULES exact.
- History data on disk (brief): 71 done tasks carry legacy `estimate`, 21 carry `actual` (minutes) - the legacy rows of AC2.
- Depends on retro-command only because both edit the retirement pin and tickets.md.

- 2026-10-25 done

- 2026-10-25 done

### S22: Retro writer

- Status: done
- Files: `plugins/workbench/agents/retro-writer.md`, `plugins/workbench/skills/start-development/SKILL.md`, `plugins/workbench/skills/start-development/references/retro.md`, `plugins/workbench/skills/start-development/tests/test_skill_size.py`, `plugins/workbench/skills/start-development/tests/test_templates.py`, `plugins/workbench/agents/planner.md`, `plugins/workbench/skills/start-development/tests/test_planner_agent.py`, `plugins/workbench/README.md`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-research && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint`
- Verified head: 7f31a5a

#### Requirement

User requirement (U3, verbatim): "during epic close, add RETRO.md including: tasks table with task title (in delivery order), post-delivery complexity measure in storypoints, delivery time (start to finish in minutes), tokens used for each task (including implementation + review); retro table with what went well, what went bad / could be improved; list of potential improvements in the code or things that were delivered in a different way than expected (include tech-debt if introduced anyway)"

User requirement (U4, verbatim, part): "retro table will be used to propose improvements for future work (also including workflow improvements). It must be seamless for the agent (taking over most of the estimation from agent's reasoning)."

Design D12: a new `plugins/workbench/agents/retro-writer.md` (model sonnet) runs at start-development phase 7 after `ticket.py retro <epic>`, beside record-writer. Inputs: the epic slug, the orchestrator's notes (per task the review rounds and the reviewer's verification tail, every ruling), and `ticket.py retro --history`. It writes only RETRO.md (`ticket.py path <epic> retro`), keeps the generated block untouched, and fills Retro as a table with the columns "Went well" and "Went bad / could be improved", and Improvements as a list of potential code improvements, things delivered differently than expected, tech debt introduced anyway, and workflow improvement proposals for items that recur in the history. ASCII only, plain hyphens. Phase 7 of start-development/SKILL.md names `ticket.py retro` and retro-writer, with the detail in a new `references/retro.md` (linked from SKILL.md and listed in test_skill_size KEPT), so SKILL.md stays within 150 lines. planner.md reads `ticket.py retro --history` before planning and places the relevant proposals in design.md's Research inputs. The plugin README's phase dispatch table gains the phase 7 retro-writer row.

#### Acceptance conditions

- AC1: retro-writer.md has `model: sonnet`, names its inputs, writes only RETRO.md, keeps the generated block, and names "Went well", "Went bad / could be improved", "delivered differently", "tech debt" and "workflow" improvements from the history; it is ASCII [evidence: test:plugins/workbench/skills/start-development/tests/test_templates.py::test_retro_writer_agent]
- AC2: SKILL.md phase 7 names `ticket.py retro` and retro-writer and links references/retro.md, which is listed in KEPT [evidence: test:plugins/workbench/skills/start-development/tests/test_skill_size.py::test_every_kept_reference_is_linked_from_skill]
- AC3: SKILL.md stays within 150 lines [evidence: test:plugins/workbench/skills/start-development/tests/test_skill_size.py::test_skill_md_within_line_cap]
- AC4: planner.md tells the planner to read `ticket.py retro --history` and place relevant proposals in design.md [evidence: test:plugins/workbench/skills/start-development/tests/test_planner_agent.py::test_planner_reads_retro_history]
- AC5: the plugin README dispatch table has a phase 7 retro-writer row matching SKILL.md [evidence: test:plugins/workbench/skills/start-development/tests/test_release.py::test_readme_dispatch_phases_match_skill]
- AC6: start-development, start-review, start-research and scripts suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-research && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

#### Files

- `plugins/workbench/agents/retro-writer.md`
- `plugins/workbench/skills/start-development/SKILL.md`
- `plugins/workbench/skills/start-development/references/retro.md`
- `plugins/workbench/skills/start-development/tests/test_skill_size.py`
- `plugins/workbench/skills/start-development/tests/test_templates.py`
- `plugins/workbench/agents/planner.md`
- `plugins/workbench/skills/start-development/tests/test_planner_agent.py`
- `plugins/workbench/README.md`

#### Interfaces

- Agent `workbench:retro-writer` (sonnet): input `{epic, notes}`; output RETRO.md only; report at most 100 words.
- `references/retro.md`: when it runs, its inputs, how the history feeds proposals, the bootstrap note.

#### Expected outcome

Every closed epic gets a RETRO.md whose judgement half is written by an agent from evidence, and whose proposals feed the next plan.

#### Steps

1. List the files under Files plus agents/record-writer.md and templates/record.md (the pattern), read them in one pass; write AC1, AC4 and AC5 tests and update KEPT; run them: they fail.
2. Write the agent, the reference, amend SKILL.md phase 7 line-neutrally, planner.md and README; run the verify once.
3. Commit; leave the tree clean.

#### Notes

- Estimate: 5 points.
- Reuse (brief): agents/record-writer.md plus templates/record.md are the pattern for a phase 7 sonnet writer; RETRO.md is written after `move done` like record.md.
- Fix-as-ac (brief): SKILL.md line cap (test_skill_size.py MAX_LINES 150, KEPT exact); test_lean_flow_docs.py:201-217 pins the record-writer phrases (keep them); test_templates.py:97-103 requires ASCII punctuation in templates and writer agents.
- New agents are pinned in skills/start-review/tests/test_agents_lean.py and skills/start-research/tests/test_start_skills_structure.py only by name lists; if one of them enumerates every agent file, update it and say so.
- The planner reads proposals; it never edits ROADMAP.md (human-owned).

- 2026-10-25 done

- 2026-10-25 done

### S23: Plugin readme commands

- Status: done
- Files: `plugins/workbench/README.md`, `plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: e68d094

#### Requirement

Discovered by the stamp-actuals implementer: `plugins/workbench/README.md` line 250 still shows the `ticket.py task ... --status done` command without the now-required `--points-actual N`. Update every `ticket.py` command line in the plugin README that this epic changed or added so the README matches the tool: `new-task` carries `--points <n>`; `task --status done` carries `--points-actual <n>` (and mentions `--logs <dir>` as the test override); the new subcommands `retro`, `deltas` and `actuals` (from tasks retro-command, deltas-command and actuals-backfill) each get one line in the README's ticket.py subcommand list with the same one-line description tickets.md gives them; the hooks table already lists the usage recorder. ASCII only, no em dash. Add a test under `plugins/workbench/skills/start-development/tests/` that pins: every backticked `ticket.py task` span in the README that contains `--status done` also contains `--points-actual`, every backticked `ticket.py new-task` span contains `--points`, and the README names `retro`, `deltas` and `actuals`.

#### Acceptance conditions

- AC1: every README `ticket.py task ... --status done` span carries `--points-actual` and every `ticket.py new-task` span carries `--points` [evidence: test:plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py::test_readme_ticket_commands_match_tool]
- AC2: the README names the subcommands retro, deltas and actuals [evidence: test:plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py::test_readme_names_new_subcommands]
- AC3: the start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

#### Files

- `plugins/workbench/README.md`
- `plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

1. Read `plugins/workbench/README.md` (ticket.py subcommand list and every backticked `ticket.py` span), `references/tickets.md` (the one-line descriptions of retro, deltas, actuals) and the existing `test_plugin_readme_rules.py`.
2. Add the two tests first; run `pytest plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py -q` and see them fail on the stale command lines and the missing subcommand names.
3. Edit the README in one pass; run the verify once and see it green.


Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Estimate: 1 points

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-25 done

- 2026-10-25 done

### S24: Review seams

- Status: done
- Files: `plugins/workbench/scripts/lib/agent_usage.py`, `plugins/workbench/scripts/lib/workbench.py`, `plugins/workbench/skills/start-development/scripts/ticket_cmds/task_cmd.py`, `plugins/workbench/skills/start-development/scripts/ticket_cmds/retro.py`, `plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py`, `plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py`, `plugins/workbench/scripts/tests/test_agent_usage.py`, `plugins/workbench/skills/start-development/tests/test_ticket_deltas.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only epic-run && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint`
- Verified head: f0bdea7

#### Requirement

Two medium findings from the whole-diff review, both confirmed:

1. The "read records, backfill from transcripts when none, read again" sequence is written twice: `ticket_cmds/task_cmd.py` `_actuals` and `ticket_cmds/retro.py` `_fill_from_records`, each resolving `default_transcripts_dir(main)` and calling `agent_usage.backfill` on its own, so the fallback rules can drift. Extract one function in `plugins/workbench/scripts/lib/agent_usage.py` (for example `records_for(epic, task_or_None, logs_dir, transcripts_dir, backfill=True)`) that does the sequence once, and call it from both places; `deltas.py` keeps `backfill=False` through the same function. `deltas.py` `_logs` rebuilds `main / ".logs"` by hand to avoid the mkdir: give `workbench.logs_dir` (or a sibling) a non-creating variant and use it, so one place knows the directory name.
2. The run marker is defined twice: `epic-run/SKILL.md` carries `[wb <epic>/<task>/impl]` and `[wb <epic>/<task>/review]` as prose; `agent_usage.MARKER` is the regex. Add a test (in the epic-run structure tests or scripts tests) that extracts the marker template from the skill text, substitutes a sample epic, task and each role, and asserts `agent_usage.parse_marker` returns that epic, task and role; so editing either side fails a test instead of silently losing attribution.

#### Acceptance conditions

- AC1: one shared records-or-backfill function exists in agent_usage.py and task_cmd.py, retro.py and deltas.py all call it; grep finds no second `backfill(` call site in ticket_cmds [evidence: command:test "$(grep -c 'agent_usage.backfill(\|\.backfill(' plugins/workbench/skills/start-development/scripts/ticket_cmds/task_cmd.py plugins/workbench/skills/start-development/scripts/ticket_cmds/retro.py plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py | awk -F: '{s+=$2} END {print s}')" = "0"]
- AC2: deltas resolves the logs dir through a non-creating workbench.py helper and stays read-only [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_deltas.py::test_read_only]
- AC3: a test builds the marker from the epic-run skill text and parses it with agent_usage.parse_marker for both roles [evidence: test:plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py::test_prompt_marker_parses]
- AC4: the start-development, epic-run and scripts suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only epic-run && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

#### Files

- `plugins/workbench/scripts/lib/agent_usage.py`
- `plugins/workbench/scripts/lib/workbench.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/task_cmd.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/retro.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py`
- `plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py`
- `plugins/workbench/scripts/tests/test_agent_usage.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_deltas.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

1. Read agent_usage.py, workbench.py (`logs_dir`, `_state_dir`), task_cmd.py `_actuals`, retro.py `_fill_from_records`, deltas.py `_logs`, test_epic_run_structure.py `test_prompt_marker`, and the existing tests of the three commands.
2. Write `test_prompt_marker_parses` and a unit test for the shared records-or-backfill function first; run them and see them fail.
3. Extract the function, switch the three call sites, add the non-creating logs resolver, run the verify once after committing (some tests count `git ls-files`).

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Estimate: 2 points

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-25 done

- 2026-10-25 done

## Files to delete

none recorded in the epic format

## Final verify

`mise run test && mise run lint`

## After merge

none
