---
title: Epic migrate skill
status: todo
repo: workbench
value: "One skill walks the whole migration: dry run, migrate, retros, and the bucket table"
files: [plugins/workbench/skills/epic-migrate/SKILL.md, plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py, plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py, plugins/workbench/README.md, plugins/workbench/skills/start-development/SKILL.md]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [migrate-command, retro-writer-record-input]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 34
expected_tokens: 2250000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Epic migrate skill

## Requirement

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

## Acceptance conditions

- AC1: skills/epic-migrate/SKILL.md exists with frontmatter exactly `name: epic-migrate` and a quoted description, ASCII only [evidence: test:plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py::test_skill_exists_with_matching_frontmatter]
- AC2: its body names `ticket.py migrate --all --dry-run`, `ticket.py migrate --all`, `retro-writer`, `record.md`, `ticket.py retro <epic>` and `ticket.py deltas --all --buckets` [evidence: test:plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py::test_body_names_ticket_subcommands]
- AC3: it is at most 45 lines [evidence: test:plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py::test_skills_are_short]
- AC4: every `--flag` the epic-migrate body names is in the `--help` of migrate, retro or deltas [evidence: test:plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py::test_epic_migrate_names_only_real_flags]
- AC5: start-development SKILL.md names epic-migrate and stays within 150 lines [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_start_development_names_epic_skills]
- AC6: SKILL.md's line cap still holds after the edit [evidence: test:plugins/workbench/skills/start-development/tests/test_skill_size.py::test_skill_md_within_line_cap]
- AC7: the plugin README lists epic-migrate in its skills list [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_readme_names_epic_skills]
- AC8: the start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

## Files

- `plugins/workbench/skills/epic-migrate/SKILL.md`
- `plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py`
- `plugins/workbench/README.md`
- `plugins/workbench/skills/start-development/SKILL.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
