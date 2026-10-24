# Housekeeping rules, estimates and retrospectives design

## Summary

Four flow improvements in one meta-mode epic over the workbench repo. A new plugin rule file carries the user's
housekeeping rules into every AGENTS.md; the em dash rule is enforced by a tracked-file lint and by the
protect-files and guard-bash hooks; `.scratchpad` and `.logs` in the main checkout become the only scratch and log
locations. Every task gains storypoints plus expected minutes and tokens (the planner gives only the points; the tool
fills the rest from calibration history). A Claude-only SubagentStart/SubagentStop hook records per-agent time and
tokens under `.logs/agents`, `ticket.py task --status done` stamps the actuals, `ticket.py retro` plus a
`retro-writer` agent write RETRO.md at close, and `ticket.py deltas` reports estimate against actual and feeds the
next estimates.

## Intent and why

The user wants agents that do not guess, do not tamper with tests, do not narrow scope and do not scatter files, and
wants estimates that come from measurement instead of reasoning. Today a task has no size, no expected cost and no
recorded cost, so nothing improves between epics. The user's words (U1-U4) are binding and quoted verbatim in the
task requirements.

## Goals

The epic README Goals G1-G7 are the checkable goals; every task maps to one or more of them.

## Non-goals

- The user's private global CLAUDE.md or any file outside this repository (C10).
- Pricing tokens in currency (C10).
- Backward compatibility shims for task files of done epics: they are read as they are, never rewritten (C10).
- A new orchestration loop: epic-run changes only by the prompt marker, `--points-actual` and the retro step.
- Mechanical enforcement of "the supervisor never writes code" or "do not guess": these stay rule text (see D2).

## Anti-goals

- A red main: every task keeps `mise run lint` and its suites green.
- A hook that blocks or crashes a subagent stop because a transcript is missing or garbled.
- A second frontmatter parser, commit helper, tracked-file walker, workbench-root resolver or transcript walker
  (reuse brief, do-not-build).
- Reviving the retired `ticket.py estimate`, `estimator.py` or the epic `## Time` line.

## Constraints

- Hooks entry scripts are Python 3.9 safe (`from __future__ import annotations`, no 3.10+ syntax, no tomllib).
- start-development/SKILL.md stays at most 150 lines; AGENTS.md stays under 24000 bytes and in sync with
  `mise run harness-setup` (lint:harness).
- Templates and agent files are ASCII only (test_repo_hygiene, test_templates).
- Retirement pins hold: no subcommand or key named `estimate`, no file named `*estimator*`, KEPT_MODULES is exact.
- Done epics are read-only for task edits; only RETRO.md (like record.md) is written after `move done`.
- Bootstrap exception (my call): this epic's own tasks are planned before `--points` exists, so each carries
  `Estimate: <n> points` in its Notes, and the gate shows the seed-table minutes and tokens for those points. The new
  hooks and ticket.py load from the main checkout only after the epic merges, so this epic's actuals are not captured;
  its RETRO.md shows them as "not recorded" and its points come from the Notes.

## Decisions

### D1: Housekeeping rules live in a new rule file in the generated rules block (my call)

`plugins/workbench/rules/housekeeping.md` states every U1 rule verbatim in substance; `RULE_FILES` in
`scripts/harness/agents_md.py` gains it, and `mise run harness-setup` regenerates AGENTS.md in the same task.
Existing statements are amended for consistency, not duplicated: AGENTS.md ground rules 3 and the writing conventions,
`references/non-negotiables.md` (orchestrate, do not implement). Alternatives: a CLAUDE.md-only rule (Claude only,
rejected), restating in every agent (drift, rejected).

### D2: The discipline in agent texts, reconciled with TDD (my call, gate Q1)

"Run tests once" reads: list every file the step touches, read them all in one pass, make all edits for the step,
then run the targeted verify once per red or green step; never an edit-run-edit-run dribble. implementer.md and
reviewer.md carry it (planner.md too, for its own reading and for what it plans), the test-tampering rule gains "xfail" and the exception "unless the test itself is no longer
accurate (say which and why)", the reviewer treats an unrequested compatibility shim as a finding, and an agent unsure
of a fact returns it in a `questions` field instead of guessing (the orchestrator asks the user or fable). Supervisor
only and "do not guess" stay rule text: no hook can tell a supervisor edit from a planning edit reliably.

### D3: Em dash lint over every tracked file (C2a)

A thin entry point `scripts/check_em_dash.py` over `check_personal._tracked` and `_text` reports `path:line` for
U+2014 in any tracked text file, with no allow list; `mise-tasks/lint/em-dash` runs it, picked up by `lint:*`. The one
literal in scripts/tests/test_agents_md.py:107 becomes the escape `"\u2014"`. Alternative: a denylist entry in
personal-denylist.json, rejected because whole-file allows there (docs/plans/**, init_engine) would exempt files.

### D4: Em dash edit guard rides protect-files (my call)

`core.protect_files` also denies an edit or write whose new content contains U+2014: Write `content`, Edit
`new_string`, MultiEdit `edits[].new_string`, NotebookEdit `new_source`, and the added lines of a Codex
`apply_patch`. Content is read from `event.raw["tool_input"]`; `harness_io.normalize` stores the normalised tool
input under that Claude-named key so every harness that already emits protect-files gets the guard. Alternative: a
new hook name, rejected because every harness target keeps an explicit allowlist and would need a new entry.

### D5: Em dash commit guard in guard-bash (C2c)

When any normalised segment of a Bash command matches `^git\s+commit\b` and the whole command contains U+2014, deny;
this covers `-m`, a heredoc and `$(cat <<EOF)` because heredoc lines are segments of the same command. `-F <file>` and
`--file=<file>`: the guard reads the file (relative to the event cwd) when it exists and denies on U+2014.

### D6: Main checkout, `.scratchpad` and `.logs` (C3)

`workbench.py` gains `main_checkout(start)` (WORKBENCH_ROOT, then CLAUDE_PROJECT_DIR, else the parent of the
absolute `git rev-parse --git-common-dir`, never an integration tree), `scratchpad_dir` and `logs_dir`, and CLI
actions `scratchpad` and `logs` that print (and create) the directory. `.scratchpad/` joins `.gitignore` beside
`.logs/`. Every skill, agent and script that names a scratch or log location names these two: run-tests.sh and
flake-hunt.sh logs, the bash-output-filter spill file, start-debugging's pristine copy, kubectl-logs-query, the
planner. Transient temp files a script creates and removes within one run (suite lock, gitleaks staging, the plugin
load probe) are neither scratchpads nor logs and stay where they are (my call); a tree-wide pin test lists them.

### D7: Estimate fields on every task (C5)

Task frontmatter appends, after `verified_head`: `points`, `expected_minutes`, `expected_tokens`, `points_actual`,
`actual_minutes`, `actual_tokens`, `actual_roles`, `actual_role_tokens`. `new-task --points N` (Fibonacci 1, 2, 3, 5,
8, 13; required) is the planner's only input; `expected_minutes` and `expected_tokens` are filled by calibration
(D8). `ticket.py lint` checks that points fields are Fibonacci and minutes and tokens are non-negative integers when
set, and that every task of a todo or in-progress epic has `points`. `ticket.py tasks` JSON carries the three
estimate fields so the gate table shows them. `actual_roles` keeps the legacy format `impl N, review N` (minutes);
`actual_role_tokens` is the matching tokens field.

### D8: Calibration library (C9)

`plugins/workbench/scripts/lib/calibration.py`, stdlib only, restores `_solve`, `refit` and `mdape` from
`git show 7b187e8^:plugins/workbench/scripts/lib/estimator.py` with points as the regressor. `expected(points, rows)`:
the median of done tasks with that `points` and both actuals when there are at least 3; else the linear refit over
all rows when there are at least 5 (my call); else the seed table (D15). `bucket_table(rows)` returns the per-points
table with `n` and `source` (history, refit, seed). Rows are plain dicts; ticket.py collects them from done tasks.

### D9: Per-agent usage records (C6)

`plugins/workbench/scripts/lib/agent_usage.py` (stdlib, 3.9 safe) owns the record: a tolerant transcript line
iterator (shared with `core.collect_worktrees`), `summarize(transcript)` (first and last timestamp, model, tokens
summed once per `message.id`, falling back to `requestId`, with input, cache_creation, cache_read and output kept and
their total), the marker parser, and `write_record`/`read_records`/`aggregate`. `hooks/agent-usage-recorder.py`
runs on SubagentStart (records start time, agent id, type, derived transcript path) and SubagentStop (recomputes from
the whole transcript and overwrites `.logs/agents/<agentId>.json` atomically). An empty `agent_type` writes nothing;
any error exits 0 with no output. Tokens are input + cache_creation + cache_read + output (brief finding 4).

### D10: Prompt marker and post-delivery points (C6, C7)

epic-run step 2 starts every implementer and reviewer prompt with the fixed line `[wb <epic>/<task>/<role>]`, role
`impl` or `review`; fix rounds continue the same agent id, so the same record grows. Role comes from the marker, and
from `agentType` (`workbench:implementer`, `workbench:reviewer`) when the marker is missing (my call). The reviewer
reports `pointsActual` (the post-delivery Fibonacci points, judged from the diff it reviewed) in its final report.

### D11: Stamping actuals at done (C7)

`ticket.py task <epic> <task> --status done --points-actual N` reads the `.logs/agents` records for that epic and
task, re-summarising each from its transcript when the file still exists, and stamps `actual_minutes` (first start to
last stop across its agents, ceiling minutes), `actual_tokens` (all agents, all rounds), `actual_roles`,
`actual_role_tokens` and `points_actual`. With no records it stamps the points and writes the dated Notes line
"actuals: no agent records" instead of numbers (never a guess). `--logs <dir>` overrides the logs dir for tests.

### D12: Retro at close (C8)

`templates/retro.md` with H2s Tasks, Deltas, Retro, Improvements. `ticket.py retro <epic>` writes RETRO.md's Tasks
table (delivery order from the git log of `chore(ticket): <epic> task <slug> done` commits; title, points estimate and
actual, minutes estimate and actual, tokens estimate and actual), the totals line and the Deltas section between
generated markers, keeping the hand-filled sections on a rerun, and commits `chore(ticket): <epic> retro`.
`ticket.py path <epic> retro` resolves RETRO.md. `ticket.py retro --history [--limit N]` prints the Retro and
Improvements sections of earlier done epics as JSON. A new `retro-writer` agent (sonnet) fills Retro (went well; went
bad / could be improved) and Improvements (code improvements, things delivered differently than expected, tech debt
introduced anyway, and workflow improvement proposals for items recurring in the history) from the reviewer tails,
rulings and deltas, keeping the generated parts. It runs at phase 7 beside record-writer; detail lives in
`references/retro.md` so SKILL.md stays within 150 lines. The planner reads `ticket.py retro --history` and places
relevant proposals in design.md.

### D13: Deltas report (C9)

`ticket.py deltas <epic>` prints per task estimate against actual for points, minutes and tokens, the ratios and the
MdAPE per metric; `--all` covers every done epic, adding legacy done tasks with numeric `estimate` and `actual` as
minutes-only rows (never written, never bucketed by points); `--buckets` prints the per-points table `new-task`
uses; `--json` for machines. The name avoids `estimate` (retirement pin).

### D14: Hooks per harness (my call)

agent-usage-recorder is Claude-only: every harness target keeps an explicit hook allowlist and none lists it, and a
root test pins that. The em dash edit guard and commit guard ride protect-files and guard-bash, which copilot, codex,
gemini, cursor and antigravity already emit, so they apply in every harness.

### D15: Seed table (my call, gate Q2)

Until a points bucket has 3 samples and the history has 5, expected values come from a seed table in
calibration.py, derived from a probe of this machine's transcripts on 2026-10-24 (implementer median 29 min and
1.87M tokens over 10 agents, reviewer median 4.8 min and 0.38M tokens over 15 agents: a task about 34 min and 2.25M
tokens) taken as 3 points and scaled linearly: 1: 11 min, 0.75M; 2: 23 min, 1.5M; 3: 34 min, 2.25M; 5: 57 min,
3.75M; 8: 91 min, 6.0M; 13: 147 min, 9.75M.

## Research

| Lens | Ran or skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| research-code-internal | ran (reuse brief) | restore refit/_solve/mdape (7b187e8^ estimator.py); legacy `actual_roles` format (7b187e8 ticket.py `_format_roles`); role from `agent-<id>.meta.json` agentType (transcript dir); delivery order from `task <slug> done` commits (task_cmd.py:36) | reviving `ticket.py estimate` or `## Time` (pinned retired, test_ticket_retired_run_loop.py); reviving hook-evidence.py or claude_json.py parsers (test_retired_verifier.py:11) |
| research-docs | ran (Claude Code hooks brief) | record at SubagentStart and overwrite at every SubagentStop, re-read transcript paths at stamp time (hooks.md, sub-agents.md) | OTel counters with query_source=subagent (needs a collector; monitoring-usage docs) |
| research-code-external | skipped: internal tooling over our own ticket files, no external analogue worth a fork | - | - |
| research-papers | skipped: no algorithmic core beyond a restored least-squares fit | - | - |

## Research inputs

- Transcripts repeat a message.id with identical usage (on-disk check, reuse brief fix-as-ac) - agent-usage-lib.
- SubagentStop refires after a commit-guard block and every fix round (reuse brief) - agent-usage-lib, agent-usage-hook.
- SubagentStop fires for internal agents with empty agent_type (hooks brief finding 1) - agent-usage-hook.
- The Agent tool result has no usage for background agents (hooks brief finding 5) - agent-usage-lib.
- An integration tree can pass `_is_metarepo` (workbench.py:45) - workbench-dirs.
- NormalizedEvent carries no Write/Edit content (core.py:38) - em-dash-edit-guard.
- guard_segments splits heredocs into lines (core.py:214, 230) - em-dash-commit-guard.
- Retirement pins: REMOVED has `estimate`, KEPT_MODULES exact, no `estimator` file, planner.md must not say `ticket.py estimate` - calibration-lib, retro-command, deltas-command, planner-points-gate.
- LEAN_KEYS exact (test_ticket_files.py:161) - estimate-fields.
- RECORD_H2 exact and ASCII templates (test_templates.py) - retro-command, retro-writer.
- SKILL.md at 150 of 150 lines (test_skill_size.py) - planner-points-gate, stamp-actuals, retro-writer.
- `.scratchpad/` not gitignored (reuse brief) - workbench-dirs.
- Hooks are 3.9 safe (test_py39_safe.py) - agent-usage-hook.
- Lint cannot validate numbers (values load as strings) - estimate-fields.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 Housekeeping rule file | housekeeping-rules |
| D2 Agent discipline and TDD | agent-discipline |
| D3 Em dash lint | em-dash-lint |
| D4 Em dash edit guard | em-dash-edit-guard |
| D5 Em dash commit guard | em-dash-commit-guard |
| D6 Scratchpad and logs | workbench-dirs, output-spill-to-logs, test-logs-dir, scratch-locations |
| D7 Estimate fields | estimate-fields, points-required, planner-points-gate |
| D8 Calibration library | calibration-lib, estimate-fields |
| D9 Usage records | agent-usage-lib, agent-usage-hook |
| D10 Marker and points actual | run-marker-points |
| D11 Stamping | stamp-actuals |
| D12 Retro | retro-command, retro-writer |
| D13 Deltas | deltas-command |
| D14 Hooks per harness | agent-usage-hook, em-dash-edit-guard |
| D15 Seed table | calibration-lib |

## Review focus

- agent-usage-lib and agent-usage-hook: once-per-message.id sums, idempotent overwrite, fail-open on every error,
  main-checkout `.logs` from inside a worktree.
- em-dash-edit-guard: protect-files fails closed; a content check must not turn a malformed payload into an allow or
  an unrelated deny.
- estimate-fields and stamp-actuals: values load as strings; numbers are validated, never trusted.
- retro-command: a rerun regenerates only the generated parts and keeps the retro-writer's sections.

## Left to the builder

- Internal helper names and module layout inside the named files, within the interfaces in each task.
- The exact wording of rule and agent text, as long as every U1 rule is stated and the pinned phrases hold.
- Table formatting of RETRO.md and the deltas report, within the named columns.

## Assumptions and unknown facts

- Whether `agent-<id>.meta.json` exists at the first SubagentStop is unknown; the role falls back to the marker, so
  nothing depends on it (probe in agent-usage-hook's tests with and without meta.json).
- Whether SubagentStop fires again on a SendMessage resume is undocumented; the overwrite-from-whole-transcript design
  is correct either way, and stamp-actuals re-summarises from the transcript path.
- The seed table rests on 25 agents of this machine's history (D15); calibration replaces it as epics close.

- Builder check (my call): the supervisor-only rule exempts the orchestrator's own duties, named in housekeeping.md:
  ticket and plan files through `ticket.py` (and design.md, record.md directly), running the repo's test and lint
  commands to read results, and the git operations of close (rebase, fast-forward) through `ticket.py close`. It
  never edits source, tests, skills, agents, hooks or docs outside `docs/plans/`, and never builds.
- Builder check (my call): the commit guard reads a `-F <file>` or `--file=<file>` message relative to the event cwd;
  `-F -` (stdin) and a file that does not exist yet are out of its scope and pass, stated in the rule's docstring.
- Builder check (fact, probed 2026-10-24): `git ls-files | xargs grep -l U+2014` finds exactly one tracked file,
  scripts/tests/test_agents_md.py:107 (a literal in a banned-character list), so em-dash-lint goes green by turning
  that literal into an escape; no other rewrite is needed.

## Open questions

- Q1: 'Run tests once' (U1) is read together with TDD as: list every file, read them all in one pass, make all edits for the step, then run the targeted verify once per red step and once per green step (never an edit-run-edit-run dribble). Accept this reading? [answer: yes, approved at the gate 2026-10-24: one targeted verify run per red step and per green step]
- Q2: Seed table for expected minutes and tokens until history has 3 samples per points bucket (and 5 overall): 1pt 11 min 0.75M, 2pt 23 min 1.5M, 3pt 34 min 2.25M, 5pt 57 min 3.75M, 8pt 91 min 6.0M, 13pt 147 min 9.75M tokens, derived from this machine's implementer and reviewer transcripts (median task taken as 3 points, scaled linearly). Accept? [answer: yes, approved at the gate 2026-10-24: the seed table stands until history has 3 samples per bucket]
- Q3: This epic's own runs happen before the usage hook loads from main, so its actuals would be 'not recorded'. Add one small task: the epic-run prompts carry the [wb ...] marker from now on, and agent-usage-lib gains a backfill that scans the harness's subagent transcript dir for marked prompts and writes the missing .logs/agents records, so stamp-actuals and retro work for this epic too [recommended: yes; one extra sonnet task (2 points), and the first RETRO.md carries real numbers instead of 'not recorded']

## Irreversible operations in scope

none
