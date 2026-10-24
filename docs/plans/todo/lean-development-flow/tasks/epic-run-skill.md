---
title: Epic-run skill
status: todo
repo: workbench
value: The one entry point that decouples executing an epic from planning it
files: [plugins/workbench/skills/epic-run/, plugins/workbench/skills/start-research/tests/]
verify: "bash plugins/workbench/scripts/run-tests.sh --only epic-run && bash plugins/workbench/scripts/run-tests.sh --only start-research && mise run lint"
depends_on: [start-development-rewrite]
owns: []
uses: []
model: sonnet
estimate: 5
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

# Epic-run skill

## Requirement

Add the `epic-run` skill (`plugins/workbench/skills/epic-run/SKILL.md`): execute one already-planned epic from any session. Description for the skill index: "Execute one planned epic: claim it, run its tasks in dependency order through one implementer and one reviewer each with at most two fix rounds, audit scope, close. Use after the gate of start-development or to run an epic planned in another session." The body is short and refers to the phase 4 text of `start-development/SKILL.md` for the loop rather than restating it; it adds only the entry conditions (`ticket.py lint <epic>` ok, epic in todo or in-progress, a clean green main), the per-task dispatch prompt shapes (implementer: the task file verbatim plus the tree path and the `cd`; reviewer: the task file, the tree path, the task's commit range), the status command after each task, what to do with `escalated`, `discovered` and `undelivered`, and the exit (phases 5 to 7 of start-development, one closing message of three lines). Add a structure test like the other skills' tests (frontmatter name and description, the referenced files exist, the forbidden words plan-execute, heartbeat, Workflow(, approvals absent) and register the skill wherever the start-* structure tests enumerate skills.

## Acceptance conditions

- AC1: `plugins/workbench/skills/epic-run/SKILL.md` exists with frontmatter `name: epic-run` and the description above, and names start-development phase 4, `ticket.py tasks`, `ticket.py task`, `workbench:implementer`, `workbench:reviewer` and `SendMessage` [evidence: test:plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py::test_skill_structure]
- AC2: the file contains none of plan-execute, heartbeat, `Workflow(`, approvals [evidence: test:plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py::test_no_retired_words]
- AC3: `bash plugins/workbench/scripts/run-tests.sh --only epic-run` and `--only start-research` pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only epic-run]

## Files

- `plugins/workbench/skills/epic-run/`
- `plugins/workbench/skills/start-research/tests/`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
