---
title: Agent discipline
status: todo
repo: workbench
value: "Implementers and reviewers read once, edit once, never tamper with tests, never add compat shims, and ask instead of guessing"
files: [plugins/workbench/agents/implementer.md, plugins/workbench/agents/reviewer.md, plugins/workbench/skills/start-review/tests/test_agents_lean.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-research && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint"
depends_on: [housekeeping-rules]
model: sonnet
review: ""
verified_head: ""
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

## Acceptance conditions

- AC1: implementer.md and reviewer.md state "list every file", "one pass" and "once per red or green step" [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_agents_list_read_once_edit_once]
- AC2: implementer.md and reviewer.md forbid editing, deleting, skipping or xfailing a test to make it pass, with the "no longer accurate" exception named [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_no_test_tampering]
- AC3: reviewer.md makes an added skip or xfail and an unrequested backward compatibility shim high findings [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_reviewer_flags_xfail_and_compat_shims]
- AC4: implementer.md's Report section has a `questions` field and says to ask instead of guessing [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_implementer_asks_instead_of_guessing]
- AC5: the existing pins hold (lean implementer, reviewer order) [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_reviewer_verifies_then_reviews]
- AC6: the agent-text suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-research && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

## Files

- `plugins/workbench/agents/implementer.md`
- `plugins/workbench/agents/reviewer.md`
- `plugins/workbench/skills/start-review/tests/test_agents_lean.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
