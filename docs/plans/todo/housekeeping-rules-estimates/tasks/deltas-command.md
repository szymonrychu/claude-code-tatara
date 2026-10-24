---
title: Deltas command
status: todo
repo: workbench
value: One read-only command shows how far estimates were off and the table the next estimate uses
files: [plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py, plugins/workbench/skills/start-development/tests/test_ticket_deltas.py, plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py, plugins/workbench/skills/start-development/references/tickets.md]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint"
depends_on: [retro-command]
model: opus
review: ""
verified_head: ""
---

# Deltas command

## Requirement

User requirement (U4, verbatim): "scripting support getting deltas between complexity/time of delivery/tokens usage per task. New tools are meant to make the estimates more precise with time. Task table will be used for future estimates, retro table will be used to propose improvements for future work (also including workflow improvements). It must be seamless for the agent (taking over most of the estimation from agent's reasoning)."

Design D13: `ticket.py deltas <epic>` prints, per task, estimate against actual for points (points vs points_actual), minutes (expected_minutes vs actual_minutes) and tokens (expected_tokens vs actual_tokens), the differences and actual-over-expected ratios, and the MdAPE per metric over the epic. `ticket.py deltas --all` covers every done epic and adds legacy done tasks that carry numeric `estimate` and `actual` (minutes) as minutes-only rows marked legacy: they count toward the minutes MdAPE, are never bucketed by points and are never written. `ticket.py deltas --buckets` prints `calibration.bucket_table` over the same rows `new-task` uses (points, minutes, tokens, n, source). `--json` prints machine-readable output for every mode. The command is read-only: it writes no file and makes no commit. KEPT and KEPT_MODULES gain `deltas` and `deltas.py`.

## Acceptance conditions

- AC1: `deltas <epic>` prints one row per task with points, minutes and tokens estimate, actual, difference and ratio, and the MdAPE per metric [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_deltas.py::test_epic_deltas]
- AC2: `deltas --all` spans done epics and includes legacy `estimate`/`actual` tasks as minutes-only rows that are never bucketed [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_deltas.py::test_all_includes_legacy_minutes]
- AC3: `deltas --buckets --json` equals `calibration.bucket_table` over the rows new-task uses [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_deltas.py::test_buckets_match_new_task]
- AC4: deltas writes nothing and commits nothing [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_deltas.py::test_read_only]
- AC5: references/tickets.md documents `deltas` [evidence: command:grep -n "deltas" plugins/workbench/skills/start-development/references/tickets.md]
- AC6: the retirement pin lists `deltas` and `deltas.py` and still holds [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py::test_run_loop_commands_retired]
- AC7: start-development and scripts suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_deltas.py`
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
