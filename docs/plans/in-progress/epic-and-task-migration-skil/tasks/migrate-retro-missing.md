---
title: Migrate retro missing
status: todo
repo: workbench
value: "A done epic that is already on the new scheme still gets its RETRO.md from migrate, as G2 promises"
files: [plugins/workbench/skills/start-development/scripts/ticket_cmds/migrate.py, plugins/workbench/skills/start-development/tests/test_ticket_migrate.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [migrate-command]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 13
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Migrate retro missing

## Requirement

Epic review finding (whole-diff reviewer, 2026-10-25, verified by the orchestrator at migrate.py:205 and :251): `_plan` adds the RETRO.md lines only when `plan["docs"]` is non-empty and `_write` skips an epic with no task changes, so a done epic whose task files are already in the new scheme but which has no RETRO.md is skipped by the dry run and the real run alike, and migrate prints `migrate: nothing to change`.

README G2 (verbatim): "Each done epic gets a RETRO.md: migrate writes its generated block in the epic's one `chore(ticket): <epic> migrate` commit, and retro-writer fills Retro and Improvements from record.md."

Requirement: a done epic with no RETRO.md counts as changed even when none of its task files change. The dry run prints its `retro:` lines (the file it would create); the real run creates RETRO.md from templates/retro.md with the generated block, commits it alone as `chore(ticket): <epic> migrate`, prints `<epic>: 0 tasks migrated, RETRO.md` and then `retro-writer: <epic>`. A done epic whose task files are current and whose RETRO.md exists stays untouched, so `migrate: nothing to change` is printed only when no epic needs a task change or a RETRO.md. Idempotence holds: a second run after the fix changes nothing.

## Acceptance conditions

- AC1: a done epic whose task files are already in the new scheme and which has no RETRO.md is listed by the dry run with its `retro:` line and no task lines [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate.py::test_dry_run_lists_missing_retro_without_task_changes]
- AC2: the real run creates that epic's RETRO.md with the generated block, commits exactly that file as `chore(ticket): <epic> migrate`, and prints `<epic>: 0 tasks migrated, RETRO.md` followed by `retro-writer: <epic>` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate.py::test_missing_retro_written_without_task_changes]
- AC3: a done epic with current task files and an existing RETRO.md is untouched, and a run over only such epics prints `migrate: nothing to change`; a second run after AC2 prints the same [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_migrate.py::test_current_epic_with_retro_is_untouched]
- AC4: the start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/migrate.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_migrate.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
