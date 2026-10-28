---
title: mxc-outbound-limits
status: todo
repo: agents-matrix-connector
value: "an agent can never flood the owner's Messenger"
files: [src/agents_matrix_connector/api/agent.py, src/agents_matrix_connector/settings.py, tests/test_api_agent.py, MEMORY.md]
verify: uv run pytest tests/test_api_agent.py -q
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 965826
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc-outbound-limits

## Requirement

Epic review findings (security review .scratchpad/matrix/review/security.md MEDIUM 2 and LOW 2/3), my call to fix: outbound messages reach a real Messenger user, so abuse limits must hold.
1. `api/agent.py` (about lines 48-51, 293-301): the per-session rate check counts recent sends and inserts in separate statements, so parallel requests exceed `agent_rate_per_minute`; and one 16000-char send splits into 4 chunks, so a session can push about 80 Messenger messages a minute. Make the check and the insert atomic per session (for example a transaction-scoped advisory lock keyed on the session id, or one guarded INSERT ... SELECT), and add a per-room cap on outbound chunks per hour (a new setting with a conservative default, documented), counted in chunks, enforced atomically with the per-session limit; a refused send answers 429 with a distinct error code.
2. `api/agent.py` (about 208-225): the `X-Orch-Slug` header is stored unvalidated and unbounded; validate it as a session slug (the orchestrator's slug rules, length cap) and answer 400 otherwise.
3. `api/agent.py` (about 239-247): an `m<n>` reference to an inbound message of another room answers 409 when the room is bound elsewhere and 422 when unknown, which lets a session probe other rooms; answer the same status and error code for both.
Test first. Record the limits and their defaults in MEMORY.md with the date and why.

## Acceptance conditions

- AC1: parallel sends from one session never exceed the per-minute limit [evidence: test:tests/test_api_agent.py::test_parallel_sends_respect_rate_limit]
- AC2: outbound chunks to one room are capped per hour and the refusal is a 429 with its own error code [evidence: test:tests/test_api_agent.py::test_room_hourly_chunk_cap]
- AC3: an invalid or oversized X-Orch-Slug answers 400 [evidence: test:tests/test_api_agent.py::test_invalid_slug_header_rejected]
- AC4: a reference into another room answers the same status and code whether the room is bound elsewhere or the id is unknown [evidence: test:tests/test_api_agent.py::test_foreign_reference_errors_are_uniform]
- AC5: MEMORY.md records the outbound limits [evidence: command:grep -q "chunks per hour" MEMORY.md]

## Files

- `src/agents_matrix_connector/api/agent.py`
- `src/agents_matrix_connector/settings.py`
- `tests/test_api_agent.py`
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
