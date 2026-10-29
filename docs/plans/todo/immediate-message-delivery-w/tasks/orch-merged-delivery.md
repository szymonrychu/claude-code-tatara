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

- `db/queue.py:turn_hop(conn, agent_id) -> int | None`: `SELECT max(m.hop) ...` over `messages m` with `m.turn_id = s.current_turn_id` and `m.sender_session_id IS NOT NULL`; None when there is none.
- `dispatcher/verify.py:_carries(record: TurnRecord, message_id: int) -> bool`: true when `record.metadata["orch_message_id"]` or any `record.merged[i].metadata["orch_message_id"]` equals the id (compared as strings, as today).

## Expected outcome

A message merged into another message's turn is counted correctly by the hop guard and is never delivered twice after an ambiguous send.

## Steps

- Read `db/queue.py:turn_hop`, `dispatcher/verify.py`, `wrapper/models.py:TurnRecord` (with `merged` from orch-wrapper-client-priority), `tests/test_agent_session_messaging.py` and `tests/test_ambiguous_verify.py` in one pass.
- Red: add the four tests; they need Postgres and fail in CI until green.
- Green: change `turn_hop` and `_carries`, MEMORY entry; run the task's verify; expect all passed. Quote the summary line; the reviewer quotes the CI summary for the Postgres tests.

## Notes

- The verifier looks at the newest turns (`NEWEST_TURNS`); a merged delivery lives in the running turn, which is among them.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR; the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
