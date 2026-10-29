---
title: mxc-pool-and-binding
status: done
repo: agents-matrix-connector
value: concurrent agent calls never stall the connector and replies reach the right session
files: [src/agents_matrix_connector/api/agent.py, src/agents_matrix_connector/sender.py, tests/test_api_agent.py, tests/test_sender.py, MEMORY.md]
verify: uv run pytest tests/test_api_agent.py tests/test_sender.py -q
depends_on: [mxc-outbound-limits]
model: sonnet
review: ""
verified_head: aaa9aa49cea92f56039750cb76e1dc41d48df093
points: 3
expected_minutes: 7
expected_tokens: 965826
points_actual: 3
actual_minutes: 9
actual_tokens: 1993675
actual_roles: "impl 7, review 2"
actual_role_tokens: "impl 1735812, review 257863"
---

# mxc-pool-and-binding

## Requirement

Epic review findings for agents-matrix-connector (.scratchpad/matrix/review/connector.md, Consider 1 and 2), my call to fix:
1. `api/agent.py` (about 255-257 and 319-326) takes a second pool connection while holding one; with the pool of 10, ten simultaneous agent requests deadlock the pool and end in 503s. Restructure so one request holds at most one pool connection at a time (pass the held connection down, or release before acquiring). Test first with a pool of size N and N concurrent requests completing.
2. `sender.py` (about 116 and 199): when an initiating send fails, the room's binding is released even if a later send in that room was already delivered, so the user's reply goes to a new session. Release the binding on a failed initiating send only when no later send of that binding was delivered. Test first.
Record both in MEMORY.md with the date and why.

## Acceptance conditions

- AC1: as many concurrent agent requests as the pool size complete without a 503 [evidence: test:tests/test_api_agent.py::test_concurrent_requests_do_not_exhaust_pool]
- AC2: a failed initiating send keeps the binding when a later send in that room was delivered [evidence: test:tests/test_sender.py::test_failed_initiating_send_keeps_binding_after_later_delivery]
- AC3: a failed initiating send with no later delivery still releases the binding [evidence: test:tests/test_sender.py::test_failed_initiating_send_releases_binding]
- AC4: MEMORY.md records the pool rule [evidence: command:grep -q "one pool connection" MEMORY.md]

## Files

- `src/agents_matrix_connector/api/agent.py`
- `src/agents_matrix_connector/sender.py`
- `tests/test_api_agent.py`
- `tests/test_sender.py`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Read every file the step touches, write the AC tests first and run the task verify: the new tests fail for the expected reason.
- Implement the smallest change that passes, rerun the verify and `mise run lint`: green.
- Commit, push, open or update the PR and quote its CI result per job.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done
