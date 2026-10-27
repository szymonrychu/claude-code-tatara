---
title: mxc e2e agent sends
status: todo
repo: agents-matrix-connector
value: "one end-to-end suite proves initiate, follow-ups, reply, react and answer routing across the real processes"
files: [tests/e2e/conftest.py, tests/e2e/test_e2e_agent.py]
verify: "uv run pytest tests/e2e/test_e2e_agent.py && mise run lint"
depends_on: [mxc-agent-routes, mxc-bot-sends-delivery, mxc-route-last-speaker, mxc-skip-duplicate-final, mxc-prompt-message-refs]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 9
expected_tokens: 1836811
points_actual: ""
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
- "The user's next chat message after an agent-initiated or follow-up message reaches the session that last spoke in the room while it runs."

Design D16, verbatim (e2e): "E2E: the connector stack test (real api and bot processes, fake homeserver, fake orchestrator) covers send without inbound, follow-ups during a running chat run, reply and reaction relations, refusals, and the answer routed to the last speaker."

Scope (agents-matrix-connector): the e2e stack (`tests/e2e/conftest.py`) also starts the api's agent listener with a test token hash and exposes a client for `/chat/v1`; new `tests/e2e/test_e2e_agent.py`.

## Acceptance conditions

- ac1: a send to a flagged allowed room with no inbound message reaches the fake homeserver and its status reads sent [evidence: test:tests/e2e/test_e2e_agent.py::test_initiate_without_inbound]
- ac2: two follow-up sends made while a chat-started run is still in progress reach the homeserver before that run's final answer [evidence: test:tests/e2e/test_e2e_agent.py::test_follow_ups_during_running_run]
- ac3: a reply to an m<n> carries m.in_reply_to with that inbound event id and a reaction carries m.annotation with the key, as recorded by the fake homeserver [evidence: test:tests/e2e/test_e2e_agent.py::test_reply_and_reaction_relations]
- ac4: a denied room, an unflagged unbound room and a bad reference are refused at once and nothing reaches the homeserver [evidence: test:tests/e2e/test_e2e_agent.py::test_refusals]
- ac5: after a non-mx session's delivered send, the user's next message in that room is delivered to that session as a follow run [evidence: test:tests/e2e/test_e2e_agent.py::test_answer_routed_to_last_speaker]
- ac6: a chat-started turn whose final answer equals what the session already sent is not posted twice [evidence: test:tests/e2e/test_e2e_agent.py::test_no_double_output]
- ac7: the existing e2e cases still pass [evidence: command:uv run pytest tests/e2e/test_e2e_api.py]
- ac8: the targeted tests and lint pass [evidence: command:uv run pytest tests/e2e/test_e2e_agent.py && mise run lint]

## Files

- `tests/e2e/conftest.py`
- `tests/e2e/test_e2e_agent.py`

## Interfaces

- `tests/e2e/conftest.py:Stack` gains the agent listener base URL and a helper that calls `/chat/v1/*` with the test bearer, `X-Orch-Session` and `X-Orch-Slug`.

## Expected outcome

One end-to-end suite proves G1, G2, G3 and G6 across the real api and bot processes.

## Steps

- Red: write `tests/e2e/test_e2e_agent.py` against the extended stack; run `uv run pytest tests/e2e/test_e2e_agent.py`: the cases fail before the stack serves the agent listener.
- Green: extend the stack fixture; run the task's verify: passes. Quote the summary line with counts.

## Notes

- The stack needs Docker (Postgres); this pod has none, so GitHub CI runs it; quote the CI run's summary.
- Use `agents_common.fake_orchestrator.FakeOrchestrator` as the existing e2e cases do; a non-mx session is a session the fake reports running whose slug does not start with `mx-`.
- Build the test token at runtime (`secrets.token_hex(32)`) and pass its sha256 in the stack env.
