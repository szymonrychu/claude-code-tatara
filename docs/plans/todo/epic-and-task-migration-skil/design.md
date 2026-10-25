# Epic and task migration skill design

## Summary

A new subcommand `ticket.py migrate` rewrites every epic's task files from the old ticket scheme (minutes
`estimate`, `actual`, run-loop keys) to the scheme epic housekeeping-rules-estimates defined (Fibonacci
`points`, `expected_minutes`, `expected_tokens`, `points_actual`, `actual_minutes`, `actual_tokens`,
`actual_roles`, `actual_role_tokens`), fills actuals from legacy numbers and from the subagent transcripts
still on disk, and writes each done epic's RETRO.md generated block in the same commit. A thin skill,
`epic-migrate`, runs it: dry run, migrate, retro-writer and `ticket.py retro` per epic, then the bucket
table. The epic ends by migrating this repository's six done epics for real, so calibration reads one
scheme and `deltas --all --buckets` leaves the seed table.

## Intent and why

The user asked on 2026-10-25: "Skill to add: migrate epics/tasks from old scheme to new one. Can be
started after current work gets delivered." Calibration (`calibration_rows`) only reads done tasks with
`points` and both actuals; no done task has `points` today (the five old epics predate it, and the
bootstrap epic housekeeping-rules-estimates was planned before the field existed), so every bucket is on
the seed table and RETRO.md exists for one epic only. The housekeeping-rules-estimates retro names this
epic as the removal of that tech debt.

## Goals

- G1: `ticket.py migrate [<epic> | --all] [--dry-run]` rewrites every old-scheme task file in todo,
  in-progress and done epics to the 18 template keys in template order, with points, expected values and
  actuals per D3 and D4, never inventing a value.
- G2: Each done epic gets a RETRO.md: migrate writes its generated block in the epic's one
  `chore(ticket): <epic> migrate` commit, and retro-writer fills Retro and Improvements from record.md.
- G3: A second run changes nothing (idempotent), and a dry run writes and commits nothing.
- G4: A thin `epic-migrate` skill (at most 45 lines) wraps the commands, and the plugin README, the flow
  docs and references/tickets.md name it and `migrate`.
- G5: This repository's six done epics are migrated: `ticket.py lint` prints `lint: ok`,
  `ticket.py deltas --all --buckets` shows at least one bucket with source history or refit, and every
  done epic has a tracked RETRO.md with a filled Retro section.

## Non-goals

- Rewriting approvals.json, rulings.json, record.md, close.json, README.md or design.md of any epic: they
  stay as history.
- Re-estimating old tasks by judgement: points come only from the legacy number or the Notes line (D3).
- Keeping a backward compatible reader for the old keys (deltas legacy rows go, D11).
- Changing the calibration formula or the seed table.

## Anti-goals

- A migrated task with a malformed number that `calibration_rows` then silently drops (D10).
- An actual or a role guessed where no number, no record and no transcript exists.
- Writing or committing anything in a dry run or on a second run.
- A per-task walk of every transcript (O(tasks x transcripts)) when one pass per epic suffices (D6).
- Touching the Retro and Improvements text of a RETRO.md that already has them (the bootstrap epic).

## Constraints

- No em dash characters anywhere; ASCII only in plugin markdown; plain hyphens and straight quotes.
- Python 3.9 safe in hooks and `scripts/lib`; `scripts/lib` is stdlib only, so `agent_usage` cannot import
  ticket.py: the legacy matcher takes a names map from its caller.
- No backward compatibility: migrate is the one path for old files; legacy keys are dropped; no shims.
- Writer rule: only the orchestrator writes tickets, only through ticket.py, only in the main checkout;
  every mutating subcommand calls `require_main_checkout` first and `commit_ticket_change` last.
- Retirement pins: KEPT and KEPT_MODULES in test_ticket_retired_run_loop.py are exact; nothing may be
  named `estimate` or `estimator`; start-development SKILL.md is at 149 of 150 lines; skill wrappers are at
  most 45 lines with frontmatter exactly `name` and `description`.
- TDD: each task is one test file's worth of behaviour, test first.
- Verify commands: `bash plugins/workbench/scripts/run-tests.sh --only <suite>` plus `mise run lint`; the
  full gate is `mise run test` and `mise run lint` (both green on main b947d5b: 1907 assertions).

## Decisions

### D1: One subcommand, one thin skill (Q1)

`ticket.py migrate` lives in a new module `ticket_cmds/migrate.py` (`register(sub, t)`, `run(a, t)`).
`migrate <epic>` migrates one epic, `migrate --all` every epic under todo, in-progress and done (Q1: today
the five old done epics plus the bootstrap epic; the two todo epics have no tasks). `--dry-run` prints
the plan; `--transcripts DIR` and `--logs DIR` override the defaults (`agent_usage.default_transcripts_dir`
of the main checkout, the main checkout's `.logs`). The skill `skills/epic-migrate/SKILL.md` is a thin
wrapper like epic-move. Alternatives: a standalone script (rejected: the writer rule puts every ticket
write in ticket.py); one subcommand per step (rejected: one command keeps the commit shape of D9).

### D2: Task frontmatter shape (Q6)

A migrated task has exactly the 18 keys of templates/task.md in that order (`t._template("task.md")`):
title, status, repo, value, files, verify, depends_on, model, review, verified_head keep their values;
the eight estimate and actual keys are set per D3 and D4 or left `""`. Dropped: estimate, estimate_by,
actual, worktree, branch, run, provides, owns, uses, process_gaps, acs_for_audit, fork_point, and any
other key outside the 18. The body is not changed (my call: the commit message records the migration).
Values are written with `ticket.dump`, so `dump(load(x)) == x` holds.

### D3: Points and expected values (Q2, Q3, Q4 amended)

- A task with a whole-number legacy `estimate` (minutes): `points` is
  `calibration.points_for_minutes(estimate)`, the SEED bucket whose minutes are nearest, ties to the
  smaller bucket (17 minutes is 1 point; 45 is 3; 46 is 5); `expected_minutes` keeps the legacy estimate
  (the planner's real estimate); `expected_tokens` is the SEED tokens of that bucket.
- A task without a legacy estimate but with a Notes line `Estimate: N points` (`retro.NOTES_POINTS`; all
  24 bootstrap tasks): `points` is N, `expected_minutes` and `expected_tokens` are `calibration.SEED[N]`;
  `points_actual` and the existing actuals stay as recorded (one task keeps points 5 against
  points_actual 3).
- Neither: `points`, `expected_minutes` and `expected_tokens` stay empty and the task stays out of
  calibration.
- A task that already has `points` keeps it and its expected values.
The same mapping applies in every phase (my call: Q3's reason, the planner's real estimate, holds for a
todo task too).

### D4: Actuals (Q5)

`actual_minutes` comes from a whole-number legacy `actual`, else from the task's matched records
(`agent_usage.aggregate`); `actual_tokens` and `actual_role_tokens` come only from matched records;
`actual_roles` from matched records. Without a number or a record the field stays empty, never invented.
An existing new-scheme actual is kept. A legacy `actual_roles` value (19 flow-speed-and-token-optimiz
tasks carry the old four-role form, for example `impl 4, verify 3, review 2, fix 2`) is kept when it
names only impl and review, and otherwise folded: `fix` minutes added to impl (fix rounds continue the
implementer) and `verify` minutes to review (the reviewer verifies first); records-derived roles win (my
call; open question Q1 below). An empty legacy value becomes `""`.

### D5: Legacy transcript matcher (Q11)

`agent_usage.legacy_task(path, names)` returns `(epic, task)` for an unmarked transcript whose first user
prompt names exactly one task: a token of `names` (a dict from name to `(epic, task or None)`) found
bounded by non-name characters. The caller (migrate) builds `names` from `<epic>/tasks/<task>.md` for every
task, every `ticket.ticket_names` entry, and each old task's legacy `worktree` basename and `branch`
(read before D2 drops them). An entry mapping to an epic only (the integration tree) or two different
tasks match nothing. `agent_usage.backfill(..., names=None)` writes a record for such a transcript only
when `names` is given and its `agent-<id>.meta.json` agentType is `workbench:implementer` or
`workbench:reviewer` (roles impl and review); planner, merger, auditor, record-writer and general-purpose
transcripts are skipped. A marker still wins over the names. Alternatives: importing ticket.py in
agent_usage (rejected: stdlib-only lib), a fixed regex for the layout (rejected: names already exist in
ticket.py).

### D6: One transcript pass per epic

`agent_usage.records_by_task(epic, logs_dir, transcripts_dir, backfill=True, names=None)` reads the
epic's records once, backfills at most once when a task wanted is missing, reads again once, and returns
`{task: [records]}`. `retro._fill_from_records` uses it instead of `records_for` per task (each empty task
walked every transcript: 23 x 149 for epic-integration-worktrees), and migrate uses it with `names`.
`records_for` stays for the single task of `ticket.py task --status done`.

### D7: Delivery order fallback (Q7)

`retro._delivery_order`: tasks with a `task <slug> done` commit first, oldest first; then the rest by the
committer date of their `verified_head`, oldest first; then the remainder in dependency order. A
`verified_head` that is empty, not a commit, or not a sha at all (`"$(see below)"` in
init-leaves-a-green-tree/license-every-plugin) puts the task in the remainder, never an error.

### D8: RETRO.md for every done epic (Q8)

Migrate writes a done epic's RETRO.md generated block with retro's own functions (`retro._rows`,
`_generated`, `_splice`), creating the file from templates/retro.md when absent and keeping Retro and
Improvements byte for byte when present. It prints `retro-writer: <epic>` for each done epic whose Retro
section is still the template's. The skill then dispatches retro-writer (sonnet) per such epic and reruns
`ticket.py retro <epic>`, which commits the filled file as `chore(ticket): <epic> retro`. Old epics have no
orchestrator notes, so retro-writer gains record.md (and the task Notes) as an input.

### D9: Commit shape, dry run and idempotence (Q9)

Migrate commits once per changed epic, `chore(ticket): <epic> migrate`, with exactly the task files and
RETRO.md it wrote; an epic with nothing to change gets no commit. `--dry-run` prints one line per task it
would change (old and new values of the changed keys, dropped keys) and per RETRO.md it would write,
writes no file, writes no `.logs` record and makes no commit. With nothing to change it prints
`migrate: nothing to change`. A second run over migrated files changes nothing.

### D10: Validate before writing

Every mapped task runs through `t._number_problems`; any problem refuses the epic (exit 1, the problems
listed, nothing written for that epic), because `calibration_rows` silently drops a malformed row.

### D11: deltas legacy rows retired (Q10)

`deltas._legacy` (minutes-only rows from `estimate` and `actual`) and the row's `legacy` flag and
`(legacy)` marker are removed, pinned by a retirement test; migrate is the one path for pre-points tasks.
`test_all_includes_legacy_minutes` is no longer accurate and is replaced by the pin.

### D12: Done epics are history, migrate is the one writer

The lint comment ("a done epic is history: its files are never rewritten") and references/tickets.md say
that only `ticket.py migrate` rewrites a done epic's task files; `ticket.py task` keeps refusing done
epics.

### D13: The real run on this repository (my call; open question Q2 below)

The last task migrates this repository's docs/plans. Since only the orchestrator writes tickets and only
in the main checkout, the orchestrator runs it there with the integration tree's ticket.py
(`python3 <integration tree>/plugins/workbench/skills/start-development/scripts/ticket.py migrate --all
--root <main>/docs/plans`, after the dry run), the same way ticket commits land on main during any epic.
The retro-writer agent type loads only after `/reload-plugins` on main, so each retro-writer step is a
general-purpose sonnet agent told to follow the integration tree's agents/retro-writer.md. The task's
acceptance conditions run against main's docs/plans; its verify is the full `mise run test && mise run
lint`.

## Research

| Lens | Ran or skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| research-code-internal | ran (reuse brief, opus) | load/dump/_template/_number_problems/commit_ticket_change (ticket.py:212,234,339,382,302); retro._rows/_generated/_splice/NOTES_POINTS (ticket_cmds/retro.py); agent_usage summarize/backfill/aggregate/_agent_type (scripts/lib/agent_usage.py); legacy `worktree`/`branch` keys name the exact tree (docs/plans/done/*/tasks); names map from the caller (agent_usage.py:13, stdlib only); Notes "Estimate: N points" over points_actual for the bootstrap epic | jscpd duplicate scan (not installed); a second frontmatter parser or commit helper (ticket.py has both) |
| research-code-external | skipped: a one-off frontmatter migration over our own ticket files has no external analogue worth a survey | - | - |
| research-papers | skipped: no scientific or algorithmic core | - | - |
| research-docs | skipped: no library or platform API used in a new way (stdlib, git, the transcript format documented in housekeeping-rules-estimates) | - | - |

## Research inputs

- Old scheme keys and counts (discovery brief: 74 old tasks over five epics; `estimate` "" in 3; numeric `actual` in flow-speed only) - migrate-dry-run.
- 19 flow-speed tasks carry a four-role `actual_roles` (on-disk grep, this plan) - migrate-dry-run (D4, Q1).
- Bootstrap epic: 24 tasks with actuals, no `points`; Notes `Estimate: N points` on all 24, one differs from points_actual (reuse brief) - migrate-dry-run.
- Transcripts: 149 on disk, 49 marked; unmarked lean-development-flow implementer and reviewer prompts name `in-progress/lean-development-flow/tasks/<task>.md`; epic-integration-worktrees ones are worktree-merger only (discovery brief and an on-disk sample) - legacy-transcript-matcher.
- Unmarked transcripts are skipped, pinned by test_agent_usage.py::test_backfill_writes_marked_only (reuse brief fix-as-ac) - legacy-transcript-matcher.
- retro._fill_from_records walks every transcript per empty task (reuse brief hot spot; housekeeping-rules-estimates retro, tech debt) - retro-records-once.
- Only lean-development-flow has `task <slug> done` commits; every old task has a verified_head, one not a sha (discovery and reuse briefs) - retro-records-once.
- calibration_rows silently drops malformed rows (ticket.py:400, reuse brief) - migrate-dry-run.
- No minutes-to-points inverse exists; tie rule needed (reuse brief) - minutes-to-points.
- deltas._legacy dead after migrate (deltas.py:81, test_ticket_deltas.py:119) - deltas-legacy-retired.
- retro-writer has no record.md input (agents/retro-writer.md:15-22) - retro-writer-record-input.
- Pins: KEPT/KEPT_MODULES, SKILLS dict and 45-line cap, README subcommands and skills, SKILL.md 149/150 lines (reuse brief, test_skill_size.py) - migrate-dry-run, migrate-command, epic-migrate-skill.
- "Done epic is history, never rewritten" in ticket.py lint and tickets.md (reuse brief) - migrate-command.
- Retro history, housekeeping-rules-estimates (workflow): implementers quote lint and suite lines run after `git add` and commit, not a tail read - every task's Notes.
- Retro history, housekeeping-rules-estimates (workflow): a feature with a default path gets one test without the override flag - migrate-command (default dirs).
- Retro history, housekeeping-rules-estimates (workflow): reviewers run the documented command for any README or skill snippet - epic-migrate-skill (flags checked against `--help`).
- Retro history, housekeeping-rules-estimates (tech debt): no `points` on that epic's tasks, remove by this epic - migrate-this-repo.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 One subcommand, one skill | migrate-dry-run, migrate-command, epic-migrate-skill |
| D2 Task frontmatter shape | migrate-dry-run |
| D3 Points and expected values | minutes-to-points, migrate-dry-run |
| D4 Actuals | migrate-dry-run |
| D5 Legacy transcript matcher | legacy-transcript-matcher, migrate-dry-run |
| D6 One transcript pass per epic | retro-records-once |
| D7 Delivery order fallback | retro-records-once |
| D8 RETRO.md for every done epic | migrate-command, retro-writer-record-input, epic-migrate-skill |
| D9 Commit shape, dry run, idempotence | migrate-dry-run, migrate-command |
| D10 Validate before writing | migrate-dry-run |
| D11 deltas legacy rows retired | deltas-legacy-retired |
| D12 Done epics are history | migrate-command |
| D13 The real run | migrate-this-repo |

## Review focus

- Never invented: every planned and actual value traces to a legacy number, a Notes line, a record or
  SEED; check the empty cases in migrate-dry-run's tests.
- Idempotence and dry run: no write, no `.logs` record and no commit on a dry run or a second run.
- Byte-for-byte keeps: title through verified_head, the task body, RETRO.md Retro and Improvements, and
  every side file.
- The matcher's skip rules (no task, two tasks, epic-only tree, non implementer/reviewer types).
- Delivery order with a non-sha verified_head.

## Left to the builder

- The dry run line format, as long as it names the epic, the task, each changed key with old and new
  value, and each dropped key.
- How the token-bounded match is written in `legacy_task`, within D5's rules.
- Whether `records_for` is rewritten on top of `records_by_task`, keeping its signature and behaviour.

## Assumptions and unknown facts

- Transcripts for flow-speed, init, template-update and most epic-integration-worktrees agents are gone
  (the harness deletes them after about 30 days); those tasks get tokens `""`. Confirmed by the dry run in
  migrate-this-repo.
- Old verified_head shas are still in the object store (merged); a missing one falls back per D7.
- After migration the bootstrap epic gives at least 5 calibration rows, so buckets leave the seed;
  confirmed by migrate-this-repo's AC.

## Open questions

none
- Q1: Old four-role actual_roles (19 flow-speed tasks, e.g. 'impl 4, verify 3, review 2, fix 2'): fold fix into impl and verify into review instead of dropping them, since no transcripts survive for that epic? [recommended: yes, fold; records-derived roles still win (D4)]

## Irreversible operations in scope

none: the real run rewrites done task files and RETRO.md on main in per-epic `chore(ticket): <epic>
migrate` and `retro` commits, each revertible with `git revert`; the dropped legacy keys stay in git
history. `.logs/agents` records it writes are gitignored and regenerable.
