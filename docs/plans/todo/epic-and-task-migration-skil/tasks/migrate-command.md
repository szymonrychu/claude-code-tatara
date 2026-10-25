---
title: Migrate command
status: todo
repo: workbench
value: "One command moves every epic to the points scheme with one commit per epic, and running it again changes nothing"
files: [plugins/workbench/skills/start-development/scripts/ticket_cmds/migrate.py, plugins/workbench/skills/start-development/tests/test_ticket_migrate.py, plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/references/tickets.md, plugins/workbench/README.md, plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [migrate-dry-run]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 57
expected_tokens: 3750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Migrate command

## Requirement

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

## Acceptance conditions

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

## Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/migrate.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_migrate.py`
- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/references/tickets.md`
- `plugins/workbench/README.md`
- `plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py`

## Interfaces

- `ticket.py migrate [<epic>] [--all] [--dry-run] [--transcripts DIR] [--logs DIR]`: without `--dry-run` it calls `t.require_main_checkout(root)` first, maps and validates every task of every epic in scope, then per changed epic writes the task files (`t.dump`) and, for a done epic, RETRO.md, and calls `t.commit_ticket_change(epic, "migrate", paths, root)`.
- Output: one line per changed epic (`<epic>: <n> tasks migrated[, RETRO.md]`), then `retro-writer: <epic>` lines, or `migrate: nothing to change`.
- RETRO.md: `retro._rows`, `retro._generated`, `retro._splice` and the template read as in `retro._write`; extract a shared helper in retro.py only if it removes duplication (the file is not in this task's list, so call the existing functions).
- `ticket.py` lint comment: "a done epic is history: only `ticket.py migrate` rewrites its task files".

## Expected outcome

`ticket.py migrate --all` moves every old-scheme epic to the points scheme in one commit per epic, gives every done epic a RETRO.md generated block, names the epics retro-writer must fill, and a second run is a no-op.

## Steps

1. List the files under Files plus ticket_cmds/retro.py, templates/retro.md, test_ticket_migrate_map.py and ticket_repo_helpers.py; read them in one pass.
2. Write test_ticket_migrate.py and the README test change; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_migrate.py skills/start-development/tests/test_plugin_readme_rules.py -q`: they fail.
3. Implement the write path, the lint comment, tickets.md and the README sentence; run the verify once.
4. `git add`, commit, rerun the verify and quote its summary lines.

## Notes

- Estimate: 5 points: the write path over an existing mapping, plus RETRO.md reuse, docs and eight command tests.
- Reuse (reuse brief): commit_ticket_change (ticket.py:302), require_main_checkout (ticket.py:292), retro run and _write (retro.py:236) for the RETRO.md shape, fixtures repo, root, mk_epic, mk_task, set_meta, commit_all (ticket_repo_helpers.py) and edit(drop=) and to_done (test_ticket_deltas.py:18,38).
- Do not build (reuse brief): a commit helper or a frontmatter writer.
- Fix-as-ac (reuse brief): "done epic is history, never rewritten" in ticket.py:1575 and references/tickets.md:130 now names migrate as the one writer (AC9).
- The Retro placeholder to detect is the template's: the `## Retro` section of templates/retro.md as written.
- Retro lesson (housekeeping-rules-estimates): a feature with a default path gets one test without the override flag (AC7); quote the lint and suite lines of a run made after `git add` and commit.
- README: add `ticket.py migrate` to the sentence listing the further ticket.py commands (README.md around line 201).

- 2026-10-25 amended: interrogate item 5: write order (retro rows from the new task values in the same commit) pinned by new AC4: migrate, ticket.py retro, migrate prints nothing to change; points stay 5
