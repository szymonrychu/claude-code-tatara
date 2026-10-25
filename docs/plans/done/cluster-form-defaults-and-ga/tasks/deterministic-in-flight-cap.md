---
title: deterministic in-flight cap test
status: done
repo: agent-orchestrator
value: "the full suite is green on every run, not most runs"
files: [tests/test_dispatcher.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_dispatcher.py && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: 3fcbb0ba697209495a2b3a6cc21b3379da6e5068
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# deterministic in-flight cap test

## Requirement

tests/test_dispatcher.py::test_at_most_eight_sends_in_flight is timing-flaky: under full-suite load the peak reaches 7, not 8 (seen twice in full runs, always passes alone). Make it deterministic without weakening it: the counting _send wrapper blocks on an asyncio.Event released only after 8 sends are in flight (or after a bounded timeout that fails the test), so the test asserts the cap is reached and never exceeded, instead of relying on asyncio.sleep(0.2) overlap. Do not change dispatcher behaviour.

## Acceptance conditions

- AC1: the in-flight cap test reaches exactly 8 concurrent sends and passes 20 runs in a row [evidence: command:for i in $(seq 20); do uv run pytest -q -p no:cacheprovider tests/test_dispatcher.py::test_at_most_eight_sends_in_flight || exit 1; done]

## Files

- `tests/test_dispatcher.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The cap test synchronises on an event, not sleep overlap, and is stable under load.

## Steps

- Test-only change (exception: the test itself is the deliverable). Rewrite the wrapper to gate on an asyncio.Event set when now reaches 8; assert peak == 8 and never above.
- Run the AC1 loop: 20 passes. Run the verify command.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
