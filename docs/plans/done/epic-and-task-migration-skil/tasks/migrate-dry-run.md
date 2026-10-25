---
title: Migrate dry run
status: done
repo: workbench
value: The exact old-to-new mapping of every task is computed and shown before anything is written
files: [plugins/workbench/skills/start-development/scripts/ticket_cmds/migrate.py, plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py, plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [legacy-transcript-matcher, minutes-to-points, retro-records-once]
model: opus
review: ""
verified_head: 494d702
points: 8
expected_minutes: 91
expected_tokens: 6000000
points_actual: 8
actual_minutes: 11
actual_tokens: 3197775
actual_roles: "impl 9, review 3"
actual_role_tokens: "impl 2978332, review 219443"
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
- A task that already has `points` keeps it and any expected value it has; an empty `expected_minutes`
  or `expected_tokens` is filled from `calibration.SEED[points]` (my call, builder check Q5).
The same mapping applies in every phase (my call: Q3's reason, the planner's real estimate, holds for a
todo task too).

Design D4: Actuals (Q5; interrogate items 3 and 4) (verbatim):

`actual_minutes` comes from a whole-number legacy `actual`, else from the task's matched records
(`agent_usage.aggregate`). `actual_tokens`, `actual_roles` and `actual_role_tokens` come only from
matched records, and only when those records cover both roles, impl and review; a partial match (one
role only) leaves all three empty, gives no `actual_minutes` from records either (my call: a one-role
span understates the task), and the dry run prints `partial: <epic>/<task> (<roles found>)`. A legacy
`actual_minutes` from `actual` is still written for a partial match. Without a number or a full record set
the field stays empty, never invented. Every legacy `actual_roles` value is dropped: the old taxonomy
(impl, verify, review, fix, and one `false-finding` in medium-only-hold) has no mapping that is not a
guess, and its sums disagree with `actual` in 2 tasks (interrogate item 3; open question Q1). A task
with no legacy key (the bootstrap epic) keeps its new-scheme actuals as recorded.

Design D5: Legacy transcript matcher (Q11; interrogate item 2) (verbatim):

`agent_usage.legacy_task(path, names)` returns `(epic, task)` for an unmarked transcript whose first user
prompt names one task, matching tokens of `names` (a dict from name to `(epic, task or None)`) bounded by
non-name characters. Precedence: exactly one task file path (`<epic>/tasks/<task>.md`) named wins; else
exactly one tree or branch name of a task; else, or when ambiguous (two tasks at the same level, or only
an epic name), no match and no record. The caller (migrate) builds `names` only from
`<epic>/tasks/<task>.md` for every task, every `ticket.ticket_names` entry, and each old task's legacy
`worktree` basename and `branch` (read before D2 drops them) when that value contains both the epic slug
and the task slug; never `HEAD` (4 old tasks carry `branch: HEAD`), an empty string or free text.
`agent_usage.backfill(..., names=None)` writes a record for such a transcript only when `names` is given
and its `agent-<id>.meta.json` agentType is `workbench:implementer` (role impl), `workbench:reviewer`
(review) or `workbench:verifier` (review: the old verifier did the review's verification); every other
agent type (planner, merger, auditor, record-writer, general-purpose) is skipped. A marker still wins over
the names. backfill's rglob already reaches the workflow transcripts under
`<session>/subagents/workflows/wf_*/` (887 of the 1042 on disk, each with a meta.json). Alternatives:
importing ticket.py in agent_usage (rejected: stdlib-only lib), a fixed regex for the layout (rejected:
names already exist in ticket.py).

Design D9: Commit shape, write order, dry run and idempotence (Q9; interrogate item 5) (verbatim):

`migrate --all` covers every epic in every phase, this epic included (builder check Q4); a file already in
the new scheme is left alone. Per changed epic, the new task frontmatter is computed first, the RETRO.md
rows are computed from those new values (not from the old files), and then both are written and
committed together, once per changed epic, `chore(ticket): <epic> migrate`, with exactly the task files and
RETRO.md it wrote; an epic with nothing to change gets no commit. So `ticket.py retro <epic>` right after
migrate regenerates the same block, and migrate after that prints `migrate: nothing to change`.
`--dry-run` prints every problem first (D10), then one line per task it would change (old and new values
of the changed keys, dropped keys), each `partial:` line (D4) and each RETRO.md it would write; it changes
no tracked file and makes no commit; like `ticket.py retro`, it may backfill the gitignored `.logs/agents`
cache (my call: the records are regenerable and the dry run must show transcript actuals). With nothing to
change it prints `migrate: nothing to change`. A second run over migrated files changes nothing.

Design D10: Validate before writing (verbatim):

Every mapped task runs through `t._number_problems` before anything is written; any problem refuses the
run (exit 1, every problem listed, nothing written in any epic; my call, kept after builder check Q3: all
or nothing keeps the commit history simple, the dry run lists every problem first, and dropping legacy
`actual_roles` (D4) removes the only known offender), because `calibration_rows` silently drops a
malformed row.

Constraint (verbatim): "No backward compatibility: migrate is the one path for old files; drop legacy keys; no shims."

Constraint (verbatim, part): "migrate.py added to KEPT and KEPT_MODULES in test_ticket_retired_run_loop.py"

## Acceptance conditions

- AC1: an old-scheme task maps to exactly the 18 keys of templates/task.md in template order; title, status, repo, value, files, verify, depends_on, model, review and verified_head keep their values; estimate, estimate_by, actual, worktree, branch, run, provides, owns, uses, process_gaps, acs_for_audit, fork_point and any other extra key are dropped; the body is unchanged [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_keys_order_and_drops]
- AC2: a whole-number legacy `estimate` gives points `calibration.points_for_minutes(estimate)`, expected_minutes the estimate and expected_tokens the SEED tokens of that bucket; an empty or non-numeric estimate leaves all three empty [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_points_from_legacy_estimate]
- AC3: a task without a legacy estimate whose Notes say `Estimate: N points` gets points N and expected minutes and tokens `calibration.SEED[N]`, keeping points_actual and its actuals as recorded (points 5 with points_actual 3 stays so) [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_points_from_notes_line]
- AC4: a task that already has points keeps points and any expected value it has; an empty expected_minutes or expected_tokens is filled from `calibration.SEED[points]` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_existing_points_kept]
- AC5: actual_minutes comes from a whole-number legacy `actual`, else from the task's records when they cover both impl and review; actual_tokens, actual_roles and actual_role_tokens come only from records covering both roles; a partial match (one role) leaves those three and records-derived minutes empty (a legacy `actual` is still written) and the dry run prints `partial: <epic>/<task> (<roles found>)`; with neither source the fields stay empty; a task with no legacy key keeps its new-scheme actuals [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_actuals_from_legacy_and_records]
- AC6: every legacy actual_roles value of a task carrying legacy keys is dropped (`impl 4, verify 3, review 2, fix 2`, `impl 8, review 8`, one with `false-finding`, and `""`): actual_roles is `""` unless records covering both roles give it [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_legacy_roles_dropped]
- AC7: the names map holds `<epic>/tasks/<task>.md` for every task, every `ticket_names` entry, and each old task's legacy worktree basename and branch only when the value contains both the epic slug and the task slug; a transcript naming any of them gives that task its records through `records_by_task(..., names=...)` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_names_map_matches_legacy_transcripts]
- AC8: `branch: HEAD`, an empty worktree or branch, and free text never enter the names map, so a transcript naming `HEAD` gets no task [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_names_map_rejects_head_and_free_text]
- AC9: a mapped task with any `_number_problems` refuses the run: exit 1, every problem on stderr before anything else, nothing written in any epic [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_malformed_mapping_refused]
- AC10: `migrate --all --dry-run` covers todo, in-progress and done epics and prints, per task it would change, the epic, the task, each changed key with old and new value and each dropped key, each `partial:` line, and per done epic the RETRO.md it would write; no tracked file changes and HEAD does not move [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_dry_run_changes_nothing]
- AC11: when every task is already in the new scheme the dry run prints `migrate: nothing to change` and exits 0 [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py::test_dry_run_nothing_to_change]
- AC12: the retirement pin lists `migrate` in KEPT and `migrate.py` in KEPT_MODULES and still holds [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py::test_run_loop_commands_retired]
- AC13: the start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/migrate.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py`

## Interfaces

- `skills/start-development/scripts/ticket_cmds/migrate.py`: `register(sub, t)`, `run(a, t) -> int`; `ticket.py migrate [<epic>] [--all] [--dry-run] [--transcripts DIR] [--logs DIR]` (`--root` comes from the module facade). An epic and `--all` together, or neither, exit 1.
- `migrate_meta(t, meta: dict, body: str, records: list[dict]) -> dict`: the new frontmatter in template order (pure; no I/O).
- `names_map(t, root: Path) -> dict[str, tuple[str, str | None]]`: built before any key is dropped.
- Uses `agent_usage.records_by_task` (task retro-records-once), `agent_usage.aggregate`, `calibration.points_for_minutes` (task minutes-to-points), `calibration.SEED`, `retro.NOTES_POINTS`, `t._template("task.md")`, `t._number_problems`, `t._format_roles`, `t.ticket_names`, `t._task_files`, `t._read_doc`.
- Without `--dry-run`, this task's `run` exits 1 with `migrate: writing lands with the write path; pass --dry-run`; task migrate-command replaces that with the write path.

## Expected outcome

`ticket.py migrate --all --dry-run` shows the exact new frontmatter of every old-scheme task in every phase, with values traced to a legacy number, a Notes line, a record or SEED, and changes nothing tracked.

## Steps

1. List the files: the three under Files plus ticket.py, ticket_cmds/retro.py, ticket_cmds/deltas.py, scripts/lib/agent_usage.py, scripts/lib/calibration.py, templates/task.md, ticket_repo_helpers.py and test_ticket_deltas.py (for the `edit(drop=)` fixture); read them in one pass.
2. Write test_ticket_migrate_map.py (old-scheme fixtures copied from the shapes in docs/plans/done/*/tasks, a bootstrap-style task with only a Notes line, a transcripts dir with a lean-development-flow style prompt) and the pin change; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_migrate_map.py skills/start-development/tests/test_ticket_retired_run_loop.py -q`: they fail.
3. Implement migrate.py; run the verify once.
4. `git add`, commit, rerun the verify and quote its summary lines.

## Notes

- Estimate: 8 points: a new command module with the whole mapping (keys, points, expected, actuals, roles, names, validation) and eleven tests.
- Reuse (reuse brief): load, dump, Doc, _read_doc (ticket.py:212,234,137,523); _template("task.md") key order (ticket.py:339, templates/task.md:1-20); _task_files, _tasks_of, scan (ticket.py:805,1018,527); _points, _count, _format_roles, _number_problems (ticket.py:353,344,378,382); calibration.SEED and POINTS; ticket_names and LEGACY_SEP (ticket.py:544,40); retro._estimate_points and NOTES_POINTS (retro.py:105,28); records to actual_* mapping as in task_cmd._actuals (task_cmd.py:53-63): call the same aggregate and _format_roles, do not copy the block.
- Do not build (reuse brief): a frontmatter parser or writer (load, dump), a commit helper (commit_ticket_change), a record writer or summariser (agent_usage), a worktree-name splitter (ticket_names).
- Fix-as-ac (reuse brief): calibration_rows silently drops malformed rows (ticket.py:400), hence AC8.
- Old shapes on disk: `estimate` is minutes (5, 6, 8 for formula estimates; 45 to 90 for overrides; `""` in 3 tasks); numeric `actual` only in flow-speed-and-token-optimiz; 19 flow-speed tasks carry a four-role actual_roles; housekeeping-rules-estimates has actuals and Notes `Estimate: N points` but no `points`.
- `_parse_roles` rejects verify and fix, so fold the legacy value with its own small parser before formatting it with `_format_roles`.
- Open question Q1 in design.md (fold versus drop of four-role values) is answered at the gate; the AC encodes the recommended fold.
- Retro lesson (housekeeping-rules-estimates): quote the lint and suite lines of a run made after `git add` and commit, never a tail read.

- 2026-10-25 amended: interrogate items 2-4 and builder answers Q3-Q5: legacy actual_roles dropped in every form (supersedes the fold notes and the Q1 note above; no fold parser needed), tokens and roles only from records covering impl and review with partial lines, names map filtered (no HEAD, empty or free text), SEED fill for empty expected values, every problem listed first, --all covers every phase; points stay 8

- 2026-10-25 done
