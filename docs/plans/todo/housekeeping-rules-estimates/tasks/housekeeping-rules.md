---
title: Housekeeping rules
status: todo
repo: workbench
value: "Every agent in every harness reads the user's housekeeping rules from AGENTS.md"
files: [plugins/workbench/rules/housekeeping.md, scripts/harness/agents_md.py, AGENTS.md, scripts/tests/test_agents_md.py, scripts/tests/harness/test_agents_md_block.py, plugins/workbench/skills/start-development/references/non-negotiables.md]
verify: "mise run test:scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [em-dash-lint]
model: opus
review: ""
verified_head: ""
---

# Housekeeping rules

## Requirement

User requirement (U1, verbatim):

- the agent I interact with never writes code, or builds anything- it's supervisor only, who is responsible and accountable for any and all work done by other subagents
- don't edit/delete/xfail tests to make them pass, unless the test itself is no longer accurate- tests are here to make the code repeatable and ensure lack of regressions
- implementing/reviewing subagents must (before changing anything) list all files, then read them in one pass, only then make all edits, then run tests once
- no backward compatibility unless I explicitely ask for it
- no em dash characters in any code, comment, commit, message, or content of any kind
- do not guess (at any level)- it's better to ask either me or fable architect if unsure
- always aim for the full scope of the improvement- never cut corners, or reduce scope
- all scratchpads edits land under `.scratchpad` in workbench root, use it as the only scratchpad dir
- all logs land in gitignored `.logs` in workbench root

Design D1: the rules live in a new `plugins/workbench/rules/housekeeping.md` (heading `# Housekeeping rules`, frontmatter like the other rule files) that states every rule above; `scripts/harness/agents_md.py:RULE_FILES` gains it, and `mise run harness-setup` regenerates AGENTS.md in this task. The "run tests once" rule is stated as reconciled with TDD (D2): list every file, read all in one pass, make all edits for the step, run the targeted verify once per red or green step. Existing statements are amended for consistency, not duplicated: AGENTS.md ground rule 3 ("Finish the whole scope") and "Writing and working conventions" (no em dashes) point at or agree with the new rules, and `references/non-negotiables.md` "Orchestrate. Do not implement." states that the orchestrator is the supervisor, accountable for all subagent work, and never writes code or builds anything.

## Acceptance conditions

- AC1: housekeeping.md states all nine rules: the test checks the phrases "supervisor", "accountable", "xfail", "no longer accurate", "list every file", "one pass", "backward compatibility", "em dash", "fable", "full scope", ".scratchpad" and ".logs" in the rule file and in AGENTS.md, and AGENTS.md has exactly one "## Housekeeping rules" heading [evidence: test:scripts/tests/test_agents_md.py::test_housekeeping_rules]
- AC2: RULE_FILES names housekeeping.md and the rendered rules block contains its heading [evidence: test:scripts/tests/harness/test_agents_md_block.py::test_rules_block_includes_housekeeping]
- AC3: AGENTS.md is regenerated and has no drift [evidence: command:python3 scripts/harness/setup.py --check]
- AC4: AGENTS.md stays under the byte caps [evidence: command:bash mise-tasks/lint/agents-md]
- AC5: non-negotiables.md "Orchestrate. Do not implement." names the orchestrator as supervisor, accountable for all subagent work [evidence: command:grep -n "accountable" plugins/workbench/skills/start-development/references/non-negotiables.md]
- AC6: the root scripts suite, the start-development suite and lint pass [evidence: command:mise run test:scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

## Files

- `plugins/workbench/rules/housekeeping.md`
- `scripts/harness/agents_md.py`
- `AGENTS.md`
- `scripts/tests/test_agents_md.py`
- `scripts/tests/harness/test_agents_md_block.py`
- `plugins/workbench/skills/start-development/references/non-negotiables.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
