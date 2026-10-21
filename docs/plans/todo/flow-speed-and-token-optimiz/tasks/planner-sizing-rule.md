---
title: Planner sizing rule
status: todo
repo: workbench
value: New plans cannot schedule full-suite verifies and size tasks by what their verify costs
files: [plugins/workbench/workflows/validate-tasks.mjs, plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs, plugins/workbench/skills/start-development/references/phases-1-3.md, plugins/workbench/agents/planner.md, plugins/workbench/skills/start-development/tests/test_planner_agent.py, plugins/workbench/skills/start-development/tests/test_review_flow_docs.py]
verify: "cd plugins/workbench && pytest skills/start-development/tests/test_planner_agent.py skills/start-development/tests/test_review_flow_docs.py -q && bash scripts/run-tests.sh --only workflows"
depends_on: [estimator-model]
owns: []
uses: [estimator-params]
model: sonnet
estimate: 6
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Planner sizing rule

## Requirement

Size tasks by test files and verify runtime and enforce targeted verifies at plan time (design D10, D11, D13).

- `plugins/workbench/workflows/validate-tasks.mjs`: read `fullSuitePatterns` from `plugins/workbench/scripts/lib/estimator.json` (path relative to the script) and the repo's workbench.json `suites` (through `scripts/lib/workbench.py config`). A task with status `todo` whose `verify` is the full suite (a part matching a pattern, after a leading `cd <dir>` part, or equal to a `suites` entry) fails with `task <id>: verify '<cmd>' runs the full suite; name the test files or the component suite (run-tests.sh --only <component>) plus lint, and split the task if that is not enough`. A task in any other status gets the same text as a warning only. The over-90 estimate warning and `MAX_ESTIMATE_MIN` are removed.
- `skills/start-development/references/phases-1-3.md`, phase 3: replace "size each task to about an hour, split it when it runs over 90" with: one test file's worth of behaviour, at most 8 files; a targeted verify (named test files or a component suite plus lint, never the full suite); sibling tasks under 3 files that share a test file are merged into one; estimates come from `ticket.py estimate <epic>` and `--estimate` is only an override.
- `plugins/workbench/agents/planner.md`: the same sizing rule, and "read each brief by its heading index: grep its `^#` headings first, then read only the sections the plan needs".
- `test_review_flow_docs.py`'s "about an hour" needle becomes the new rule's needle; `test_planner_agent.py` pins the planner's sizing and heading-index lines.

## Acceptance conditions

- AC1: a full-suite verify on a todo task fails the lint with the split hint [evidence: test:plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs::full-suite-verify-on-todo-task-fails]
- AC2: a full-suite verify on a started task is a warning only [evidence: test:plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs::full-suite-verify-on-started-task-warns]
- AC3: targeted verifies pass [evidence: test:plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs::targeted-verify-passes]
- AC4: an estimate over 90 no longer warns [evidence: test:plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs::no-estimate-warning]
- AC5: a verify equal to a repo suites entry counts as the full suite [evidence: test:plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs::repo-suites-entry-counts-as-full]
- AC6: the planner agent carries the sizing rule and the heading-index reading [evidence: test:plugins/workbench/skills/start-development/tests/test_planner_agent.py::test_planner_sizing_and_heading_index]
- AC7: phases-1-3.md states the sizing rule by test files and verify runtime [evidence: test:plugins/workbench/skills/start-development/tests/test_review_flow_docs.py::test_phase3_sizing_by_test_files_and_verify_runtime]

## Files

- `plugins/workbench/workflows/validate-tasks.mjs`
- `plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs`
- `plugins/workbench/skills/start-development/references/phases-1-3.md`
- `plugins/workbench/agents/planner.md`
- `plugins/workbench/skills/start-development/tests/test_planner_agent.py`
- `plugins/workbench/skills/start-development/tests/test_review_flow_docs.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
