---
title: mxc skip duplicate final
status: todo
repo: agents-matrix-connector
value: "an answer the agent already sent is not posted a second time as the turn's final reply"
files: [src/agents_matrix_connector/tracker.py, src/agents_matrix_connector/db/sends.py, README.md, tests/test_tracker.py, tests/test_readme_api.py]
verify: "uv run pytest tests/test_tracker.py tests/test_readme_api.py && mise run lint"
depends_on: [mxc-bot-sends-delivery, mxc-agent-routes]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 941421
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc skip duplicate final

## Requirement

README Non-goal, verbatim: "No automatic forwarding of every final reply of every turn to the chat (agents use the send tool)."

Design D10, verbatim: "When a chat-started run completes and its `final_text`, stripped, equals the stripped `text` of a `message` send of the same session created at or after the run's `started_at` (any status except `refused`), the tracker closes the run `handled` with reason `already_sent` and stores no outbound row. Anything else posts as today."

Design anti-goal, verbatim: "Double output: the same text posted twice because the agent sent it and its final answer repeated it."

Scope (agents-matrix-connector): `tracker.py` (the match in the completed-turn branch, a new reason constant `ALREADY_SENT = "already_sent"`), the query in `db/sends.py`, README (the reason). `tests/test_readme_api.py::test_readme_lists_every_reason` gains `tracker.ALREADY_SENT` in its reason set (extended, nothing removed).

## Acceptance conditions

- ac1: a completed chat run whose final text equals a message send of the same session made during the run is handled with reason already_sent and stores no outbound row [evidence: test:tests/test_tracker.py::test_final_text_already_sent_is_not_posted]
- ac2: a different text, a send made before the run started, a refused send, a reaction and another session's send all leave the reply posted as today [evidence: test:tests/test_tracker.py::test_final_text_posted_unless_already_sent]
- ac3: README names the already_sent reason [evidence: test:tests/test_readme_api.py::test_readme_lists_every_reason]
- ac4: the existing tracker behaviour is unchanged [evidence: test:tests/test_tracker.py::test_completed_turn_replies]
- ac5: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_tracker.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agents_matrix_connector/tracker.py`
- `src/agents_matrix_connector/db/sends.py`
- `README.md`
- `tests/test_tracker.py`
- `tests/test_readme_api.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
