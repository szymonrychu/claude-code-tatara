---
title: Migrate dry run
status: todo
repo: workbench
value: The exact old-to-new mapping of every task is computed and shown before anything is written
files: [plugins/workbench/skills/start-development/scripts/ticket_cmds/migrate.py, plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py, plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [legacy-transcript-matcher, minutes-to-points, retro-records-once]
model: opus
review: ""
verified_head: ""
points: 8
expected_minutes: 91
expected_tokens: 6000000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Migrate dry run

## Requirement

User request (verbatim, 2026-10-25): "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered."

User decision (verbatim): "Q1 Scope: every epic under docs/plans (todo, in-progress, done); today that is the five old done epics plus the bootstrap epic housekeeping-rules-estimates; the two todo epics have no tasks yet."

User decision (verbatim): "Q2 Points for old tasks: nearest calibration.SEED bucket to the legacy `estimate` minutes (ties go to the smaller bucket); a task without a numeric legacy estimate gets no points and stays out of calibration."

User decision (verbatim): "Q3 Expected values for old tasks: expected_minutes keeps the legacy estimate (the planner's real estimate), expected_tokens is the SEED tokens of the derived bucket."

User decision (verbatim): "Q4 amended (my call, from the reuse hunt): the bootstrap epic's `points` comes from each task's Notes line "Estimate: N points" (present on all 24 tasks; one differs from points_actual, 5 vs 3), not from points_actual; expected_minutes/expected_tokens := SEED of that bucket; points_actual stays as recorded."

User decision (verbatim): "Q5 Actuals for old tasks: actual_minutes from legacy numeric `actual`, else from matched transcripts; actual_tokens and roles only from matched transcripts (first prompt names the task file or the task worktree; role from meta.json agentType); otherwise absent, never invented."

User decision (verbatim): "Q6 Legacy keys dropped from task frontmatter: estimate, estimate_by, actual, actual_roles (old empty form), worktree, branch, run, provides, owns, uses, process_gaps, acs_for_audit, fork_point. approvals.json and rulings.json stay untouched as history."

User decision (verbatim): "Q11 (my call): the legacy transcript matcher skips transcripts that name no task (planner, merger, auditor, record-writer); only implementer and reviewer agent types count, mapped to impl and review."

Design D1: One subcommand, one thin skill (Q1) (verbatim):

`ticket.py migrate` lives in a new module `ticket_cmds/migrate.py` (`register(sub, t)`, `run(a, t)`).
`migrate <epic>` migrates one epic, `migrate --all` every epic under todo, in-progress and done (Q1: today
the five old done epics plus the bootstrap epic; the two todo epics have no tasks). `--dry-run` prints
the plan; `--transcripts DIR` and `--logs DIR` override the defaults (`agent_usage.default_transcripts_dir`
of the main checkout, the main checkout's `.logs`). The skill `skills/epic-migrate/SKILL.md` is a thin
wrapper like epic-move. Alternatives: a standalone script (rejected: the writer rule puts every ticket
write in ticket.py); one subcommand per step (rejected: one command keeps the commit shape of D9).

Design D2: Task frontmatter shape (Q6) (verbatim):

A migrated task has exactly the 18 keys of templates/task.md in that order (`t._template("task.md")`):
title, status, repo, value, files, verify, depends_on, model, review, verified_head keep their values;
the eight estimate and actual keys are set per D3 and D4 or left `""`. Dropped: estimate, estimate_by,
actual, worktree, branch, run, provides, owns, uses, process_gaps, acs_for_audit, fork_point, and any
other key outside the 18. The body is not changed (my call: the commit message records the migration).
Values are written with `ticket.dump`, so `dump(load(x)) == x` holds.

Design D3: Points and expected values (Q2, Q3, Q4 amended) (verbatim):

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

Design D4: Actuals (Q5) (verbatim):

`actual_minutes` comes from a whole-number legacy `actual`, else from the task's matched records
(`agent_usage.aggregate`); `actual_tokens` and `actual_role_tokens` come only from matched records;
`actual_roles` from matched records. Without a number or a record the field stays empty, never invented.
An existing new-scheme actual is kept. A legacy `actual_roles` value (19 flow-speed-and-token-optimiz
tasks carry the old four-role form, for example `impl 4, verify 3, review 2, fix 2`) is kept when it
names only impl and review, and otherwise folded: `fix` minutes added to impl (fix rounds continue the
implementer) and `verify` minutes to review (the reviewer verifies first); records-derived roles win (my
call; open question Q1 below). An empty legacy value becomes `""`.

Design D5: Legacy transcript matcher (Q11) (verbatim):

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

Design D9: Commit shape, dry run and idempotence (Q9) (verbatim):

Migrate commits once per changed epic, `chore(ticket): <epic> migrate`, with exactly the task files and
RETRO.md it wrote; an epic with nothing to change gets no commit. `--dry-run` prints one line per task it
would change (old and new values of the changed keys, dropped keys) and per RETRO.md it would write,
changes no tracked file and makes no commit; like `ticket.py retro`, it may backfill the gitignored
`.logs/agents` cache (my call: the records are regenerable and the dry run must show transcript actuals).
With nothing to change it prints `migrate: nothing to change`. A second run over migrated files changes
nothing.

Design D10: Validate before writing (verbatim):

Every mapped task runs through `t._number_problems` before anything is written; any problem refuses the
run (exit 1, the problems listed, nothing written in any epic; my call: all or nothing keeps the commit
history simple), because `calibration_rows` silently drops a malformed row.

Constraint (verbatim): "No backward compatibility: migrate is the one path for old files; drop legacy keys; no shims."

Constraint (verbatim, part): "migrate.py added to KEPT and KEPT_MODULES in test_ticket_retired_run_loop.py"

## Acceptance conditions

- AC1: an old-scheme task maps to exactly the 18 keys of templates/task.md in template order; title, status, repo, value, files, verify, depends_on, model, review and verified_head keep their values; estimate, estimate_by, actual, worktree, branch, run, provides, owns, uses, process_gaps, acs_for_audit, fork_point and any other extra key are dropped; the body is unchanged [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_keys_order_and_drops]
- AC2: a whole-number legacy `estimate` gives points `calibration.points_for_minutes(estimate)`, expected_minutes the estimate and expected_tokens the SEED tokens of that bucket; an empty or non-numeric estimate leaves all three empty [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_points_from_legacy_estimate]
- AC3: a task without a legacy estimate whose Notes say `Estimate: N points` gets points N and expected minutes and tokens `calibration.SEED[N]`, keeping points_actual and its actuals as recorded (points 5 with points_actual 3 stays so) [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_points_from_notes_line]
- AC4: a task that already has points keeps points, expected_minutes and expected_tokens [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_existing_points_kept]
- AC5: actual_minutes comes from a whole-number legacy `actual`, else from the task's matched records (`agent_usage.aggregate`); actual_tokens, actual_roles and actual_role_tokens only from records; with neither they stay empty; existing new-scheme actuals are kept [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_actuals_from_legacy_and_records]
- AC6: a legacy actual_roles of `""` stays `""`, `impl N, review N` is kept, and one naming verify or fix folds fix into impl and verify into review (`impl 4, verify 3, review 2, fix 2` becomes `impl 6, review 5`); roles from records win [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_legacy_roles_folded]
- AC7: the names map holds `<epic>/tasks/<task>.md` for every task, every `ticket_names` entry, and each old task's legacy worktree basename and branch; a transcript naming any of them gives that task its records through `records_by_task(..., names=...)` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_names_map_matches_legacy_transcripts]
- AC8: a mapped task with any `_number_problems` refuses the run: exit 1, the problems on stderr, nothing written in any epic [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_malformed_mapping_refused]
- AC9: `migrate --all --dry-run` prints, per task it would change, the epic, the task, each changed key with old and new value and each dropped key, and per done epic the RETRO.md it would write; no tracked file changes and HEAD does not move [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_dry_run_changes_nothing]
- AC10: when every task is already in the new scheme the dry run prints `migrate: nothing to change` and exits 0 [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_dry_run_nothing_to_change]
- AC11: the retirement pin lists `migrate` in KEPT and `migrate.py` in KEPT_MODULES and still holds [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py::test_run_loop_commands_retired]
- AC12: the start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/migrate.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
