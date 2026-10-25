---
title: Agent discipline
status: done
repo: workbench
value: "Implementers, reviewers and the planner read once, edit once, never tamper with tests, never add compat shims, and ask instead of guessing"
files: [plugins/workbench/agents/implementer.md, plugins/workbench/agents/reviewer.md, plugins/workbench/skills/start-review/tests/test_agents_lean.py, plugins/workbench/agents/planner.md, plugins/workbench/skills/start-development/tests/test_planner_agent.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-research && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint"
depends_on: [housekeeping-rules]
model: sonnet
review: ""
verified_head: b9ee9ba
points_actual: 2
actual_minutes: 14
actual_tokens: 691774
actual_roles: "impl 10, review 4"
actual_role_tokens: "impl 609420, review 82354"
---

# Agent discipline

## Requirement

User requirement (U1, verbatim, the parts addressed to implementing and reviewing subagents):

- don't edit/delete/xfail tests to make them pass, unless the test itself is no longer accurate- tests are here to make the code repeatable and ensure lack of regressions
- implementing/reviewing subagents must (before changing anything) list all files, then read them in one pass, only then make all edits, then run tests once
- no backward compatibility unless I explicitely ask for it
- do not guess (at any level)- it's better to ask either me or fable architect if unsure
- always aim for the full scope of the improvement- never cut corners, or reduce scope

Design D2: implementer.md and reviewer.md carry the discipline reconciled with TDD: list every file the step touches, read them all in one pass, make all edits for the step, then run the targeted verify once per red or green step, never an edit-run-edit-run dribble; this agrees with rules/tdd.md (red, then green, then refactor). The test-tampering rule reads: never edit, delete, skip or xfail a test to make it pass, unless the test itself is no longer accurate, and then say which test and why. The reviewer treats an added skip or xfail, a weakened test, and a backward compatibility shim the requirement did not ask for as high findings. An implementer unsure of a fact does not guess: it returns the question in a new report field `questions` (the orchestrator asks the user or fable). Existing pinned wording (`undelivered`, `discovered`, `tests.red`, `handoff`, the reviewer's step order and output fields, the word caps) stays.

README goal G3 names the planner too: planner.md carries the same discipline for its own work (list every file the plan touches, read them in one pass before writing tasks) and the no-tampering rule for what it plans: it never plans a task that edits, deletes, skips or xfails a test to make it pass unless the test itself is no longer accurate, and it states that a requirement it is unsure of is asked (open question), never guessed.

## Acceptance conditions

- AC1: implementer.md and reviewer.md state "list every file", "one pass" and "once per red or green step" [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_agents_list_read_once_edit_once]
- AC2: implementer.md and reviewer.md forbid editing, deleting, skipping or xfailing a test to make it pass, with the "no longer accurate" exception named [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_no_test_tampering]
- AC3: reviewer.md makes an added skip or xfail and an unrequested backward compatibility shim high findings [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_reviewer_flags_xfail_and_compat_shims]
- AC4: implementer.md's Report section has a `questions` field and says to ask instead of guessing [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_implementer_asks_instead_of_guessing]
- AC5: the existing pins hold (lean implementer, reviewer order) [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_reviewer_verifies_then_reviews]
- AC6: the agent-text suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-research && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]
- AC7: planner.md states "list every file", "one pass", the no-tampering rule with the "no longer accurate" exception, and asks instead of guessing [evidence: test:plugins/workbench/skills/start-development/tests/test_planner_agent.py::test_planner_discipline]

## Files

- `plugins/workbench/agents/implementer.md`
- `plugins/workbench/agents/reviewer.md`
- `plugins/workbench/skills/start-review/tests/test_agents_lean.py`
- `plugins/workbench/agents/planner.md`
- `plugins/workbench/skills/start-development/tests/test_planner_agent.py`

## Interfaces

- implementer report fields: existing `complete`, `summary`, `commits`, `acEvidence`, `undelivered`, `discovered`, `tests`, `verification`, plus `questions` (list of strings).
- reviewer output fields unchanged: `head`, `verifyPassed`, `unmetAcs`, `findings`, `declined`, `cannotVerify`.

## Expected outcome

The implementer, reviewer and planner texts carry the list, read once, edit all, verify once per step discipline, the no-tampering rule with its exception, the no-compat-shim rule and the ask-do-not-guess rule, consistent with rules/tdd.md and rules/housekeeping.md.

## Steps

1. List the files under Files plus rules/tdd.md and rules/housekeeping.md, read them in one pass; add the four new tests and run `pytest skills/start-review/tests/test_agents_lean.py -q` from plugins/workbench: they fail.
2. Amend implementer.md and reviewer.md (amend the existing lines at implementer.md "Never weaken or delete" and reviewer.md step 4, do not add parallel statements); run the verify once.
3. Commit; leave the tree clean.

## Notes

- Estimate: 2 points.
- Do-not-build (brief): a separate "never weaken or delete a test" rule; amend implementer.md:59,90 and reviewer.md:40-41.
- Fix-as-ac (brief, conflict with TDD): the discipline reads "list, read all, edit all, run verify once per red/green step" and must agree with tdd.md and implementer.md:52-57.
- Agent files are pinned by test_epic_skills_structure.py (word caps, `acEvidence`) and test_start_skills_structure.py; keep those phrases.
- `pointsActual` for the reviewer is added later by run-marker-points; do not add it here.

- 2026-10-24 done

- 2026-10-25 done
