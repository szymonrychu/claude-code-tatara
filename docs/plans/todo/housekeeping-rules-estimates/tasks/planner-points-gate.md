---
title: Planner points gate
status: todo
repo: workbench
value: The planner gives one number per task and the gate shows the derived minutes and tokens
files: [plugins/workbench/agents/planner.md, plugins/workbench/skills/start-development/tests/test_planner_agent.py, plugins/workbench/skills/start-development/SKILL.md, plugins/workbench/skills/start-development/tests/test_lean_flow_docs.py, plugins/workbench/skills/epic-task-create/SKILL.md]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-review && mise run lint"
depends_on: [points-required, scratch-locations]
model: sonnet
review: ""
verified_head: ""
---

# Planner points gate

## Requirement

User requirement (U2, verbatim): "each task consists also of: complexity estimate in storypoints; expected time; expected tokens"

User requirement (U4, verbatim, the seamless part): "It must be seamless for the agent (taking over most of the estimation from agent's reasoning)."

Design D7: planner.md tells the planner to give each task Fibonacci storypoints with `ticket.py new-task --points N` and that the tool fills expected minutes and tokens (the planner never estimates time or tokens itself). The gate's task table in start-development/SKILL.md lists `points, expected_minutes, expected_tokens` beside id, title, value, files, depends_on, model (line-neutral: SKILL.md stays at most 150 lines). Every place the flow creates a task (`discovered` in phase 4, epic-run "What comes back", phase 5 gaps) passes `--points`. epic-task-create/SKILL.md names `--points` in its new-task command.

## Acceptance conditions

- AC1: planner.md names `--points`, the Fibonacci values and that the tool fills expected minutes and tokens, and still never says `ticket.py estimate` [evidence: test:plugins/workbench/skills/start-development/tests/test_planner_agent.py::test_planner_gives_points]
- AC2: the gate's task table line in SKILL.md names points, expected_minutes and expected_tokens, pinned [evidence: test:plugins/workbench/skills/start-development/tests/test_lean_flow_docs.py::test_gate_table_shows_estimates]
- AC3: epic-task-create names `--points` and only flags new-task has [evidence: test:plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py::test_epic_task_create_names_only_flags_new_task_has]
- AC4: SKILL.md stays within 150 lines [evidence: test:plugins/workbench/skills/start-development/tests/test_skill_size.py::test_skill_md_within_line_cap]
- AC5: start-development and start-review suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-review && mise run lint]

## Files

- `plugins/workbench/agents/planner.md`
- `plugins/workbench/skills/start-development/tests/test_planner_agent.py`
- `plugins/workbench/skills/start-development/SKILL.md`
- `plugins/workbench/skills/start-development/tests/test_lean_flow_docs.py`
- `plugins/workbench/skills/epic-task-create/SKILL.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
