---
title: wrapper fake claude queue
status: todo
repo: claude-code-wrapper
value: "wrapper tests can show a message pasted mid-turn being absorbed, as Claude Code does"
files: [tests/fake_claude/fake_claude.py, tests/test_fake_claude_queue.py, tests/conftest.py]
verify: "uv run pytest tests/test_fake_claude_queue.py tests/test_fake_claude.py tests/test_fake_claude_commands.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-midturn-probe]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper fake claude queue

## Requirement

Design D10, verbatim: "Scenario key `"midturn_input": "queue"` (default `"drop"`, today's behaviour). With `queue`, a paste plus CR arriving while a turn runs is queued; it is written and handed to the turn at the next tool boundary, and input still queued at the turn end is sent as the next prompt, in the shapes and order the probe recorded (P1-P5). Every input is still logged in `fake-inputs.jsonl` with state `busy`."

Cartographer brief (Plan inputs, fix as acceptance criteria), verbatim: "The fake claude models absorption (`queued_command` line) instead of dropping busy input. That is the fake-claude task, which alone may edit `tests/conftest.py`."

Design Constraints, verbatim: "only wrapper-fake-claude-queue edits `tests/conftest.py`."

Scope (claude-code-wrapper): `tests/fake_claude/fake_claude.py` (the queue mode and its docstring), `tests/test_fake_claude_queue.py` (new), `tests/conftest.py` (only if a fixture helper for queue-mode scenarios is needed).

## Acceptance conditions

- ac1: in queue mode a paste plus CR during a tool step is written, after that tool's result line, in the shape P1 recorded (a `queued_command` attachment carrying the full prompt, unless the probe recorded otherwise), and the turn goes on to one Stop whose `last_assistant_message` is the text after the injection (new) [evidence: test:tests/test_fake_claude_queue.py::test_paste_during_tool_is_injected_at_the_tool_boundary]
- ac2: in queue mode input still queued when the turn's steps end goes out as the next prompt in the shape and Stop order P2 recorded (new) [evidence: test:tests/test_fake_claude_queue.py::test_input_queued_at_turn_end_goes_out_after_the_turn]
- ac3: two pastes queued before one boundary are handed over as P4 recorded, in paste order, each keeping its own markers (new) [evidence: test:tests/test_fake_claude_queue.py::test_two_queued_pastes_keep_their_order]
- ac4: ESC with queued input writes the interrupt line and then does with the queued input what P5 recorded (new) [evidence: test:tests/test_fake_claude_queue.py::test_esc_with_queued_input_follows_the_probe]
- ac5: UserPromptSubmit fires for an injected prompt exactly as P3 recorded (new) [evidence: test:tests/test_fake_claude_queue.py::test_user_prompt_submit_for_injected_prompt_matches_probe]
- ac6: every input arriving in queue mode while a turn runs is logged in fake-inputs.jsonl with state busy (new) [evidence: test:tests/test_fake_claude_queue.py::test_queued_input_logged_busy]
- ac7: without the key, input while busy is still recorded busy and dropped, and ESC is still not recorded (unchanged pins) [evidence: command:uv run pytest tests/test_fake_claude_commands.py::test_input_while_busy_recorded tests/test_fake_claude_commands.py::test_esc_not_recorded_as_busy]
- ac8: the fake's module docstring documents `midturn_input` and both values [evidence: command:grep -q 'midturn_input' tests/fake_claude/fake_claude.py && grep -q '"queue"' tests/fake_claude/fake_claude.py]
- ac9: the fake claude suites and lint pass [evidence: command:uv run pytest tests/test_fake_claude_queue.py tests/test_fake_claude.py tests/test_fake_claude_commands.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `tests/fake_claude/fake_claude.py`
- `tests/test_fake_claude_queue.py`
- `tests/conftest.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
