---
title: Actuals backfill
status: todo
repo: workbench
value: "Runs the hook missed, this epic included, still get measured actuals"
files: [plugins/workbench/scripts/lib/agent_usage.py, plugins/workbench/scripts/tests/test_agent_usage.py, plugins/workbench/skills/start-development/scripts/ticket_cmds/task_cmd.py, plugins/workbench/skills/start-development/scripts/ticket_cmds/actuals.py, plugins/workbench/skills/start-development/tests/test_ticket_task_status.py, plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py, plugins/workbench/skills/start-development/references/tickets.md]
verify: "bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [agent-usage-lib, stamp-actuals]
model: sonnet
review: ""
verified_head: ""
---

# Actuals backfill

## Requirement

User requirement (U3, verbatim, the measured part): "delivery time (start to finish in minutes), tokens used for each task (including implementation + review)"

Gate answer Q3 (approved 2026-10-24): add a backfill so stamp-actuals and retro work for runs the hook did not record, this epic included.

Design D16: `plugins/workbench/scripts/lib/agent_usage.py` gains `backfill(transcripts_dir, logs_dir, refresh=False)`. It scans a harness subagent transcript dir (Claude Code: `~/.claude/projects/<project>/<session>/subagents/agent-*.jsonl`; `<project>` derived from the workbench root the way Claude Code derives it, every character that is not a letter or digit replaced by `-`, or the dir passed explicitly) for transcripts whose first user prompt starts with the `[wb <epic>/<task>/<role>]` marker, and writes the missing `.logs/agents/<agentId>.json` records with the same summariser and record format the hook uses (`summarize`, `parse_marker`, `role_for`, `write_record`; agentType from `agent-<id>.meta.json` when present). It never overwrites a record the hook already wrote unless `refresh` is set. Unmarked transcripts are skipped. It returns the records it wrote. `ticket.py task <epic> <task> --status done` runs the backfill for that epic before stamping when `.logs/agents` has no record for the task. A new subcommand `ticket.py actuals <epic> --backfill [--transcripts <dir>] [--refresh]` runs it by hand and prints one line per record written (agentId, epic/task/role, minutes, tokens). The retirement pin's KEPT and KEPT_MODULES gain `actuals` and its module; references/tickets.md documents the subcommand.

## Acceptance conditions

- AC1: in a fixture dir with a marked and an unmarked transcript, backfill writes one record for the marked agent, with the hook's fields and once-per-message.id tokens, and none for the unmarked one [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_writes_marked_only]
- AC2: running backfill twice writes nothing the second time and leaves an existing hook record untouched [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_is_idempotent]
- AC3: with refresh set, backfill rewrites an existing record from its transcript [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_refresh_overwrites]
- AC4: the default transcripts dir is `~/.claude/projects/<root with every non-alphanumeric character replaced by ->` (home overridable in the test) [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_default_transcripts_dir]
- AC5: `ticket.py task --status done` with no record for the task backfills from `--transcripts` and stamps the actuals [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_task_status.py::test_done_backfills_before_stamping]
- AC6: `ticket.py actuals <epic> --backfill --transcripts <dir>` prints one line per record written and writes nothing on a rerun [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_task_status.py::test_actuals_backfill_command]
- AC7: the retirement pin lists `actuals` and its module and still holds [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py::test_run_loop_commands_retired]
- AC8: scripts and start-development suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

## Files

- `plugins/workbench/scripts/lib/agent_usage.py`
- `plugins/workbench/scripts/tests/test_agent_usage.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/task_cmd.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/actuals.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_task_status.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py`
- `plugins/workbench/skills/start-development/references/tickets.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
