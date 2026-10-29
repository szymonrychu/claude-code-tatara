---
title: orch flaky push after decision
status: todo
repo: agents-orchestrator
value: "orchestrator main stays reliably green for every hive's merges"
files: [tests/test_hive_push.py, src/agents_orchestrator/dispatcher/hive.py, src/agents_orchestrator/dispatcher/loop.py]
verify: "uv run --frozen pytest tests/test_hive_push.py && mise run lint"
depends_on: [orch-e2e-hive-activity]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch flaky push after decision

## Requirement

Reported by hive cct2 (via mx-34 msg 391, 2026-10-29), verbatim: "orchestrator main has a flaky test from hive-decoupling: test_hive_push.py::test_dispatcher_run_pushes_after_decision fails about 1 in 4 on clean origin/main (local Postgres)."

Find the root cause of the intermittent failure of tests/test_hive_push.py::test_dispatcher_run_pushes_after_decision (added by orch-handover-outcome-note) and fix it at the cause. If the race is in the dispatcher (the leadership-request outcome push after a decision), fix the code; if the test's own timing or ordering is wrong, fix the test so it waits on the real condition rather than a sleep. Do not quarantine, skip, xfail or loosen what the test asserts (the rejection note reaches the requester and the epoch stays 1). Reproduce first: run the test repeatedly against a local Postgres (pgserver worked in this pod for earlier tasks) and record the failure rate before and after; the fix must hold over at least 40 consecutive runs.

## Acceptance conditions

- AC1: the test passes 40 consecutive runs against a local Postgres after the fix, and the failure was reproduced before it [evidence: command:for i in $(seq 1 40); do uv run --frozen pytest -q -p no:cacheprovider tests/test_hive_push.py::test_dispatcher_run_pushes_after_decision || exit 1; done]
- AC2: the test still asserts the rejection note and epoch 1, with no skip, xfail or weakened assertion [evidence: test:tests/test_hive_push.py::test_dispatcher_run_pushes_after_decision]
- AC3: the hive push suite and lint pass [evidence: command:uv run --frozen pytest tests/test_hive_push.py && mise run lint]

## Files

- `tests/test_hive_push.py`
- `src/agents_orchestrator/dispatcher/hive.py`
- `src/agents_orchestrator/dispatcher/loop.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Sync the branch to origin/main; start a local Postgres (pgserver) and run the test 40 times: record the failure count (expect about 1 in 4).
- Read the test and the dispatcher outcome-push path; name the race.
- Fix at the cause; rerun 40 times: 0 failures. Run the verify.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
