---
title: Stamp actuals
status: todo
repo: workbench
value: "Marking a task done records its measured minutes, tokens and post-delivery points with no arithmetic by the orchestrator"
files: [plugins/workbench/skills/start-development/scripts/ticket_cmds/task_cmd.py, plugins/workbench/skills/start-development/tests/test_ticket_task_status.py, plugins/workbench/skills/start-development/references/tickets.md, plugins/workbench/scripts/lib/agent_usage.py, plugins/workbench/scripts/tests/test_agent_usage.py, plugins/workbench/skills/epic-run/SKILL.md, plugins/workbench/skills/start-development/SKILL.md, plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only epic-run && mise run lint"
depends_on: [run-marker-points, agent-usage-hook, points-required]
model: opus
review: ""
verified_head: ""
---

# Stamp actuals

## Requirement

User requirement (U3, verbatim, the per-task part): "post-delivery complexity measure in storypoints, delivery time (start to finish in minutes), tokens used for each task (including implementation + review)"

User requirement (U4, verbatim, the seamless part): "It must be seamless for the agent (taking over most of the estimation from agent's reasoning)."

Design D11: `ticket.py task <epic> <task> --status done --points-actual N` (N Fibonacci, required with `--status done`) reads the `.logs/agents` records for that epic and task through `agent_usage.read_records` (re-summarising from transcripts that still exist), and `agent_usage.aggregate` stamps `actual_minutes` (first start to last end across the task's agents, ceiling minutes), `actual_tokens` (all agents, all rounds), `actual_roles` (`impl N, review N`, minutes per role, each the sum of that role's agent spans) and `actual_role_tokens` (`impl N, review N`, tokens per role), plus `points_actual`. With no records it stamps `points_actual` only and appends the dated Notes line `actuals: no agent records` (never a guess). `--logs <dir>` overrides the logs dir (default `workbench.logs_dir` of the main checkout). Statuses other than done stamp nothing new. Done epics stay refused. epic-run step 4 and start-development phase 4 step 4 pass `--points-actual <the reviewer's pointsActual>` (SKILL.md line-neutral, at most 150 lines).

## Acceptance conditions

- AC1: done with two agents' records (impl with a fix round, review) stamps actual_minutes as the ceiling of first start to last end, actual_tokens as the sum, actual_roles, actual_role_tokens and points_actual, and commits [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_task_status.py::test_done_stamps_actuals]
- AC2: `--status done` without `--points-actual`, or with a non-Fibonacci value, exits non-zero and writes nothing [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_task_status.py::test_done_requires_points_actual]
- AC3: with no records, done stamps points_actual and the Notes line `actuals: no agent records`, and leaves minutes and tokens empty [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_task_status.py::test_done_without_records_notes_it]
- AC4: records of other tasks and epics are ignored; escalated stamps no actuals [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_task_status.py::test_stamp_reads_only_its_task]
- AC5: `aggregate` computes span minutes, total tokens and per-role minutes and tokens [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_aggregate]
- AC6: epic-run step 4 passes `--points-actual` from the reviewer's pointsActual [evidence: test:plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py::test_done_passes_points_actual]
- AC7: SKILL.md stays within 150 lines and names `--points-actual` in phase 4 [evidence: test:plugins/workbench/skills/start-development/tests/test_skill_size.py::test_skill_md_within_line_cap]
- AC8: start-development, scripts and epic-run suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only epic-run && mise run lint]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/task_cmd.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_task_status.py`
- `plugins/workbench/skills/start-development/references/tickets.md`
- `plugins/workbench/scripts/lib/agent_usage.py`
- `plugins/workbench/scripts/tests/test_agent_usage.py`
- `plugins/workbench/skills/epic-run/SKILL.md`
- `plugins/workbench/skills/start-development/SKILL.md`
- `plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
