# Epic and task migration skill implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: Legacy transcript matcher

- Status: done
- Files: `plugins/workbench/scripts/lib/agent_usage.py`, `plugins/workbench/scripts/tests/test_agent_usage.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint`
- Verified head: a408f1e

#### Requirement

User request (verbatim, 2026-10-25): "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered."

User decision (verbatim): "Q5 Actuals for old tasks: actual_minutes from legacy numeric `actual`, else from matched transcripts; actual_tokens and roles only from matched transcripts (first prompt names the task file or the task worktree; role from meta.json agentType); otherwise absent, never invented."

User decision (verbatim): "Q11 (my call): the legacy transcript matcher skips transcripts that name no task (planner, merger, auditor, record-writer); only implementer and reviewer agent types count, mapped to impl and review."

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

Constraint (verbatim): "Python 3.9 safe in hooks and scripts/lib; stdlib only in scripts/lib (agent_usage cannot import ticket.py, so the legacy matcher takes a names map from its caller)."

Reuse brief fix-as-ac (verbatim): "unmarked skipped - AU:257; pinned by test_agent_usage.py:293 - update test, keep no-task transcripts skipped"

Interrogate verdict item 2 (verbatim): "Only task file paths, ticket_names entries and worktree or branch names that contain both the epic and the task slug enter the map; never HEAD, empty strings or free text. Precedence: exactly one task file path wins, else exactly one tree name, else skipped; an ambiguous prompt never gets a record."

Interrogate verdict item 3 (verbatim, part): "workbench:verifier transcripts count as role review, implementer as impl, reviewer as review, every other agent type skipped."

#### Acceptance conditions

- AC1: `agent_usage.legacy_task(path, names)` matches tokens of `names` bounded by non-name characters with this precedence: exactly one task file path (`<epic>/tasks/<task>.md` under any phase dir) wins, even when a tree name of another task is also named; else exactly one task tree or branch name (`<epic>--<task>`, `<epic>-<task>`); a prompt naming only an epic name, no name, or two different tasks at the deciding level returns None [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_legacy_task_matches_one_task]
- AC2: `backfill(transcripts, logs, names=names)` writes a record for an unmarked transcript that `legacy_task` matches and whose `agent-<id>.meta.json` agentType is `workbench:implementer` (role impl), `workbench:reviewer` (review) or `workbench:verifier` (review), with epic and task from the match and the same summariser and record shape as a marked one; with `epic=` set, other epics' matches are skipped [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_matches_legacy_transcripts]
- AC3: unmarked transcripts that name no task or an ambiguous set, and matched ones of any other agent type (worktree-merger, general-purpose, planner, scope-auditor, record-writer) or with no meta.json, are skipped [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_skips_unmatched_and_other_types]
- AC4: a matched transcript under `<session>/subagents/workflows/wf_<id>/agent-<id>.jsonl` with its meta.json beside it is reached and recorded like one directly under `subagents/` [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_reaches_workflow_transcripts]
- AC5: test_backfill_writes_marked_only is updated, not weakened: its fixture gains an unmarked implementer transcript naming a task file, and without `names` only the marked record is written, as before [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_writes_marked_only]
- AC6: a marked transcript keeps its marker's epic, task and role even when its prompt also names another task of `names` [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_marker_wins_over_names]
- AC7: agent_usage imports no ticket module (stdlib plus workbench only) [evidence: command:! grep -nE '^\s*(import|from)\s+ticket' plugins/workbench/scripts/lib/agent_usage.py]
- AC8: the scripts suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

#### Files

- `plugins/workbench/scripts/lib/agent_usage.py`
- `plugins/workbench/scripts/tests/test_agent_usage.py`

#### Interfaces

- `agent_usage.legacy_task(path: str | os.PathLike, names: dict[str, tuple[str, str | None]]) -> tuple[str, str] | None` (plugins/workbench/scripts/lib/agent_usage.py).
- `agent_usage.backfill(transcripts_dir, logs_dir, refresh=False, epic=None, names=None) -> list[dict]`: new keyword `names`; `None` keeps today's marked-only behaviour.
- Record shape unchanged: agentId, agentType, transcript, updatedAt, start, end, model, epic, task, role, tokens.

#### Expected outcome

Given a names map, backfill writes `.logs/agents` records for the old epics' implementer and reviewer transcripts that name one task (lean-development-flow's name their task files); without one, nothing changes.

#### Steps

1. Read agent_usage.py and test_agent_usage.py in one pass. Write the four new tests and the fixture change; run `cd plugins/workbench && pytest scripts/tests/test_agent_usage.py -q`: the new tests fail (no `legacy_task`, no `names` keyword).
2. Implement `legacy_task` and the `names` path in `backfill`; run the verify once: `bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint`.
3. `git add`, commit, rerun the verify and quote the `[lint:*]` and suite summary lines from that run.

#### Notes

- Estimate: 3 points: one lib function plus a keyword on backfill, four tests in one file.
- Reuse (reuse brief): parse_marker, _first_text, transcript_lines, _agent_type, role_for, summarize, write_record (agent_usage.py:107,96,45,231,121,69,128); AGENT_ROLES maps the two agent types to impl and review; fixtures usage, assistant, user, write, backfill_fixture (test_agent_usage.py:12,22,32,43,269).
- Do not build (reuse brief): a summariser or record writer (summarize, write_record); a worktree-name splitter (ticket.ticket_names lives in ticket.py; the caller, migrate, builds `names` with it).
- Real prompt shapes (on-disk sample of ~/.claude/projects/-Users-szymonri-Documents-workbench): lean-development-flow implementers and reviewers name `.../docs/plans/in-progress/lean-development-flow/tasks/<task>.md` plus the epic tree `.claude/worktrees/lean-development-flow` (epic only, which matches nothing alone); the epic-integration-worktrees transcripts naming `worktrees/epic-integration-worktrees--<task>` are all worktree-merger, so skipped.
- The phase dir varies (in-progress at run time, done now), so `names` holds `<epic>/tasks/<task>.md` without the phase.
- Stdlib only and Python 3.9 safe (hooks import agent_usage).
- Retro lesson (housekeeping-rules-estimates): quote the lint and suite lines of a run made after `git add` and commit, never a tail read.

- 2026-10-25 amended: interrogate items 1-3: match precedence (task file path, then one tree name), workbench:verifier counts as review, workflow transcripts under <session>/subagents/workflows/wf_*/ (887 of 1042) covered by new AC4; Steps now mean five new tests; points stay 3

- 2026-10-25 done

### S2: Minutes to points

- Status: done
- Files: `plugins/workbench/scripts/lib/calibration.py`, `plugins/workbench/scripts/tests/test_calibration.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint`
- Verified head: 77abb7a

#### Requirement

User request (verbatim, 2026-10-25): "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered."

User decision (verbatim): "Q2 Points for old tasks: nearest calibration.SEED bucket to the legacy `estimate` minutes (ties go to the smaller bucket); a task without a numeric legacy estimate gets no points and stays out of calibration."

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

Reuse brief idea (verbatim): "noted: no minutes-to-bucket inverse exists; tie rule needed (nearest SEED minutes)"

#### Acceptance conditions

- AC1: `calibration.points_for_minutes(m)` returns the SEED bucket whose minutes are nearest m, ties to the smaller bucket: 0, 5, 6, 11 and 17 give 1; 23 gives 2; 45 gives 3; 46 and 57 give 5; 90 gives 8; 120 and 500 give 13 [evidence: test:plugins/workbench/scripts/tests/test_calibration.py::test_points_for_minutes_nearest_seed]
- AC2: a negative number, a bool or a non-int raises ValueError [evidence: test:plugins/workbench/scripts/tests/test_calibration.py::test_points_for_minutes_rejects]
- AC3: the scripts suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

#### Files

- `plugins/workbench/scripts/lib/calibration.py`
- `plugins/workbench/scripts/tests/test_calibration.py`

#### Interfaces

- `calibration.points_for_minutes(minutes: int) -> int`, one of `calibration.POINTS` (plugins/workbench/scripts/lib/calibration.py); stdlib, Python 3.9 safe.

#### Expected outcome

One tested function maps a legacy minutes estimate to its storypoints bucket; migrate (task migrate-dry-run) uses it.

#### Steps

1. Read calibration.py and test_calibration.py. Write the two tests; run `cd plugins/workbench && pytest scripts/tests/test_calibration.py -q`: they fail (no function).
2. Implement over `SEED` and `POINTS`; run the verify once: `bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint`.
3. `git add`, commit, rerun the verify and quote its summary lines.

#### Notes

- Estimate: 1 point: one pure function and a table test.
- Reuse (reuse brief): calibration.SEED and POINTS (calibration.py:19,14).
- The name must not contain `estimate`: the retirement pin in test_ticket_retired_run_loop.py forbids the `estimate` subcommand and any `estimator` file.

- 2026-10-25 done

### S3: Retro writer record input

- Status: done
- Files: `plugins/workbench/agents/retro-writer.md`, `plugins/workbench/skills/start-development/references/retro.md`, `plugins/workbench/skills/start-development/tests/test_templates.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: e91ee9a

#### Requirement

User request (verbatim, 2026-10-25): "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered."

User decision (verbatim): "Q8 RETRO.md for every old done epic: `ticket.py retro <epic>` for the measured tables, retro-writer (sonnet) fills Retro and Improvements from record.md and the deltas; the skill runs this per epic."

Design D8: RETRO.md for every done epic (Q8) (verbatim):

Migrate writes a done epic's RETRO.md generated block with retro's own functions (`retro._rows`,
`_generated`, `_splice`), creating the file from templates/retro.md when absent and keeping Retro and
Improvements byte for byte when present. It prints `retro-writer: <epic>` for each done epic whose Retro
section is still the template's. The skill then dispatches retro-writer (sonnet) per such epic and reruns
`ticket.py retro <epic>`, which commits the filled file as `chore(ticket): <epic> retro`. Old epics have no
orchestrator notes, so retro-writer gains record.md (and the task Notes) as an input.

Reuse brief fix-as-ac (verbatim): "retro-writer has no record.md input - agents/retro-writer.md:15-22 - add it"

#### Acceptance conditions

- AC1: retro-writer's "Inputs you are given" names the epic's record.md as an input and says that for an epic with no orchestrator notes (one migrated by `ticket.py migrate`) record.md and the task files' Notes stand in for them [evidence: test:plugins/workbench/skills/start-development/tests/test_templates.py::test_retro_writer_agent]
- AC2: references/retro.md's Bootstrap section says epics closed before RETRO.md existed get one through the epic-migrate skill: `ticket.py migrate` writes the generated block, retro-writer fills it from record.md, `ticket.py retro <epic>` commits it [evidence: test:plugins/workbench/skills/start-development/tests/test_templates.py::test_retro_reference]
- AC3: both files stay ASCII with no em dash, en dash, smart quote or arrow [evidence: test:plugins/workbench/skills/start-development/tests/test_templates.py::test_plain_ascii_punctuation]
- AC4: the start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

#### Files

- `plugins/workbench/agents/retro-writer.md`
- `plugins/workbench/skills/start-development/references/retro.md`
- `plugins/workbench/skills/start-development/tests/test_templates.py`

#### Interfaces

- agents/retro-writer.md "## Inputs you are given": a record.md bullet; Limits unchanged (record.md is read with Read, not Bash).
- references/retro.md "## Bootstrap": the migrated-epic path.

#### Expected outcome

retro-writer can fill a migrated epic's Retro and Improvements from its record.md when no orchestrator notes exist, and the reference says how old epics get a RETRO.md.

#### Steps

1. Read agents/retro-writer.md, references/retro.md and test_templates.py in one pass. Add the needles to test_retro_writer_agent and test_retro_reference; run `cd plugins/workbench && pytest skills/start-development/tests/test_templates.py -q`: they fail.
2. Edit the two docs; run the verify once.
3. `git add`, commit, rerun the verify and quote its summary lines.

#### Notes

- Estimate: 2 points: two prose edits pinned by needles in one test file.
- Fix-as-ac (reuse brief): "retro-writer has no record.md input - agents/retro-writer.md:15-22 - add it".
- Old epics have record.md (all five) but no orchestrator notes and no rulings beyond rulings.json; record.md is where their review rounds and rulings were written.
- Keep test_retro_writer_agent's existing needles; add, do not replace.

- 2026-10-25 done

### S4: Retro records once

- Status: done
- Files: `plugins/workbench/scripts/lib/agent_usage.py`, `plugins/workbench/skills/start-development/scripts/ticket_cmds/retro.py`, `plugins/workbench/skills/start-development/tests/test_ticket_retro.py`, `plugins/workbench/skills/start-development/references/tickets.md`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint`
- Verified head: 816af0c

#### Requirement

User request (verbatim, 2026-10-25): "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered."

User decision (verbatim): "Q7 Delivery order for epics without `task <slug> done` commits: by the commit date of each task's verified_head (retro fallback), then dependency order for the rest."

Design D6: One transcript pass per epic (verbatim):

`agent_usage.records_by_task(epic, logs_dir, transcripts_dir, backfill=True, names=None)` reads the
epic's records once, backfills at most once when a task wanted is missing, reads again once, and returns
`{task: [records]}`. `retro._fill_from_records` uses it instead of `records_for` per task (each empty task
walked every transcript: 23 x 1042 for epic-integration-worktrees, 1042 transcripts being on disk), and migrate uses it with `names`.
`records_for` stays for the single task of `ticket.py task --status done`.

Design D7: Delivery order fallback (Q7) (verbatim):

`retro._delivery_order`: tasks with a `task <slug> done` commit first, oldest first; then the rest by the
committer date of their `verified_head`, oldest first; then the remainder in dependency order. A
`verified_head` that is empty, not a commit, or not a sha at all (`"$(see below)"` in
init-leaves-a-green-tree/license-every-plugin) puts the task in the remainder, never an error.

Reuse brief fix-as-ac (verbatim): "hot spot: retro._fill_from_records calls records_for per task (C/retro.py:139-142); each empty task triggers a full rglob+parse of every transcript (AU:254,302): O(tasks x transcripts), 23x149 for epic-integration-worktrees. Index once per epic."

Correction (interrogate item 1): 1042 transcripts are on disk (887 under <session>/subagents/workflows/wf_*/), so the cost is 23 x 1042.

Reuse brief fix-as-ac (verbatim): "verified_head \"$(see...\" non-sha - done/init-leaves-a-green-tree/tasks/license-every-plugin.md - fallback tolerates it"

housekeeping-rules-estimates RETRO.md, Tech debt (verbatim): "retro backfills per empty task (up to N transcript walks): lives in retro command; remove by a single transcript pass shared across tasks. Accepted at review."

#### Acceptance conditions

- AC1: `agent_usage.records_by_task(epic, logs_dir, transcripts_dir, backfill=True, names=None)` returns `{task: [records]}` for the epic, reading the logs once, backfilling at most once (only when a wanted task has no record) and reading again once; `backfill=False` or no transcripts dir only reads; `names` passes through to `backfill` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_records_by_task_one_pass]
- AC2: `ticket.py retro` over an epic whose three tasks have no records parses each transcript's marker at most once (one backfill per epic, not one per task) and fills the same minutes and tokens as before [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_retro_walks_transcripts_once]
- AC3: tasks with no `task <slug> done` commit follow the delivered ones by the committer date of their verified_head, oldest first, before the remaining tasks in dependency order [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_delivery_order_falls_back_to_verified_head]
- AC4: a verified_head that is empty, an unknown sha, or not a sha at all (`"$(see below)"`) puts its task with the dependency-ordered rest, and retro exits 0 [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_delivery_order_tolerates_non_sha_verified_head]
- AC5: the existing delivery order test still passes unchanged: done commits win over verified_head dates [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_tasks_in_delivery_order]
- AC6: the existing records and Notes fallback test still passes unchanged [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_falls_back_to_records_and_notes]
- AC7: references/tickets.md's `retro` entry names the verified_head fallback and the one transcript pass per epic [evidence: command:awk '/^- `retro`:/,/^- `deltas`:/' plugins/workbench/skills/start-development/references/tickets.md | grep -q 'verified_head']
- AC8: the start-development and scripts suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

#### Files

- `plugins/workbench/scripts/lib/agent_usage.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/retro.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_retro.py`
- `plugins/workbench/skills/start-development/references/tickets.md`

#### Interfaces

- `agent_usage.records_by_task(epic: str, logs_dir, transcripts_dir, backfill: bool = True, names: dict | None = None) -> dict[str, list[dict]]` (plugins/workbench/scripts/lib/agent_usage.py), next to `records_for`.
- `ticket_cmds/retro.py`: `_fill_from_records` calls `records_by_task` once per epic; `_delivery_order(t, root, epic, slugs, deps)` gains the verified_head step (it needs each task's verified_head; pass it in from `_rows`).
- `records_for` keeps its signature and behaviour (ticket.py task --status done uses it for one task).
- deltas keeps calling `retro._rows(..., backfill=False)`: read-only, never backfills.

#### Expected outcome

`ticket.py retro` walks the transcripts at most once per epic, and an epic with no `task <slug> done` commits lists its tasks in the order their work was verified.

#### Steps

1. Read agent_usage.py, ticket_cmds/retro.py, test_ticket_retro.py and references/tickets.md in one pass. Write the four new tests; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_retro.py -q`: they fail.
2. Implement `records_by_task`, switch `_fill_from_records` to it, add the verified_head step to `_delivery_order`, update tickets.md; run the verify once.
3. `git add`, commit, rerun the verify and quote its summary lines.

#### Notes

- Estimate: 5 points: a lib helper, two retro changes, four git-fixture tests with dated commits.
- Hot spot (reuse brief): `retro._fill_from_records` calls `records_for` per task (retro.py:139-142), and each empty task triggers a full rglob and parse of every transcript (agent_usage.py:254,302): O(tasks x transcripts), 23 x 149 for epic-integration-worktrees. housekeeping-rules-estimates retro, tech debt: "remove by a single transcript pass shared across tasks".
- Reuse (reuse brief): retro._git_lines (retro.py:83), ticket.dependency_order (ticket.py:809), agent_usage.read_records and backfill.
- Commit date: check the value against `[0-9a-f]{4,40}` before handing it to git (never pass an option-like string), then `git show -s --format=%ct <sha>`; a non-zero exit means unknown. The non-sha case is real: docs/plans/done/init-leaves-a-green-tree/tasks/license-every-plugin.md has `verified_head: "$(see below)"`.
- Test hint for AC2: drive `ticket.main([...])` in-process with `agent_usage.parse_marker` monkeypatched to count calls; set commit dates with `GIT_COMMITTER_DATE` for AC3.
- Fixtures (reuse brief): repo and root (conftest), mk_epic, mk_task, set_meta, commit_all (ticket_repo_helpers.py:36,45,96,83); setup_epic in test_ticket_retro.py.
- Retro lesson (housekeeping-rules-estimates): quote the lint and suite lines of a run made after `git add` and commit, never a tail read.

- 2026-10-25 amended: interrogate item 1: 1042 transcripts on disk, not 149; the Notes cost figure reads 23 x 1042, not 23 x 149; ACs unchanged

- 2026-10-25 done

### S5: Migrate dry run

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket_cmds/migrate.py`, `plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py`, `plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: 494d702

#### Requirement

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

#### Acceptance conditions

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

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/migrate.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_migrate_map.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py`

#### Interfaces

- `skills/start-development/scripts/ticket_cmds/migrate.py`: `register(sub, t)`, `run(a, t) -> int`; `ticket.py migrate [<epic>] [--all] [--dry-run] [--transcripts DIR] [--logs DIR]` (`--root` comes from the module facade). An epic and `--all` together, or neither, exit 1.
- `migrate_meta(t, meta: dict, body: str, records: list[dict]) -> dict`: the new frontmatter in template order (pure; no I/O).
- `names_map(t, root: Path) -> dict[str, tuple[str, str | None]]`: built before any key is dropped.
- Uses `agent_usage.records_by_task` (task retro-records-once), `agent_usage.aggregate`, `calibration.points_for_minutes` (task minutes-to-points), `calibration.SEED`, `retro.NOTES_POINTS`, `t._template("task.md")`, `t._number_problems`, `t._format_roles`, `t.ticket_names`, `t._task_files`, `t._read_doc`.
- Without `--dry-run`, this task's `run` exits 1 with `migrate: writing lands with the write path; pass --dry-run`; task migrate-command replaces that with the write path.

#### Expected outcome

`ticket.py migrate --all --dry-run` shows the exact new frontmatter of every old-scheme task in every phase, with values traced to a legacy number, a Notes line, a record or SEED, and changes nothing tracked.

#### Steps

1. List the files: the three under Files plus ticket.py, ticket_cmds/retro.py, ticket_cmds/deltas.py, scripts/lib/agent_usage.py, scripts/lib/calibration.py, templates/task.md, ticket_repo_helpers.py and test_ticket_deltas.py (for the `edit(drop=)` fixture); read them in one pass.
2. Write test_ticket_migrate_map.py (old-scheme fixtures copied from the shapes in docs/plans/done/*/tasks, a bootstrap-style task with only a Notes line, a transcripts dir with a lean-development-flow style prompt) and the pin change; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_migrate_map.py skills/start-development/tests/test_ticket_retired_run_loop.py -q`: they fail.
3. Implement migrate.py; run the verify once.
4. `git add`, commit, rerun the verify and quote its summary lines.

#### Notes

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

### S6: Migrate command

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket_cmds/migrate.py`, `plugins/workbench/skills/start-development/tests/test_ticket_migrate.py`, `plugins/workbench/skills/start-development/scripts/ticket.py`, `plugins/workbench/skills/start-development/references/tickets.md`, `plugins/workbench/README.md`, `plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: b92409c

#### Requirement

User request (verbatim, 2026-10-25): "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered."

User decision (verbatim): "Q1 Scope: every epic under docs/plans (todo, in-progress, done); today that is the five old done epics plus the bootstrap epic housekeeping-rules-estimates; the two todo epics have no tasks yet."

User decision (verbatim): "Q8 RETRO.md for every old done epic: `ticket.py retro <epic>` for the measured tables, retro-writer (sonnet) fills Retro and Improvements from record.md and the deltas; the skill runs this per epic."

User decision (verbatim): "Q9 Commit shape: one `chore(ticket): <epic> migrate` commit per epic (task files and RETRO.md), the skill run is idempotent (a second run changes nothing)."

Design D1: One subcommand, one thin skill (Q1) (verbatim):

`ticket.py migrate` lives in a new module `ticket_cmds/migrate.py` (`register(sub, t)`, `run(a, t)`).
`migrate <epic>` migrates one epic, `migrate --all` every epic under todo, in-progress and done (Q1: today
the five old done epics plus the bootstrap epic; the two todo epics have no tasks). `--dry-run` prints
the plan; `--transcripts DIR` and `--logs DIR` override the defaults (`agent_usage.default_transcripts_dir`
of the main checkout, the main checkout's `.logs`). The skill `skills/epic-migrate/SKILL.md` is a thin
wrapper like epic-move. Alternatives: a standalone script (rejected: the writer rule puts every ticket
write in ticket.py); one subcommand per step (rejected: one command keeps the commit shape of D9).

Design D8: RETRO.md for every done epic (Q8) (verbatim):

Migrate writes a done epic's RETRO.md generated block with retro's own functions (`retro._rows`,
`_generated`, `_splice`), creating the file from templates/retro.md when absent and keeping Retro and
Improvements byte for byte when present. It prints `retro-writer: <epic>` for each done epic whose Retro
section is still the template's. The skill then dispatches retro-writer (sonnet) per such epic and reruns
`ticket.py retro <epic>`, which commits the filled file as `chore(ticket): <epic> retro`. Old epics have no
orchestrator notes, so retro-writer gains record.md (and the task Notes) as an input.

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

Design D12: Done epics are history, migrate is the one writer (verbatim):

The lint comment ("a done epic is history: its files are never rewritten") and references/tickets.md say
that only `ticket.py migrate` rewrites a done epic's task files; `ticket.py task` keeps refusing done
epics.

Constraint (verbatim, part): "references/tickets.md documents `migrate`."

Reuse brief fix-as-ac (verbatim): "\"done epic is history, never rewritten\" - T:1575, references/tickets.md:130 - doc and comment name migrate as the one writer"

Reuse brief fix-as-ac (verbatim, part): "README names subcommand (test_plugin_readme_rules.py:52)"

Interrogate verdict item 5 (verbatim): "Write order and idempotence (C3): task files are rewritten first, retro rows are computed from the new values, both written and committed together; test migrate, then `ticket.py retro <epic>`, then migrate prints nothing to change."

#### Acceptance conditions

- AC1: `migrate <epic>` and `migrate --all` rewrite the old-scheme task files of todo, in-progress and done epics and commit once per changed epic as `chore(ticket): <epic> migrate`, each commit holding exactly that epic's task files and RETRO.md written [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate.py::test_one_commit_per_epic]
- AC2: a done epic without RETRO.md gets one from templates/retro.md with retro's generated block; one with RETRO.md gets its generated block regenerated and its Retro and Improvements kept byte for byte; both land in the migrate commit [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate.py::test_retro_written_in_migrate_commit]
- AC3: a second run changes no file, makes no commit and prints `migrate: nothing to change` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate.py::test_second_run_is_noop]
- AC4: write order: the RETRO.md rows come from the new task values in the same commit, so `migrate`, then `ticket.py retro <epic>` (no new commit, block unchanged), then `migrate` again prints `migrate: nothing to change` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate.py::test_retro_after_migrate_is_stable]
- AC5: approvals.json, rulings.json, record.md, close.json, README.md and design.md of every epic are byte for byte unchanged [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate.py::test_side_files_untouched]
- AC6: migrate prints `retro-writer: <epic>` for each done epic whose RETRO.md Retro section is still the template's, and not for one already filled [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate.py::test_names_epics_needing_retro_writer]
- AC7: in a linked worktree migrate exits 1 with the main-checkout message and writes nothing [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate.py::test_refuses_linked_worktree]
- AC8: without `--transcripts` and `--logs` migrate reads the main checkout's `.logs` and `agent_usage.default_transcripts_dir` under HOME (HOME pointed at a temp dir holding a matched transcript) [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate.py::test_default_dirs]
- AC9: with `--all`, a malformed mapping in one epic writes nothing in any epic and exits 1 [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate.py::test_malformed_epic_blocks_all]
- AC10: the lint comment in ticket.py names `ticket.py migrate` as the one writer of a done epic's task files, and references/tickets.md documents `migrate` (flags, mapping, commit, idempotence) and drops "nothing writes them" for older done epics' extra keys [evidence: command:grep -q 'ticket.py migrate' plugins/workbench/skills/start-development/scripts/ticket.py && grep -q '^- `migrate`' plugins/workbench/skills/start-development/references/tickets.md && ! grep -q 'nothing writes them' plugins/workbench/skills/start-development/references/tickets.md]
- AC11: the plugin README names `ticket.py migrate` and the README test checks it [evidence: test:plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py::test_readme_names_new_subcommands]
- AC12: the start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/migrate.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_migrate.py`
- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/references/tickets.md`
- `plugins/workbench/README.md`
- `plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py`

#### Interfaces

- `ticket.py migrate [<epic>] [--all] [--dry-run] [--transcripts DIR] [--logs DIR]`: without `--dry-run` it calls `t.require_main_checkout(root)` first, maps and validates every task of every epic in scope, then per changed epic writes the task files (`t.dump`) and, for a done epic, RETRO.md, and calls `t.commit_ticket_change(epic, "migrate", paths, root)`.
- Output: one line per changed epic (`<epic>: <n> tasks migrated[, RETRO.md]`), then `retro-writer: <epic>` lines, or `migrate: nothing to change`.
- RETRO.md: `retro._rows`, `retro._generated`, `retro._splice` and the template read as in `retro._write`; extract a shared helper in retro.py only if it removes duplication (the file is not in this task's list, so call the existing functions).
- `ticket.py` lint comment: "a done epic is history: only `ticket.py migrate` rewrites its task files".

#### Expected outcome

`ticket.py migrate --all` moves every old-scheme epic to the points scheme in one commit per epic, gives every done epic a RETRO.md generated block, names the epics retro-writer must fill, and a second run is a no-op.

#### Steps

1. List the files under Files plus ticket_cmds/retro.py, templates/retro.md, test_ticket_migrate_map.py and ticket_repo_helpers.py; read them in one pass.
2. Write test_ticket_migrate.py and the README test change; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_migrate.py skills/start-development/tests/test_plugin_readme_rules.py -q`: they fail.
3. Implement the write path, the lint comment, tickets.md and the README sentence; run the verify once.
4. `git add`, commit, rerun the verify and quote its summary lines.

#### Notes

- Estimate: 5 points: the write path over an existing mapping, plus RETRO.md reuse, docs and eight command tests.
- Reuse (reuse brief): commit_ticket_change (ticket.py:302), require_main_checkout (ticket.py:292), retro run and _write (retro.py:236) for the RETRO.md shape, fixtures repo, root, mk_epic, mk_task, set_meta, commit_all (ticket_repo_helpers.py) and edit(drop=) and to_done (test_ticket_deltas.py:18,38).
- Do not build (reuse brief): a commit helper or a frontmatter writer.
- Fix-as-ac (reuse brief): "done epic is history, never rewritten" in ticket.py:1575 and references/tickets.md:130 now names migrate as the one writer (AC9).
- The Retro placeholder to detect is the template's: the `## Retro` section of templates/retro.md as written.
- Retro lesson (housekeeping-rules-estimates): a feature with a default path gets one test without the override flag (AC7); quote the lint and suite lines of a run made after `git add` and commit.
- README: add `ticket.py migrate` to the sentence listing the further ticket.py commands (README.md around line 201).

- 2026-10-25 amended: interrogate item 5: write order (retro rows from the new task values in the same commit) pinned by new AC4: migrate, ticket.py retro, migrate prints nothing to change; points stay 5

- 2026-10-25 done

### S7: Deltas legacy retired

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py`, `plugins/workbench/skills/start-development/tests/test_ticket_deltas.py`, `plugins/workbench/skills/start-development/references/tickets.md`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: ec62d68

#### Requirement

User request (verbatim, 2026-10-25): "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered."

User decision (verbatim): "Q10 (my call): deltas._legacy (minutes-only legacy rows) is removed once migrate exists, pinned by a retirement test; migrate is the one path for pre-points tasks (no backward compatibility rule)."

Design D11: deltas legacy rows retired (Q10) (verbatim):

`deltas._legacy` (minutes-only rows from `estimate` and `actual`) and the row's `legacy` flag and
`(legacy)` marker are removed, pinned by a retirement test; migrate is the one path for pre-points tasks.
`test_all_includes_legacy_minutes` is no longer accurate and is replaced by the pin.

Reuse brief fix-as-ac (verbatim): "deltas._legacy dead after migrate - C/deltas.py:81, test_ticket_deltas.py:119 - remove (no back-compat) or keep, decide"

Constraint (verbatim, part): "deltas._legacy removal with a retirement pin"

Interrogate verdict item 6 (verbatim): "deltas-legacy-retired AC3 (B3): the awk range ends at the next `^- \`` line, not at `^## Naming`."

#### Acceptance conditions

- AC1: a done task without points that carries numeric legacy `estimate` and `actual` reads `not recorded` for points, minutes and tokens in `deltas --all --json`, rows carry no `legacy` key, the text output has no `(legacy)` marker, and the task file is unchanged; this replaces test_all_includes_legacy_minutes, which is no longer accurate because migrate is the one path for pre-points tasks (Q10), and drops the `legacy` assertion of test_epic_deltas [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_deltas.py::test_pre_points_tasks_are_not_read]
- AC2: retirement pin: the deltas module has no `_legacy` attribute and its source contains neither `get("estimate"` nor `get("actual"` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_deltas.py::test_legacy_rows_retired]
- AC3: references/tickets.md's `deltas` entry has no legacy-row text and names `ticket.py migrate` as the path for pre-points tasks, and deltas.py no longer says legacy [evidence: command:! grep -qi 'legacy' plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py && awk '/^- `deltas`:/{f=1;print;next} f&&/^(- `|## )/{f=0} f' plugins/workbench/skills/start-development/references/tickets.md | grep -q 'ticket.py migrate' && ! (awk '/^- `deltas`:/{f=1;print;next} f&&/^(- `|## )/{f=0} f' plugins/workbench/skills/start-development/references/tickets.md | grep -qi 'legacy')]
- AC4: the start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_deltas.py`
- `plugins/workbench/skills/start-development/references/tickets.md`

#### Interfaces

- `ticket_cmds/deltas.py`: `_legacy` and `WHOLE` removed; `_report` rows lose the `legacy` key; `_epic_text` loses the `(legacy)` suffix; the `--all` help drops "legacy tasks included".
- The module docstring drops the legacy sentence.

#### Expected outcome

deltas reads only the points scheme; pre-points tasks show `not recorded` until `ticket.py migrate` moves them.

#### Steps

1. Read deltas.py, test_ticket_deltas.py and references/tickets.md in one pass. Replace test_all_includes_legacy_minutes with the two new tests and drop the `legacy` assertion in test_epic_deltas; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_deltas.py -q`: the new tests fail while `_legacy` exists.
2. Remove the code and the doc text; run the verify once.
3. `git add`, commit, rerun the verify and quote its summary lines. TDD exception that applies to the code change: deletion pinned by a retirement test.

#### Notes

- Estimate: 2 points: a deletion with its pin and a doc edit.
- Fix-as-ac (reuse brief): "deltas._legacy dead after migrate - C/deltas.py:81, test_ticket_deltas.py:119 - remove (no back-compat)"; user decision Q10.
- test_all_includes_legacy_minutes is replaced, not weakened: the behaviour it pinned is retired by Q10; say so in the commit message.
- Keep the rest of test_all_includes_legacy_minutes' coverage (the live epic is excluded from `--all`, the overall MdAPE) in the replacement test.

- 2026-10-25 amended: interrogate item 6: AC3 awk range ends at the next '- `' bullet or '## ' heading, not at '## Naming'

- 2026-10-25 done

### S8: Epic migrate skill

- Status: done
- Files: `plugins/workbench/skills/epic-migrate/SKILL.md`, `plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py`, `plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py`, `plugins/workbench/README.md`, `plugins/workbench/skills/start-development/SKILL.md`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: 3c5c5a5

#### Requirement

User request (verbatim, 2026-10-25): "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered."

User decision (verbatim): "Q8 RETRO.md for every old done epic: `ticket.py retro <epic>` for the measured tables, retro-writer (sonnet) fills Retro and Improvements from record.md and the deltas; the skill runs this per epic."

Design D1: One subcommand, one thin skill (Q1) (verbatim):

`ticket.py migrate` lives in a new module `ticket_cmds/migrate.py` (`register(sub, t)`, `run(a, t)`).
`migrate <epic>` migrates one epic, `migrate --all` every epic under todo, in-progress and done (Q1: today
the five old done epics plus the bootstrap epic; the two todo epics have no tasks). `--dry-run` prints
the plan; `--transcripts DIR` and `--logs DIR` override the defaults (`agent_usage.default_transcripts_dir`
of the main checkout, the main checkout's `.logs`). The skill `skills/epic-migrate/SKILL.md` is a thin
wrapper like epic-move. Alternatives: a standalone script (rejected: the writer rule puts every ticket
write in ticket.py); one subcommand per step (rejected: one command keeps the commit shape of D9).

Design D8: RETRO.md for every done epic (Q8) (verbatim):

Migrate writes a done epic's RETRO.md generated block with retro's own functions (`retro._rows`,
`_generated`, `_splice`), creating the file from templates/retro.md when absent and keeping Retro and
Improvements byte for byte when present. It prints `retro-writer: <epic>` for each done epic whose Retro
section is still the template's. The skill then dispatches retro-writer (sonnet) per such epic and reruns
`ticket.py retro <epic>`, which commits the filled file as `chore(ticket): <epic> retro`. Old epics have no
orchestrator notes, so retro-writer gains record.md (and the task Notes) as an input.

Constraint (verbatim): "The skill plugins/workbench/skills/epic-migrate/SKILL.md is a thin wrapper over ticket.py (dry run, migrate, retro per epic, retro-writer per epic, deltas --all --buckets), at most 45 lines, frontmatter exactly name and description, registered in test_epic_skills_structure.py SKILLS, named in the plugin README and in the flow docs that test_ticket_flow_docs checks; migrate.py added to KEPT and KEPT_MODULES in test_ticket_retired_run_loop.py; references/tickets.md documents `migrate`."

Reuse brief fix-as-ac (verbatim, part): "SKILLS dict, <=45 lines, frontmatter exactly name+description, ASCII (test_epic_skills_structure.py:10,55,37); README names subcommand (test_plugin_readme_rules.py:52) and skill (test_ticket_flow_docs.py:89)"

#### Acceptance conditions

- AC1: skills/epic-migrate/SKILL.md exists with frontmatter exactly `name: epic-migrate` and a quoted description, ASCII only [evidence: test:plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py::test_skill_exists_with_matching_frontmatter]
- AC2: its body names `ticket.py migrate --all --dry-run`, `ticket.py migrate --all`, `retro-writer`, `record.md`, `ticket.py retro <epic>` and `ticket.py deltas --all --buckets` [evidence: test:plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py::test_body_names_ticket_subcommands]
- AC3: it is at most 45 lines [evidence: test:plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py::test_skills_are_short]
- AC4: every `--flag` the epic-migrate body names is in the `--help` of migrate, retro or deltas [evidence: test:plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py::test_epic_migrate_names_only_real_flags]
- AC5: start-development SKILL.md names epic-migrate and stays within 150 lines [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_start_development_names_epic_skills]
- AC6: SKILL.md's line cap still holds after the edit [evidence: test:plugins/workbench/skills/start-development/tests/test_skill_size.py::test_skill_md_within_line_cap]
- AC7: the plugin README lists epic-migrate in its skills list [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_readme_names_epic_skills]
- AC8: the start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

#### Files

- `plugins/workbench/skills/epic-migrate/SKILL.md`
- `plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py`
- `plugins/workbench/README.md`
- `plugins/workbench/skills/start-development/SKILL.md`

#### Interfaces

- `plugins/workbench/skills/epic-migrate/SKILL.md`, frontmatter `name` and `description` only, at most 45 lines, ASCII. Body, in order: dry run (`ticket.py migrate --all --dry-run`, read the plan, stop on a refusal and show its problems); `ticket.py migrate --all`; for each `retro-writer: <epic>` line, dispatch `workbench:retro-writer` (sonnet) with the epic slug and its record.md as the notes, then `ticket.py retro <epic>`; finally `ticket.py deltas --all --buckets` and report which buckets left the seed.
- `test_epic_skills_structure.py`: SKILLS gains `"epic-migrate"` with those needles; a new `test_epic_migrate_names_only_real_flags` modelled on `test_epic_task_create_names_only_flags_new_task_has`.
- `test_ticket_flow_docs.py`: `epic-migrate` added to the needles of `test_start_development_names_epic_skills` and `test_readme_names_epic_skills`.

#### Expected outcome

One skill walks a workbench from the old scheme to the new one with the right commands in the right order, and the flow docs and README point to it.

#### Steps

1. Read the five files under Files plus skills/epic-move/SKILL.md (the shape to copy) and the migrate, retro and deltas `--help` output, in one pass.
2. Update the two tests; run `cd plugins/workbench && pytest skills/start-development/tests/test_epic_skills_structure.py skills/start-development/tests/test_ticket_flow_docs.py -q`: they fail.
3. Write the skill and the two doc mentions; run the verify once.
4. `git add`, commit, rerun the verify and quote its summary lines.

#### Notes

- Estimate: 3 points: a short skill, two doc mentions, four test edits.
- start-development SKILL.md is at 149 of 150 lines: add `epic-migrate` to an existing line (the Phase 7 sentence naming `ticket.py retro <epic>` and `retro-writer` fits: epics from before RETRO.md come through `epic-migrate`), adding no line.
- Plugin README: add `epic-migrate` to the skills block (README.md around line 160, the `epic-move, epic-worktrees-remove` row or a row of its own).
- Retro lesson (housekeeping-rules-estimates): reviewers run the documented command for any README or skill snippet; AC4 makes the flags mechanical, and the reviewer also runs `ticket.py migrate --all --dry-run --root <a fixture plans dir>`.
- Until the epic merges and /reload-plugins runs, `workbench:retro-writer` is not loaded; the skill text still names it (it is the steady-state flow).

- 2026-10-25 done

### S9: Migrate retro missing

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket_cmds/migrate.py`, `plugins/workbench/skills/start-development/tests/test_ticket_migrate.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: b1072ef

#### Requirement

Epic review finding (whole-diff reviewer, 2026-10-25, verified by the orchestrator at migrate.py:205 and :251): `_plan` adds the RETRO.md lines only when `plan["docs"]` is non-empty and `_write` skips an epic with no task changes, so a done epic whose task files are already in the new scheme but which has no RETRO.md is skipped by the dry run and the real run alike, and migrate prints `migrate: nothing to change`.

README G2 (verbatim): "Each done epic gets a RETRO.md: migrate writes its generated block in the epic's one `chore(ticket): <epic> migrate` commit, and retro-writer fills Retro and Improvements from record.md."

Requirement: a done epic with no RETRO.md counts as changed even when none of its task files change. The dry run prints its `retro:` lines (the file it would create); the real run creates RETRO.md from templates/retro.md with the generated block, commits it alone as `chore(ticket): <epic> migrate`, prints `<epic>: 0 tasks migrated, RETRO.md` and then `retro-writer: <epic>`. A done epic whose task files are current and whose RETRO.md exists stays untouched, so `migrate: nothing to change` is printed only when no epic needs a task change or a RETRO.md. Idempotence holds: a second run after the fix changes nothing.

#### Acceptance conditions

- AC1: a done epic whose task files are already in the new scheme and which has no RETRO.md is listed by the dry run with its `retro:` line and no task lines [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate.py::test_dry_run_lists_missing_retro_without_task_changes]
- AC2: the real run creates that epic's RETRO.md with the generated block, commits exactly that file as `chore(ticket): <epic> migrate`, and prints `<epic>: 0 tasks migrated, RETRO.md` followed by `retro-writer: <epic>` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate.py::test_missing_retro_written_without_task_changes]
- AC3: a done epic with current task files and an existing RETRO.md is untouched, and a run over only such epics prints `migrate: nothing to change`; a second run after AC2 prints the same [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate.py::test_current_epic_with_retro_is_untouched]
- AC4: the start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/migrate.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_migrate.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

1. Red: add the three tests named in the acceptance conditions to tests/test_ticket_migrate.py (a done fixture epic with new-scheme task files and no RETRO.md; one with current files and a RETRO.md); run `bash plugins/workbench/scripts/run-tests.sh --only start-development` and see exactly those three fail.
2. Green: in ticket_cmds/migrate.py let `_plan` mark a done epic as changed when its RETRO.md is absent (retro lines in the dry run, the file in the write), make `_write` skip only epics with neither task changes nor a missing RETRO.md, and print `<epic>: 0 tasks migrated, RETRO.md`; keep `migrate: nothing to change` for a run where no epic needs anything; run the same command once and see it green.
3. Verify on the committed HEAD: `bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-25 done

### S10: Migrate this repo

- Status: done
- Files: `docs/plans/done/epic-integration-worktrees`, `docs/plans/done/flow-speed-and-token-optimiz`, `docs/plans/done/init-leaves-a-green-tree`, `docs/plans/done/lean-development-flow`, `docs/plans/done/template-update-skill-and-in`, `docs/plans/done/housekeeping-rules-estimates`
- Verify: `mise run test && mise run lint`
- Verified head: 3c5c5a5

#### Requirement

User request (verbatim, 2026-10-25): "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered."

Constraint (verbatim): "Include a final task that runs the migration for real on this repository's docs/plans (all six done epics), commits via the skill's commands, and whose acceptance conditions check `ticket.py lint` ok, `ticket.py deltas --all --buckets` showing at least one bucket with source history or refit, and a RETRO.md in every done epic; its verify is the full `mise run test && mise run lint`. Note that the retro-writer agent type loads only after /reload-plugins; the task may use a general-purpose sonnet agent instructed to follow agents/retro-writer.md."

User decision (verbatim): "Q1 Scope: every epic under docs/plans (todo, in-progress, done); today that is the five old done epics plus the bootstrap epic housekeeping-rules-estimates; the two todo epics have no tasks yet."

User decision (verbatim): "Q8 RETRO.md for every old done epic: `ticket.py retro <epic>` for the measured tables, retro-writer (sonnet) fills Retro and Improvements from record.md and the deltas; the skill runs this per epic."

Design D13: The real run on this repository (my call; open question Q2 below) (verbatim):

The last task migrates this repository's docs/plans. Since only the orchestrator writes tickets and only
in the main checkout, the orchestrator runs it there with the integration tree's ticket.py
(`python3 <integration tree>/plugins/workbench/skills/start-development/scripts/ticket.py migrate --all
--root <main>/docs/plans`, after the dry run), the same way ticket commits land on main during any epic.
The retro-writer agent type loads only after `/reload-plugins` on main, so each retro-writer step is a
general-purpose sonnet agent told to follow the integration tree's agents/retro-writer.md. Step one is
the dry run over all 1042 transcripts on disk (887 under `<session>/subagents/workflows/wf_*/`). The
task's acceptance conditions are the real check: they run the integration tree's ticket.py against main's
docs/plans (interrogate item 7). Its verify, the full `mise run test && mise run lint` in the integration
tree, guards the code only: that tree cannot see main's migrated docs/plans.

Interrogate verdict item 7 (verbatim): "migrate-this-repo verify (C4): the full suite in the integration tree cannot see main's docs/plans; the AC commands run in the main checkout are the real check and the task says so."

#### Acceptance conditions

- AC1: `ticket.py lint` over main's docs/plans prints `lint: ok` [evidence: command:P="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/docs/plans"; python3 plugins/workbench/skills/start-development/scripts/ticket.py lint --root "$P" | grep -qx 'lint: ok']
- AC2: `ticket.py deltas --all --buckets` over main's docs/plans shows at least one bucket with source history or refit [evidence: command:P="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/docs/plans"; python3 plugins/workbench/skills/start-development/scripts/ticket.py deltas --all --buckets --root "$P" | grep -Eq '^\| [0-9]+ \| [0-9]+ \| [0-9]+ \| [0-9]+ \| (history|refit) \|$']
- AC3: every done epic on main has a tracked RETRO.md [evidence: command:P="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/docs/plans"; for d in "$P"/done/*/; do git -C "$P" ls-files --error-unmatch "${d}RETRO.md" >/dev/null || exit 1; done]
- AC4: no done epic's RETRO.md still holds the template's Retro or Improvements placeholder [evidence: command:P="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/docs/plans"; ! grep -l 'Filled by retro-writer' "$P"/done/*/RETRO.md]
- AC5: the migration is complete and idempotent: a dry run over main's docs/plans prints `migrate: nothing to change` [evidence: command:P="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/docs/plans"; python3 plugins/workbench/skills/start-development/scripts/ticket.py migrate --all --dry-run --root "$P" | grep -qx 'migrate: nothing to change']
- AC6: main carries a `chore(ticket): <epic> migrate` commit for each of the six done epics [evidence: command:test "$(git log main --format=%s | grep -E '^chore\(ticket\): (epic-integration-worktrees|flow-speed-and-token-optimiz|init-leaves-a-green-tree|lean-development-flow|template-update-skill-and-in|housekeeping-rules-estimates) migrate$' | sort -u | wc -l | tr -d ' ')" -eq 6]
- AC7: main's docs/plans has no uncommitted change [evidence: command:P="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/docs/plans"; test -z "$(git -C "$P" status --porcelain -- .)"]
- AC8: the code's full suite and lint pass in the integration tree; that tree cannot see main's migrated docs/plans, so AC1 to AC7 (the integration tree's ticket.py run against main's docs/plans) are the check of the migration itself [evidence: command:mise run test && mise run lint]

#### Files

- `docs/plans/done/epic-integration-worktrees`
- `docs/plans/done/flow-speed-and-token-optimiz`
- `docs/plans/done/init-leaves-a-green-tree`
- `docs/plans/done/lean-development-flow`
- `docs/plans/done/template-update-skill-and-in`
- `docs/plans/done/housekeeping-rules-estimates`

#### Interfaces

- Commands only, the epic-migrate skill's sequence with the integration tree's ticket.py: `WT=<integration tree>`, `TK="python3 $WT/plugins/workbench/skills/start-development/scripts/ticket.py"`, run from the main checkout (`--root` defaults to main's docs/plans there).
- Writes, on main only: docs/plans/done/<epic>/tasks/*.md and docs/plans/done/<epic>/RETRO.md of the six done epics, in `chore(ticket): <epic> migrate` and `chore(ticket): <epic> retro` commits; `.logs/agents` records (gitignored).

#### Expected outcome

The six done epics are on the points scheme with a filled RETRO.md each, `deltas --all --buckets` shows calibrated buckets, and a rerun changes nothing.

#### Steps

1. Orchestrator, main checkout, clean tree: `$TK migrate --all --dry-run`; read the plan per epic (points, expected, actuals only where a legacy number, Notes line or matched transcript exists; folded roles per Q1's answer). On a refusal, stop and report the problems.
2. `$TK migrate --all`; note the `retro-writer: <epic>` lines (expected: the five old epics; the bootstrap epic's Retro is already filled).
3. Per listed epic: dispatch a general-purpose agent on sonnet told to follow `$WT/plugins/workbench/agents/retro-writer.md` (the `workbench:retro-writer` type loads only after /reload-plugins on main) with the epic slug and its record.md; then `$TK retro <epic>`, which commits the filled RETRO.md.
4. `$TK deltas --all --buckets`; record which buckets left the seed.
5. Run AC1 to AC7 from the integration tree, then the verify `mise run test && mise run lint` there; quote each summary line.

#### Notes

- Estimate: 5 points: no code, but six epics, five retro-writer dispatches and a full-suite verify.
- Writer rule (references/tickets.md): only the orchestrator writes tickets, only through ticket.py, only in the main checkout; the commits land on main like every ticket commit during an epic, while the code stays on the integration branch until close. Open question Q2 in design.md confirms this at the gate.
- `files` lists the six epic dirs because the task rewrites every task file and the RETRO.md under each.
- approvals.json, rulings.json, record.md, close.json, README.md and design.md must stay unchanged (migrate-command AC4); check `git show --stat` of each migrate commit.
- housekeeping-rules-estimates RETRO.md: its Retro and Improvements stay byte for byte; only its generated block changes (points and expected values filled).
- The verify is the full gate on purpose: this is the epic's last task.

- 2026-10-25 amended: interrogate items 1 and 7: step 1's dry run walks 1042 transcripts (887 workflow ones); AC1-AC7 run the integration tree's ticket.py against main's docs/plans and are the real check, the verify guards the code only

- 2026-10-25 done

## Files to delete

none recorded in the epic format

## Final verify

`mise run test && mise run lint`

## After merge

none
