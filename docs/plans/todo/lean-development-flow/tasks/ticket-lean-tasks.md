---
title: Ticket lean tasks
status: todo
repo: workbench
value: "The task file becomes the whole contract between planner, implementer and reviewer; one status command replaces apply-run"
files: [plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/scripts/ticket_cmds/, plugins/workbench/skills/start-development/tests/, plugins/workbench/skills/start-development/templates/]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [ticket-drop-run-commands]
owns: []
uses: []
model: opus
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Ticket lean tasks

## Requirement

Slim the task model to one integration worktree per epic with tasks run sequentially inside it, and give the orchestrator the one status command the loop needs.

1. Task frontmatter becomes exactly: `title`, `status`, `repo`, `value`, `files`, `verify`, `depends_on`, `model`, `review`, `verified_head`. Remove `owns`, `uses`, `provides`, `estimate`, `estimate_by`, `actual`, `actual_roles`, `worktree`, `branch`, `run` from the template, the loader, the writer and `new-task` (`--owns`, `--uses` go). `templates/task.md`, `templates/epic.md` (drop `## Time`) and `templates/design.md` (drop the Contracts table, the Research inputs ledger wording and every mention of approval ids) follow. `tasks <epic>` stops regenerating the README Time section and emits the tasks in dependency order (a dependency always precedes its dependents).
2. New subcommand `task <epic> <task> --status <todo|in-progress|done|escalated|blocked> [--verified-head <sha>] [--note <text>]`: sets the status (and `verified_head`, appends a dated note line under `## Notes`) and commits as `chore(ticket): <epic> task <task> <status>`. It is how the orchestrator records a task's outcome.
3. `worktrees <epic>` creates or reuses only the integration tree and branch `<epic>` (the per-task mode and `--integration` flag go; `move in-progress` keeps creating the integration tree; `--refresh` keeps fast-forwarding it). `reap --epic <epic>` reaps the integration trees of a done epic; `--task` goes.
4. `close <epic> --verify <cmd>` keeps rebase, verify on the rebased tip, fast-forward, verify on main and `close.json`; the "every done task contained in <epic>" gate and its MERGE lines go, since tasks commit directly on `<epic>`. `stage review` still refuses while a task is not `done`.
5. `lint` no longer reads approvals.json or checks owns/uses. It requires per task: a non-empty Requirement, at least one AC, `verify`, `files`, and `depends_on` entries that resolve to tasks of the epic with no cycle; when design.md exists its Decision coverage maps every `### D<n>` to existing task slugs. `check`, `index`, `existing`, `questions`, `amend`, `rename`, `roadmap`, `path`, `slug`, `stage`, `review`, `move` keep their behaviour; update their tests only where a removed field appears.
Every behaviour above is covered by a test seen red first; existing tests that assert the removed fields are updated, not deleted wholesale.

## Acceptance conditions

- AC1: a task written by `new-task` has exactly the ten frontmatter keys title, status, repo, value, files, verify, depends_on, model, review, verified_head [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_task_frontmatter_is_lean]
- AC2: `task <epic> <task> --status done --verified-head <sha>` writes status and verified_head, appends a dated note, and commits as `chore(ticket): <epic> task <task> done`; an unknown status exits 1 [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_task_status.py::test_task_status_sets_fields_and_commits]
- AC3: `tasks <epic>` emits every dependency before its dependents [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_tasks_are_in_dependency_order]
- AC4: `worktrees <epic>` creates only the integration tree; `--integration`, per-task trees and `reap --task` are gone from `--help` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py::test_worktrees_creates_integration_tree_only]
- AC5: `close` has no MERGE-line gate: with every task done it rebases, verifies and fast-forwards; it still refuses (exit 4) on a failed verify [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_close_without_containment_gate]
- AC6: `lint` passes an epic with no approvals.json and fails one whose task lacks an AC, lacks `verify`, or has a dependency cycle, and one whose design.md Decision coverage names a missing task [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_lint.py::test_lint_lean_rules]
- AC7: `grep -n "owns\|uses\|provides\|approvals\|estimate\|## Time" plugins/workbench/skills/start-development/scripts/ticket.py plugins/workbench/skills/start-development/templates/*.md` prints nothing [evidence: command:grep -c "owns\|uses\|provides\|approvals\|estimate\|## Time" plugins/workbench/skills/start-development/scripts/ticket.py plugins/workbench/skills/start-development/templates/task.md plugins/workbench/skills/start-development/templates/epic.md plugins/workbench/skills/start-development/templates/design.md]
- AC8: `bash plugins/workbench/scripts/run-tests.sh --only start-development` passes [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/`
- `plugins/workbench/skills/start-development/tests/`
- `plugins/workbench/skills/start-development/templates/`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
