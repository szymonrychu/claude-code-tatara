---
title: Run marker points
status: todo
repo: workbench
value: "Every implementer and reviewer run is attributable to its task, and every review measures post-delivery points"
files: [plugins/workbench/skills/epic-run/SKILL.md, plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py, plugins/workbench/agents/reviewer.md, plugins/workbench/skills/start-review/tests/test_agents_lean.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only epic-run && bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [agent-discipline, planner-points-gate, agent-usage-lib]
model: sonnet
review: ""
verified_head: ""
---

# Run marker points

## Requirement

User requirement (U3, verbatim, the per-task part): "tasks table with task title (in delivery order), post-delivery complexity measure in storypoints, delivery time (start to finish in minutes), tokens used for each task (including implementation + review)"

Design D10: epic-run step 2 starts every implementer prompt with the fixed first line `[wb <epic>/<task>/impl]` and every reviewer prompt with `[wb <epic>/<task>/review]`; fix rounds continue the same agents (SendMessage), so they need no new marker. The marker format equals `agent_usage.MARKER`. reviewer.md's Output gains `pointsActual`: the post-delivery complexity of the task in Fibonacci storypoints (1, 2, 3, 5, 8, 13), judged from the diff it reviewed against the requirement, on the same scale the planner uses. epic-run/SKILL.md stays within its line cap.

## Acceptance conditions

- AC1: epic-run step 2 puts `[wb <epic>/<task>/impl]` first in the implementer prompt and `[wb <epic>/<task>/review]` first in the reviewer prompt [evidence: test:plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py::test_prompt_marker]
- AC2: reviewer.md's Output names `pointsActual` with the Fibonacci scale [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_reviewer_reports_points_actual]
- AC3: the epic skills stay within their line caps and pins [evidence: test:plugins/workbench/skills/start-development/tests/test_epic_skills_structure.py::test_epic_run_skips_done_tasks_and_caps_are_one_number_per_role]
- AC4: epic-run, start-review and start-development suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only epic-run && bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

## Files

- `plugins/workbench/skills/epic-run/SKILL.md`
- `plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py`
- `plugins/workbench/agents/reviewer.md`
- `plugins/workbench/skills/start-review/tests/test_agents_lean.py`

## Interfaces

- Prompt marker line: `[wb <epic>/<task>/<role>]`, role `impl` or `review`, first line of the prompt.
- Reviewer output field: `pointsActual` (integer, Fibonacci).

## Expected outcome

Every implementer and reviewer run is attributable to its epic, task and role, and every review carries a post-delivery storypoint measure.

## Steps

1. List the files under Files plus scripts/lib/agent_usage.py (MARKER), read them in one pass; write AC1 and AC2 tests and run them: they fail.
2. Amend epic-run/SKILL.md and reviewer.md; run the verify once.
3. Commit; leave the tree clean.

## Notes

- Estimate: 2 points.
- Fix-as-ac (brief, prompt marker): nothing in epic-run/SKILL.md:23-27 puts epic/task in the prompt today; a structure test pins the marker (AC1).
- Depends on agent-discipline (reviewer.md, test_agents_lean.py) and planner-points-gate (Fibonacci scale wording).
