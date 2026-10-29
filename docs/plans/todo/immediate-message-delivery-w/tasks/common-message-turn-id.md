---
title: common message turn id
status: todo
repo: agents-common
value: trigger services can tell when merged messages share one answer
files: [src/agents_common/orchestrator.py, src/agents_common/fake_orchestrator.py, tests/test_orchestrator_client.py]
verify: "uv run pytest tests/test_orchestrator_client.py tests/test_runs.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# common message turn id

## Requirement

Goal G4 (README), verbatim: "Matrix chat messages in a room whose run is in progress are delivered at once, and an answer shared by merged messages is relayed to the room once."

Design D18 (agents-common part), verbatim: "agents-common `Message.turn_id` (new, released 0.4.0, connector pin moved) carries the link; the fake orchestrator can complete one turn for several messages."

Design D14, verbatim: "`messages.status` stays `sent`; "answered" stays derived through `turn_id` (all messages merged into one turn read its `final_text`). agents-common's run tracker reads the linked turn as today."

Scope (agents-common): `src/agents_common/orchestrator.py` (`Message.turn_id`), `src/agents_common/fake_orchestrator.py` (`complete_turn(..., turn_id=None)` and the message view's `turn_id`), `tests/test_orchestrator_client.py`.

## Acceptance conditions

- ac1: Message parses turn_id from a message view (a string, or null while unlinked) (new) [evidence: test:tests/test_orchestrator_client.py::test_message_turn_id]
- ac2: FakeOrchestrator.complete_turn with an explicit turn_id lets two messages share one turn; get_message returns that turn_id and the same final_text for both (new) [evidence: test:tests/test_orchestrator_client.py::test_fake_completes_one_turn_for_two_messages]
- ac3: the client and runs suites and lint pass [evidence: command:uv run pytest tests/test_orchestrator_client.py tests/test_runs.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_common/orchestrator.py`
- `src/agents_common/fake_orchestrator.py`
- `tests/test_orchestrator_client.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
