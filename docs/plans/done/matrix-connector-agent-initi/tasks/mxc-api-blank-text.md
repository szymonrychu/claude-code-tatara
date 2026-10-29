---
title: mxc api blank text
status: done
repo: agents-matrix-connector
value: an agent learns at once that a whitespace-only message cannot be sent
files: [src/agents_matrix_connector/api/agent.py, tests/test_api_agent.py, MEMORY.md]
verify: "uv run pytest tests/test_api_agent.py && mise run lint"
depends_on: [mxc-agent-routes]
model: sonnet
review: ""
verified_head: ed9c0f71164f5efe4fe56c01d9f967982f7d8224
points: 1
expected_minutes: 4
expected_tokens: 637069
points_actual: 1
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc api blank text

## Requirement

Discovered by mxc-bot-sends-delivery (2026-10-28): the `/chat/v1` message route accepts a text that is only whitespace; the sender then fails that send as `empty_text`, so the agent gets 202 for a message that can never be delivered.

Design D5, verbatim: "`text`: 1 to 16000 characters (same bound as `session_send`); split into chunks of `MATRIX_REPLY_CHUNK_CHARS` with `chunks.split`."

Rule (my call, recorded in the connector MEMORY.md): a text with no non-whitespace character counts as empty and is refused at the api with 422 `invalid_text` (the same code and status as an empty text), nothing queued. The sender keeps its `empty_text` failure as a defence for rows queued before this change.

## Acceptance conditions

- ac1: a message whose text is only whitespace is refused with 422 invalid_text and no sends row is written [evidence: test:tests/test_api_agent.py::test_whitespace_only_text_refused]
- ac2: MEMORY.md records the whitespace rule [evidence: command:grep -qi "whitespace" MEMORY.md]
- ac3: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_api_agent.py && mise run lint]

## Files

- `src/agents_matrix_connector/api/agent.py`
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

- 2026-10-28 done: CI 40750406829 green

- 2026-10-28 actuals: no agent records
