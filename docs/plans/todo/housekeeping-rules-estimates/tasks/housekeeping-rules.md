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

- `scripts/harness/agents_md.py:RULE_FILES` - tuple order decides block order; append `housekeeping.md`.
- `plugins/workbench/rules/housekeeping.md` - same frontmatter shape as rules/tdd.md (parsed by `harness.sources.parse_frontmatter`).

## Expected outcome

Every workbench AGENTS.md (through `mise run harness-setup`) carries the housekeeping rules; this repo's AGENTS.md is regenerated and lint:harness is clean.

## Steps

1. List every file under Files plus rules/tdd.md and AGENTS.md's ground rules, read them in one pass; write the two tests (AC1, AC2) and run them: they fail on the missing rule file.
2. Write housekeeping.md, add it to RULE_FILES, amend AGENTS.md ground rule 3 and the writing conventions and non-negotiables.md for consistency, run `mise run harness-setup`, then the verify once.
3. Commit; leave the tree clean.

## Notes

- Estimate: 3 points.
- Do-not-build (brief): separate "never weaken or delete a test", "orchestrator never implements", "full scope" and "no em dashes" statements already exist (implementer.md:59,90, reviewer.md:40-41, non-negotiables.md:8-12, SKILL.md:104,146, AGENTS.md ground rule 3 and Writing conventions, pinned by scripts/tests/test_agents_md.py:90); the rule file restates them consistently and the others are amended, never duplicated.
- Fix-as-ac: AGENTS.md byte cap (mise-tasks/lint/agents-md, under 24000, 11184 now) and harness-setup drift (lint:harness) - AC3, AC4. Never edit the generated block by hand.
- The TDD reconciliation wording is D2 (gate Q1); the implementer and reviewer texts follow in agent-discipline.
- AGENTS.md and rule text are ASCII only; the em dash lint from em-dash-lint now runs on them.
