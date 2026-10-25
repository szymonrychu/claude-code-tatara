---
title: Review seams
status: done
repo: workbench
value: "One records-or-backfill path and one marker contract, so capture cannot drift silently"
files: [plugins/workbench/scripts/lib/agent_usage.py, plugins/workbench/scripts/lib/workbench.py, plugins/workbench/skills/start-development/scripts/ticket_cmds/task_cmd.py, plugins/workbench/skills/start-development/scripts/ticket_cmds/retro.py, plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py, plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py, plugins/workbench/scripts/tests/test_agent_usage.py, plugins/workbench/skills/start-development/tests/test_ticket_deltas.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only epic-run && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint"
depends_on: [retro-command, deltas-command, actuals-backfill]
model: sonnet
review: ""
verified_head: f0bdea7
---

# Review seams

## Requirement

Two medium findings from the whole-diff review, both confirmed:

1. The "read records, backfill from transcripts when none, read again" sequence is written twice: `ticket_cmds/task_cmd.py` `_actuals` and `ticket_cmds/retro.py` `_fill_from_records`, each resolving `default_transcripts_dir(main)` and calling `agent_usage.backfill` on its own, so the fallback rules can drift. Extract one function in `plugins/workbench/scripts/lib/agent_usage.py` (for example `records_for(epic, task_or_None, logs_dir, transcripts_dir, backfill=True)`) that does the sequence once, and call it from both places; `deltas.py` keeps `backfill=False` through the same function. `deltas.py` `_logs` rebuilds `main / ".logs"` by hand to avoid the mkdir: give `workbench.logs_dir` (or a sibling) a non-creating variant and use it, so one place knows the directory name.
2. The run marker is defined twice: `epic-run/SKILL.md` carries `[wb <epic>/<task>/impl]` and `[wb <epic>/<task>/review]` as prose; `agent_usage.MARKER` is the regex. Add a test (in the epic-run structure tests or scripts tests) that extracts the marker template from the skill text, substitutes a sample epic, task and each role, and asserts `agent_usage.parse_marker` returns that epic, task and role; so editing either side fails a test instead of silently losing attribution.

## Acceptance conditions

- AC1: one shared records-or-backfill function exists in agent_usage.py and task_cmd.py, retro.py and deltas.py all call it; grep finds no second `backfill(` call site in ticket_cmds [evidence: command:test "$(grep -c 'agent_usage.backfill(\|\.backfill(' plugins/workbench/skills/start-development/scripts/ticket_cmds/task_cmd.py plugins/workbench/skills/start-development/scripts/ticket_cmds/retro.py plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py | awk -F: '{s+=$2} END {print s}')" = "0"]
- AC2: deltas resolves the logs dir through a non-creating workbench.py helper and stays read-only [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_deltas.py::test_read_only]
- AC3: a test builds the marker from the epic-run skill text and parses it with agent_usage.parse_marker for both roles [evidence: test:plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py::test_prompt_marker_parses]
- AC4: the start-development, epic-run and scripts suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only epic-run && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

## Files

- `plugins/workbench/scripts/lib/agent_usage.py`
- `plugins/workbench/scripts/lib/workbench.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/task_cmd.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/retro.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py`
- `plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py`
- `plugins/workbench/scripts/tests/test_agent_usage.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_deltas.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

1. Read agent_usage.py, workbench.py (`logs_dir`, `_state_dir`), task_cmd.py `_actuals`, retro.py `_fill_from_records`, deltas.py `_logs`, test_epic_run_structure.py `test_prompt_marker`, and the existing tests of the three commands.
2. Write `test_prompt_marker_parses` and a unit test for the shared records-or-backfill function first; run them and see them fail.
3. Extract the function, switch the three call sites, add the non-creating logs resolver, run the verify once after committing (some tests count `git ls-files`).

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Estimate: 2 points

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-25 done
