---
title: mxc e2e agent sends
status: done
repo: agents-matrix-connector
value: "one end-to-end suite proves initiate, follow-ups, reply, react and the 1:1 room-session binding across the real processes"
files: [tests/e2e/conftest.py, tests/e2e/test_e2e_agent.py]
verify: "uv run pytest tests/e2e/test_e2e_agent.py && mise run lint"
depends_on: [mxc-agent-routes, mxc-bot-sends-delivery, mxc-room-session-binding, mxc-skip-duplicate-final, mxc-prompt-message-refs]
model: sonnet
review: ""
verified_head: 40810bd99d90a3628dfbb1f3ee7ff6786aac447e
points: 5
expected_minutes: 9
expected_tokens: 1836811
points_actual: 5
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc e2e agent sends

## Requirement

README Goal, verbatim: "Docs, tests (unit, contract, e2e) and a live smoke in the owner DM covering send without inbound, quoted reply and reaction."

README Goals, verbatim:
- "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."
- "An agent can send several messages in a row without a user reply in between (follow-ups), including while a chat-started turn is still running."
- "An agent can reply to a specific chat message (quoted reply) and react to a message with an emoji."
- "A chat room and a session are bound one to one: a room has at most one bound session and a session at most one bound room, and the user's chat messages in a bound room, including the answer to an agent-initiated or follow-up message, always reach its bound session."

Design D16, verbatim (e2e): "E2E: the connector stack test (real api and bot processes, fake homeserver, fake orchestrator) covers send without inbound, follow-ups during a running chat run, reply and reaction relations, refusals, the 1:1 binding (an initiation binds the room, the user's answer reaches the bound session, `room_bound` and `session_bound` refusals, the release on session delete), and a 16000-character text of 4-byte characters accepted and delivered in chunks (interrogate Act 6)."

User decision (final gate, 2026-10-27), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go".

Scope (agents-matrix-connector): the e2e stack (`tests/e2e/conftest.py`) also starts the api's agent listener with a test token hash and exposes a client for `/chat/v1`; new `tests/e2e/test_e2e_agent.py`.

## Acceptance conditions

- ac1: a send to a flagged allowed unbound room with no inbound message reaches the fake homeserver and its status reads sent [evidence: test:tests/e2e/test_e2e_agent.py::test_initiate_without_inbound]
- ac2: two follow-up sends of the room's bound session made while its chat-started run is still in progress reach the homeserver before that run's final answer [evidence: test:tests/e2e/test_e2e_agent.py::test_follow_ups_during_running_run]
- ac3: a reply to an m<n> carries m.in_reply_to with that inbound event id and a reaction carries m.annotation with the key, as recorded by the fake homeserver [evidence: test:tests/e2e/test_e2e_agent.py::test_reply_and_reaction_relations]
- ac4: a denied room, an unflagged unbound room and a bad reference are refused at once and nothing reaches the homeserver [evidence: test:tests/e2e/test_e2e_agent.py::test_refusals]
- ac5: a non-mx session's delivered send to an unbound flagged room binds the room to it, and the user's next message there is delivered to that session as a follow run [evidence: test:tests/e2e/test_e2e_agent.py::test_initiation_binds_and_answer_reaches_session]
- ac6: in a bound room another session's send answers 409 room_bound, and the bound session's send to a second unbound flagged room answers 409 session_bound; nothing of either reaches the homeserver and the binding is unchanged [evidence: test:tests/e2e/test_e2e_agent.py::test_binding_refusals]
- ac7: after the bound session is deleted in the fake orchestrator, the binding is released and the user's next message starts a new mx- session that then holds the room [evidence: test:tests/e2e/test_e2e_agent.py::test_release_on_session_delete]
- ac8: a chat-started turn whose final answer equals what the session already sent is not posted twice [evidence: test:tests/e2e/test_e2e_agent.py::test_no_double_output]
- ac9: a message of 16000 4-byte characters is accepted by the agent listener and reaches the fake homeserver in MATRIX_REPLY_CHUNK_CHARS chunks whose bodies join to that text, and its status reads sent [evidence: test:tests/e2e/test_e2e_agent.py::test_max_text_delivered]
- ac10: the existing e2e cases still pass [evidence: command:uv run pytest tests/e2e/test_e2e_api.py]
- ac11: the targeted tests and lint pass [evidence: command:uv run pytest tests/e2e/test_e2e_agent.py && mise run lint]

## Files

- `tests/e2e/conftest.py`
- `tests/e2e/test_e2e_agent.py`

## Interfaces

- `tests/e2e/conftest.py:Stack` gains the agent listener base URL and a helper that calls `/chat/v1/*` with the test bearer, `X-Orch-Session` and `X-Orch-Slug`.

## Expected outcome

One end-to-end suite proves G1, G2, G3 and G6 (the 1:1 binding: bind on initiation, answers to the bound session, room_bound and session_bound, release on session delete) across the real api and bot processes.

## Steps

- Red: write `tests/e2e/test_e2e_agent.py` against the extended stack; run `uv run pytest tests/e2e/test_e2e_agent.py`: the cases fail before the stack serves the agent listener.
- Green: extend the stack fixture; run the task's verify: passes. Quote the summary line with counts.

## Notes

- The stack needs Docker (Postgres); this pod has none, so GitHub CI runs it; quote the CI run's summary.
- Use `agents_common.fake_orchestrator.FakeOrchestrator` as the existing e2e cases do; a non-mx session is a session the fake reports running whose slug does not start with `mx-`; deleting a session is removing it from the fake (or setting its desired state to deleting), after which the next user message or the 60 s binding sweep releases the binding (shorten the wait through the stack's clock or by sending the next message, never by sleeping 60 s).
- Build the test token at runtime (`secrets.token_hex(32)`) and pass its sha256 in the stack env.

- 2026-10-27 amended: interrogate.md Act 6: 16000 4-byte characters delivered end to end

- 2026-10-27 amended: final gate 2026-10-27: hard 1:1 room-session binding replaces last-speaker routing (D9): binding, refusals and release end to end

- 2026-10-28 done: CI 40751882452 green (345 passed)

- 2026-10-28 actuals: no agent records
