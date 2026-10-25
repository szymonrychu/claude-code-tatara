---
title: Plugin readme commands
status: todo
repo: workbench
value: "The plugin README shows the ticket.py commands as they now are, so nobody copies a command that exits 2"
files: [plugins/workbench/README.md, plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [retro-command, deltas-command, actuals-backfill]
model: sonnet
review: ""
verified_head: ""
---

# Plugin readme commands

## Requirement

Discovered by the stamp-actuals implementer: `plugins/workbench/README.md` line 250 still shows the `ticket.py task ... --status done` command without the now-required `--points-actual N`. Update every `ticket.py` command line in the plugin README that this epic changed or added so the README matches the tool: `new-task` carries `--points <n>`; `task --status done` carries `--points-actual <n>` (and mentions `--logs <dir>` as the test override); the new subcommands `retro`, `deltas` and `actuals` (from tasks retro-command, deltas-command and actuals-backfill) each get one line in the README's ticket.py subcommand list with the same one-line description tickets.md gives them; the hooks table already lists the usage recorder. ASCII only, no em dash. Add a test under `plugins/workbench/skills/start-development/tests/` that pins: every backticked `ticket.py task` span in the README that contains `--status done` also contains `--points-actual`, every backticked `ticket.py new-task` span contains `--points`, and the README names `retro`, `deltas` and `actuals`.

## Acceptance conditions

- AC1: every README `ticket.py task ... --status done` span carries `--points-actual` and every `ticket.py new-task` span carries `--points` [evidence: test:plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py::test_readme_ticket_commands_match_tool]
- AC2: the README names the subcommands retro, deltas and actuals [evidence: test:plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py::test_readme_names_new_subcommands]
- AC3: the start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

## Files

- `plugins/workbench/README.md`
- `plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
