---
title: ambiguous fail releases agent
status: done
repo: agent-orchestrator
value: an ambiguous send that times out never strands its agent
files: [src/agent_orchestrator/db/queue.py, tests/test_ambiguous_verify.py]
verify: "uv run pytest tests/test_ambiguous_verify.py tests/test_dispatch_queue.py -q && mise run lint"
depends_on: [ambiguous-send-verifier, dispatch-queue-sql]
model: ""
review: ""
verified_head: 165785929473436152b446bdb1d41a6c360c8294
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 4
actual_tokens: 378966
actual_roles: "impl 3, review 2"
actual_role_tokens: "impl 288433, review 90533"
---

# ambiguous fail releases agent

## Requirement

Panel finding (high, opus, verified: tests/test_ambiguous_verify.py:242 resets the reservation by hand): db/queue.py fail_ambiguous (:512) fails the message at the deadline but leaves agents.last_dispatched_at = dispatched_at; when the turn never started the agent stays idle, free_since never advances, so it is excluded forever and a user Retry never dispatches. Fix: fail_ambiguous (and retry_message) release the reservation guarded by last_dispatched_at = the message's dispatched_at, like resolve_not_started; remove the manual UPDATE from the test.

## Acceptance conditions

- AC1: after an ambiguous deadline failure the agent is pickable again and Retry dispatches without manual reset [evidence: test:tests/test_ambiguous_verify.py::test_unknown_outcome_waits_then_fails_at_deadline]
- AC2: the release never clears a newer reservation [evidence: test:tests/test_ambiguous_verify.py::test_ambiguous_fail_keeps_newer_reservation]

## Files

- `src/agent_orchestrator/db/queue.py`
- `tests/test_ambiguous_verify.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The requirement holds, pinned by the acceptance tests.

What is true and observable when the task is done.

## Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
