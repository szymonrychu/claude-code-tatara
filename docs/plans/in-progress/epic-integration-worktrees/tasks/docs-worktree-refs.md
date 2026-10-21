---
title: Docs worktree refs
status: done
repo: workbench
value: "The worktree and ticket references match the new names, tree and landing"
files: [plugins/workbench/skills/start-development/references/worktrees.md, plugins/workbench/skills/start-development/references/tickets.md, plugins/workbench/skills/start-development/references/hooks.md, plugins/workbench/agents/implementer.md, plugins/workbench/skills/start-development/tests/test_ticket_files.py, plugins/workbench/skills/worktree-create/SKILL.md, plugins/workbench/skills/start-development/tests/test_ticket_run.py]
verify: "cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only workflows && cd ../.. && mise run lint"
depends_on: [slug-collision-guard, land-in-run, epic-base-wiring, common-worktree-path-sh, epic-close-command, fork-point-record]
owns: []
uses: []
model: sonnet
estimate: 55
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/epic-integration-worktrees--docs-worktree-refs
branch: epic-integration-worktrees--docs-worktree-refs
verified_head: cdc965c3d5981ff89cf00e9c0b0c00a7166d3ee9
run: epic-integration-worktrees
provides: []
acs_for_audit: []
process_gaps: [Implementer reports no red run and no captured pytest summary]
---

# Docs worktree refs

## Requirement

Describe naming, the integration tree, landing and cleanup in the worktree reference docs (design D1, D3, D7, D13, D14; user decisions U1, U2; interrogate verdict F, G, I).

- `references/worktrees.md`:
  - names: `<epic>-<task>`, at most 57 characters;
  - the integration tree: `<configdir>/worktrees/<epic>[/<repo>]` on branch `<epic>`, created by `move in-progress`;
  - task trees fork from `<epic>` and land on it in the run through a `worktree-merger` (`merge.py --base <epic> --keep --verify`);
  - every role on a task shares the task's one tree;
  - the harness built-in worktree feature is never used (keep the existing EnterWorktree guard sentence);
  - `move done` removes every tree and branch.
- `references/tickets.md`:
  - Naming table: per-task worktree and branch `<epic>-<task>`, at most 57 characters (28 + 1 + 28); the integration branch and tree `<epic>` at `<configdir>/worktrees/<epic>[/<repo>]`;
  - the collision rule of new-epic, new-task and rename, including names whose tree or branch (legacy double-hyphen form included) is still on disk;
  - `ticket.py close <epic> --verify <cmd>` and its `close.json` summary, `ticket.py worktrees <epic> --integration` for an epic claimed before this change, and the task frontmatter field `fork_point`;
  - the continue MERGE line `MERGE <task> --name <epic>-<task> --base <epic> --repo <repo>`;
  - the `worktree_name` cap 57.
- `references/hooks.md` (6-7): the guarded paths are `<configdir>/worktrees/<name>` for task and integration trees, plus the legacy `.worktrees/`.
- `plugins/workbench/agents/implementer.md`: a dependent's first step merges the epic branch; the tree is shared by every role on the task; the sentence `Do not call the built-in EnterWorktree` stays.
- `test_ticket_files.py:351` needles become `<epic>-<task>`, `57` and `Integration branch`, and assert `<epic>--<task>` is absent from tickets.md.
- `plugins/workbench/skills/worktree-create/SKILL.md` names task trees `<epic>-<task>` (the procedure's naming step), and the needle in `test_ticket_run.py:462` asserts `<epic>-<task>` is present and `<epic>--<task>` absent.

## Acceptance conditions

- AC1: tickets.md names the single-hyphen trees, the cap 57 and the integration branch, and no double-hyphen name [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_tickets_doc_names_single_hyphen_and_integration]
- AC2: tickets.md documents the collision rule and the MERGE line with the epic base [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_tickets_doc_collision_rule_and_merge_line]
- AC3: worktrees.md describes the integration tree, landing on the epic branch and that every role shares the task tree [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_worktrees_doc_integration_lifecycle]
- AC4: the implementer agent keeps the EnterWorktree guard [evidence: command:grep -q 'Do not call the built-in EnterWorktree' plugins/workbench/agents/implementer.md plugins/workbench/skills/worktree-create/SKILL.md]
- AC5: no double-hyphen task name remains in the worktree reference docs [evidence: command:! grep -n '<epic>--<task>' plugins/workbench/skills/start-development/references/worktrees.md plugins/workbench/skills/start-development/references/tickets.md plugins/workbench/skills/start-development/references/hooks.md plugins/workbench/agents/implementer.md plugins/workbench/skills/worktree-create/SKILL.md]
- AC6: the worktree-create skill names task trees with one hyphen [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_run.py::test_worktree_create_skill_uses_epic_task_naming]
- AC7: tickets.md documents the close command, the integration upgrade flag and the fork_point field [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_tickets_doc_close_upgrade_and_fork_point]

## Files

- `plugins/workbench/skills/start-development/references/worktrees.md`
- `plugins/workbench/skills/start-development/references/tickets.md`
- `plugins/workbench/skills/start-development/references/hooks.md`
- `plugins/workbench/agents/implementer.md`
- `plugins/workbench/skills/start-development/tests/test_ticket_files.py`
- `plugins/workbench/skills/worktree-create/SKILL.md`
- `plugins/workbench/skills/start-development/tests/test_ticket_run.py`

## Interfaces

- Documentation only; needles in test_ticket_files.py pin the wording.

## Expected outcome

A reader of worktrees.md and tickets.md finds one consistent naming and lifecycle that matches the code.

## Steps

- Red: update and add the needle tests in `test_ticket_files.py`; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_files.py -q`; expect failures.
- Green: edit the five docs.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only workflows && cd ../.. && mise run lint`.

## Notes

- `plan-execute-implementer.test.mjs:64` pins `Do not call the built-in EnterWorktree` in implementer.md; keep it.
- AC5 forbids the literal double-hyphen name in these docs: describe legacy trees as "legacy double-hyphen trees", never by the literal form.

- 2026-10-21 run epic-integration-worktrees: dependency-failed on slug-collision-guard, land-in-run, epic-base-wiring, epic-close-command, fork-point-record

- 2026-10-21 run epic-integration-worktrees: dependency-failed on slug-collision-guard, fork-point-record

- 2026-10-21 run epic-integration-worktrees: dependency-failed on fork-point-record
