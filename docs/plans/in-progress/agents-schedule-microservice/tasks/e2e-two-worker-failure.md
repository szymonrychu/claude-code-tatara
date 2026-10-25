---
title: e2e two worker failure
status: todo
repo: agents-schedule
value: the kind e2e is a reliable gate for exactly-once firing
files: [tests/e2e/test_e2e_kind.py, scripts/e2e.sh, MEMORY.md]
verify: "bash -n scripts/e2e.sh && uv run --frozen pytest tests/e2e/test_e2e_kind.py --collect-only -q -m e2e && uv run --frozen pytest -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [ci-image-checks-and-worker-t]
model: opus
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 502921
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# e2e two worker failure

## Requirement

The kind e2e on PR #1 head 814ba20 failed (CI log: /Users/szymonri/Documents/claude-code-tatara/.logs/sched-pr1-e2e-814ba20.log; the same suite passed on fc99d8c): `test_two_workers_one_run_and_one_session_per_fire` got a 500 from the fake orchestrator control route `POST /_messages/None/complete` (the test asked to complete a run whose `message_id` was still None), and the next test, `test_delete_removes_the_schedule_and_its_runs`, failed with `Server disconnected without sending a response`. Find the root cause (a test race, a regression from the epic-review-fixes or ci-image-checks commits, or a port-forward or api pod failure) from the log and the code, prove it with a deterministic reproduction where one is possible, and fix the cause (product code if the product is wrong, the test if the test is inaccurate), without weakening the exactly-once assertions. The e2e is deterministic enough to pass on repeated CI runs, and a test does not complete a message before the run has a `message_id`.

## Acceptance conditions

- AC1: the two-worker test never asks the fake orchestrator to complete a message that does not exist yet [evidence: judgement:tests/e2e/test_e2e_kind.py waits for a run's message_id before completing it, and the root cause is named in the component MEMORY.md]
- AC2: the e2e suite still collects every test [evidence: command:bash -n scripts/e2e.sh && uv run --frozen pytest tests/e2e/test_e2e_kind.py --collect-only -q -m e2e]
- AC3: the kind e2e passes in PR CI on the fixed head [evidence: judgement:PR #1 CI e2e job green on the head that contains this task]

## Files

- `tests/e2e/test_e2e_kind.py`
- `scripts/e2e.sh`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
