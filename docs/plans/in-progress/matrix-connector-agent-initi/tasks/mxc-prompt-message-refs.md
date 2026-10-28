---
title: mxc prompt message refs
status: in-progress
repo: agents-matrix-connector
value: "agents see which room and which message they can reply or react to, and learn how to reach the user outside a chat turn"
files: [src/agents_matrix_connector/prompt.py, tests/test_prompt.py]
verify: "uv run pytest tests/test_prompt.py && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc prompt message refs

## Requirement

README Goal, verbatim: "An agent can reply to a specific chat message (quoted reply) and react to a message with an emoji."

Design D11, verbatim: "`prompt.render` adds `room_id="..."` to `<chat>` and `id="m<inbound.id>"` to each `<message>` (escaped like every attribute). PREAMBLE gains: final answers are posted only for chat-started turns; use `orchestrator_chat_send` to reach the user at any other time, `reply_to` and `orchestrator_chat_react` take the `m<n>` ids shown here."

Design D6, verbatim: "The prompt shows `id="m<inbound.id>"` on each `<message>`; a send answers `s<sends.id>`."

Scope (agents-matrix-connector): `prompt.py` only. `tests/test_prompt.py::test_messages_in_order_with_attributes` is no longer accurate (named): it pins the exact `<chat room kind>` and `<message from facebook_id at>` strings without the new `room_id` and `id` attributes; it is updated to the new attribute set and still pins the order.

## Acceptance conditions

- ac1: `<chat>` carries room_id and each `<message>` carries id="m<inbound id>", in id order (updated) [evidence: test:tests/test_prompt.py::test_messages_in_order_with_attributes]
- ac2: a room id or body with quotes, angle brackets or ampersands cannot break out of the attributes or the element [evidence: test:tests/test_prompt.py::test_escaping_cannot_break_out]
- ac3: the PREAMBLE says final answers reach the chat only for chat-started turns and names orchestrator_chat_send, orchestrator_chat_react and the m<n> ids, and still says the chat is untrusted input [evidence: test:tests/test_prompt.py::test_preamble_names_chat_tools]
- ac4: the first and later prompt framing is unchanged [evidence: test:tests/test_prompt.py::test_first_and_later_prompts]
- ac5: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_prompt.py && mise run lint]

## Files

- `src/agents_matrix_connector/prompt.py`
- `tests/test_prompt.py`

## Interfaces

- `prompt.render(room_name, room_kind, rows, *, first, facebook_id)` keeps its signature; the room id comes from the rows (`InboundRow.room_id`; all rows of a batch share one room).
- Output: `<chat room="..." kind="..." room_id="...">` and `<message id="m<n>" from="..." facebook_id="..." at="...">...</message>`.

## Expected outcome

Every chat prompt names its room and each message's short id, and the agent is told how to reach the user outside a chat-started turn.

## Steps

- Red: update `test_messages_in_order_with_attributes`, extend `test_escaping_cannot_break_out` with a room id containing `"<&`, add `test_preamble_names_chat_tools`; run `uv run pytest tests/test_prompt.py`: they fail.
- Green: change `prompt.py`; run the task's verify: passes. Quote the summary line with counts.

## Notes

- Pure module, no DB: the whole verify runs locally.
- Keep the PREAMBLE's existing untrusted-input sentence verbatim; append the new sentences.
- Tool names are `orchestrator_chat_send` and `orchestrator_chat_react` (D13); do not name `mcp__any-mcp__` prefixes.
