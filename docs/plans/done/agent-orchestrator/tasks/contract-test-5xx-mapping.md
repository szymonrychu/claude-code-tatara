---
title: contract test 5xx mapping
status: done
repo: agent-orchestrator
value: the full suite is green with the approved 5xx mapping
files: [tests/test_fake_wrapper_contract.py]
verify: "uv run pytest tests/test_fake_wrapper_contract.py tests/test_wrapper_client.py -q -p no:cacheprovider && mise run lint"
depends_on: [wrapper-5xx-ambiguous, fake-wrapper-contract]
model: ""
review: ""
verified_head: 54bd9178ff979d70b3f52fa7fc47e1595f8656a5
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 3
actual_tokens: 445312
actual_roles: "impl 2, review 2"
actual_role_tokens: "impl 227537, review 217775"
---

# contract test 5xx mapping

## Requirement

The epic full suite fails tests/test_fake_wrapper_contract.py::test_fake_status_delay_and_reset_controls (1 failed, 392 passed): it asserts a wrapper 500 maps to Unavailable, but wrapper-5xx-ambiguous (approved panel fix) maps 500 and 502 to Ambiguous. Update the contract test to the approved mapping: 500/502 -> Ambiguous, 503/504 -> Unavailable, without weakening the delay and reset control checks.

## Acceptance conditions

- AC1: the contract test pins 500 -> Ambiguous and 503 -> Unavailable and passes [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_status_delay_and_reset_controls]

## Files

- `tests/test_fake_wrapper_contract.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The full suite is green.

What is true and observable when the task is done.

## Steps

- Red already seen in the epic full suite (isinstance Ambiguous vs Unavailable).
- Update the assertion to the approved mapping; run green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
