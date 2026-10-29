---
title: orch merged delivery
status: todo
repo: agents-orchestrator
value: a merged message is never sent twice and cannot bypass the hop limit
files: [src/agents_orchestrator/db/queue.py, src/agents_orchestrator/dispatcher/verify.py, tests/test_agent_session_messaging.py, tests/test_ambiguous_verify.py, MEMORY.md]
verify: "uv run --frozen pytest tests/test_readme_api.py tests/test_wrapper_client.py && mise run lint"
depends_on: [orch-dispatch-immediate, orch-session-send-priority]
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

# orch merged delivery

## Requirement

Goal G3 (README), verbatim: "a message delivered mid-turn never wedges the session: the running turn still ends on its Stop, and the message is linked to the turn that answered it (hop guard and delivery verifier included)."

Design D14, verbatim: "`queue.turn_hop` takes `max(hop)` over the messages with a sender linked to the agent's current turn (today `ORDER BY m.id DESC LIMIT 1`), so a merged session message cannot reset the hop count. The verifier's `_carries` matches a turn whose `metadata.orch_message_id` or any `merged[].metadata.orch_message_id` equals the message id, so an ambiguous send that was merged resolves `started` with that turn instead of being resent. The orchestrator's `TurnRecord` model gains `merged`. `messages.status` stays `sent`; "answered" stays derived through `turn_id` (all messages merged into one turn read its `final_text`). agents-common's run tracker reads the linked turn as today."

Design anti-goal, verbatim: "An ambiguous send resent after it was merged (duplicate delivery): the verifier recognises merged deliveries (D14)."

Scope (agents-orchestrator): `db/queue.py` (`turn_hop`), `dispatcher/verify.py` (`_carries`), `tests/test_agent_session_messaging.py`, `tests/test_ambiguous_verify.py`, `MEMORY.md`.

## Acceptance conditions

- ac1: (CI or a Docker host) turn_hop returns the highest hop among the sender messages linked to the agent's current turn, not the newest one's (new) [evidence: test:tests/test_agent_session_messaging.py::test_turn_hop_is_max_over_merged_messages]
- ac2: (CI or a Docker host) a session_send from a turn that absorbed a hop-3 message and then a hop-1 message is stored with hop 4 (new) [evidence: test:tests/test_agent_session_messaging.py::test_send_from_merged_turn_counts_the_max_hop]
- ac3: (CI or a Docker host) an ambiguous send whose message was merged into a running turn resolves started with that turn and is never resent (new) [evidence: test:tests/test_ambiguous_verify.py::test_merged_delivery_resolves_started]
- ac4: (CI or a Docker host) a stale dispatching immediate message that the wrapper merged resolves the same way (new) [evidence: test:tests/test_ambiguous_verify.py::test_stale_dispatching_merged_resolves_started]
- ac5: MEMORY.md has a dated entry on merged deliveries (hop and verifier) and why [evidence: command:grep -q 'merged' MEMORY.md]
- ac6: Docker-free suites and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_wrapper_client.py && mise run lint]

## Files

- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/dispatcher/verify.py`
- `tests/test_agent_session_messaging.py`
- `tests/test_ambiguous_verify.py`
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
