---
title: Full suite split shared
status: done
repo: workbench
value: The estimator and the plan lint can no longer disagree on what a full-suite verify is
files: [plugins/workbench/workflows/validate-tasks.mjs, plugins/workbench/scripts/lib/estimator.py, plugins/workbench/scripts/lib/estimator.json, plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs, plugins/workbench/scripts/tests/test_estimator.py]
verify: "cd plugins/workbench && pytest scripts/tests/test_estimator.py -q && node --test workflows/tests/validate-tasks-sizing.test.mjs && ruff check scripts"
depends_on: [audit-context-and-models, review-tiering, triage-one-call, flow-docs-update, cache-probe, cache-prefix-change]
model: sonnet
review: ""
verified_head: 7937ba8d97fa0c985fafd67ce0b116534273578a
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 3
actual_tokens: 537834
actual_roles: "impl 2, review 2"
actual_role_tokens: "impl 367157, review 170677"
---

# Full suite split shared

## Requirement

Epic review finding (2026-10-22): D13 says the full-suite predicate has no second copy, but the command splitting is implemented twice and differently: estimator.py:29-39 splits on `&&` and `;` and skips every `cd` part; validate-tasks.mjs:346-351 splits only on `&&` and skips only a leading `cd`. So `a; mise run test` is full-suite for the estimator and passes the lint.

Deliver: both classify a command the same way: split on `&&`, `||` and `;`, skip every part that is a `cd` command, and call the command full-suite when any remaining part matches `fullSuitePatterns` or equals one of the repo's suites. estimator.json gains `fullSuiteExamples`, a list of `{command, full}` pairs covering at least: `mise run test` (full), `cd plugins/x && mise run test` (full), `a; mise run test` (full), `true || mise run test` (full), `cd x; pytest -q tests/test_a.py` (not full), `pytest -q` (full), `bash scripts/run-tests.sh --only workflows` (not full). Both the python and the node test suites assert every example, so a future divergence fails a test.

## Acceptance conditions

- AC1: estimator.py classifies every fullSuiteExamples entry as listed [evidence: test:plugins/workbench/scripts/tests/test_estimator.py::test_full_suite_examples]
- AC2: validate-tasks.mjs classifies every fullSuiteExamples entry as listed [evidence: test:plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs]
- AC3: a todo task verifying with `a; mise run test` fails the plan lint [evidence: test:plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs]

## Files

- `plugins/workbench/workflows/validate-tasks.mjs`
- `plugins/workbench/scripts/lib/estimator.py`
- `plugins/workbench/scripts/lib/estimator.json`
- `plugins/workbench/workflows/tests/validate-tasks-sizing.test.mjs`
- `plugins/workbench/scripts/tests/test_estimator.py`

## Interfaces

- `estimator.json`: new key `fullSuiteExamples: [{command, full}]`; `fullSuitePatterns` unchanged.
- `estimator.full_suite(cmd, suites)` and the validate-tasks.mjs predicate keep their signatures.

## Expected outcome

One splitting rule in two languages, pinned by one shared example list.

## Steps

1. Add fullSuiteExamples and the two tests; see the node side fail on the `;` and `||` examples.
2. Align the node splitter (and the python one for `||`).
3. Run the verify command.

## Ruling

- 2026-10-22 accepted: run 3: verify-shared-deadline, launch-land-verify, full-suite-split-shared and shell-quote-refs verified clean (landing on main via c2-land). medium-only-hold rejected for one fix round: transitive hold through a chain.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
