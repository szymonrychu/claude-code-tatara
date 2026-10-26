---
title: orch agent session messaging
status: todo
repo: agents-orchestrator
value: "an opted-in leader can list other opted-in sessions and message their leaders, with loops and floods stopped"
files: [src/agents_orchestrator/api/agent.py, src/agents_orchestrator/db/queue.py, src/agents_orchestrator/db/sessions.py, openapi.json, README.md, MEMORY.md, tests/test_agent_session_messaging.py]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_agent_session_messaging.py tests/test_readme_api.py && mise run lint"
depends_on: [orch-session-options-spec, orch-session-message-sender]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 12
expected_tokens: 1686779
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch agent session messaging

## Requirement

User decision 2026-10-26, verbatim: "Cross-session messaging means: the session's leader can send messages to other sessions' leaders and receive messages from other sessions' leaders." Goal G1 (epic README), verbatim: "A sparse create-time spec option for cross-session messaging; a session with it on can list messaging-enabled sessions and send a message to another one's leader, and receives messages sent to it as turns on its leader that name the sender session." Non-goals, verbatim: "No synchronous request/reply or context transfer between sessions; messaging is an async mailbox." "No messaging for non-leader agents and no cross-session messaging for sessions without the option." Design D6, D7, D10.

Scope (agents-orchestrator), two agent routes in `src/agents_orchestrator/api/agent.py`, authenticated by `require_agent` like every `/agent/v1` route:

- `GET /agent/v1/sessions` answers 200 `{"sessions": [{"slug": str, "preset_name": str | null, "leader_present": bool}]}`: every session other than the caller's whose spec has `session_messaging` true and whose `desired` is `active`, ordered by slug. `leader_present` is true when a hive has a current leader on a not-gone agent, or an alone session has a not-gone agent. A caller whose own session lacks the option gets 403 `messaging_disabled`.
- `POST /agent/v1/sessions/{slug}/messages` with body `{"text": str}` (1 to 16000 characters, module constant; `extra="forbid"`) answers 202 `{"message_id": int}` after `queue.enqueue_message(conn, target.id, text, sender_session_id=caller session id, sender_slug=caller slug, hop=<computed>)`. Checks in this order, each refusal queues nothing (design D7):
  1. caller session without `session_messaging`: 403 `messaging_disabled`;
  2. caller not the current leader (hive: `leadership.current_leader` is another agent or none; the only agent of an alone session counts as leader): 403 `not_leader`;
  3. no session with that slug: 404 `not_found`;
  4. the slug is the caller's own: 422 `self_send`;
  5. target without `session_messaging`: 409 `target_messaging_disabled`;
  6. target `desired` is `deleting`: 409 `session_deleting`;
  7. hop: when the caller's current turn (`agent_status.current_turn_id`) is the `turn_id` of a message in the caller's session that has a sender, the new hop is that message's hop + 1, else 1; above `settings.session_message_max_hops`: 409 `hop_limit`;
  8. the caller's session sent `settings.session_message_rate_per_minute` or more messages (rows with that `sender_session_id`) in the last 60 seconds: 429 `rate_limited`;
  8b. pair budget (panel finding: the hop resets across turns, so the hop limit alone does not stop a two-leader ping-pong): the number of cross-session messages between the caller's session and the target session in either direction (rows with sender_session_id = caller and session_id = target, plus rows with sender_session_id = target and session_id = caller) created in the last hour is at least `settings.session_message_pair_max_per_hour`: 429 `pair_budget`;
  9. the target holds `settings.session_message_queued_max` or more queued rows with a sender: 409 `target_queue_full`.
  Text outside 1 to 16000 characters: 422 `invalid_request` (the app's validation error shape).
- DB helpers: in `src/agents_orchestrator/db/queue.py` the counts and the hop lookup (one function per SQL op); in `src/agents_orchestrator/db/sessions.py` the messaging-session listing if SQL is used.
- `openapi.json` regenerated; `README.md` documents both routes under the agent API, the codes, the limits and that the limits are advisory under concurrent sends (design D10); `MEMORY.md` dated entry for D6, D7, D10.

## Acceptance conditions

- ac1: GET /agent/v1/sessions lists only the other active sessions with session_messaging on, by slug, with preset_name and leader_present, and answers 403 messaging_disabled to a caller whose session lacks the option [evidence: test:tests/test_agent_session_messaging.py::test_list_messaging_sessions]
- ac2: the leader of a hive and the only agent of an alone session can each send to another messaging session: 202 with a message_id, and the queued row carries the sender session id, sender slug and hop 1 and is untargeted [evidence: test:tests/test_agent_session_messaging.py::test_send_queues_with_sender]
- ac3: a caller session without the option gets 403 messaging_disabled and a non-leader member of a hive gets 403 not_leader, and neither queues a row [evidence: test:tests/test_agent_session_messaging.py::test_send_refusals_for_sender]
- ac4: an unknown slug gets 404 not_found, the caller's own slug 422 self_send, a target without the option 409 target_messaging_disabled, a deleting target 409 session_deleting, and an empty or 16001-character text 422 invalid_request, each queuing no row [evidence: test:tests/test_agent_session_messaging.py::test_send_refusals_for_target]
- ac5: a send made while the caller's current turn delivered a cross-session message of hop h is stored with hop h+1, and is refused 409 hop_limit when h+1 exceeds ORCH_SESSION_MESSAGE_MAX_HOPS [evidence: test:tests/test_agent_session_messaging.py::test_hop_counter]
- ac6b: once ORCH_SESSION_MESSAGE_PAIR_MAX_PER_HOUR messages were exchanged between two sessions in either direction within the last hour, a further send between them, made from a turn that did not deliver a cross-session message (hop 1), gets 429 pair_budget while sends to a third session still succeed [evidence: test:tests/test_agent_session_messaging.py::test_pair_budget_stops_cross_turn_ping_pong]
- ac6: the send after ORCH_SESSION_MESSAGE_RATE_PER_MINUTE sends within 60 seconds gets 429 rate_limited, and a target holding ORCH_SESSION_MESSAGE_QUEUED_MAX queued cross-session messages gets 409 target_queue_full [evidence: test:tests/test_agent_session_messaging.py::test_rate_limit_and_queue_cap]
- ac7: README routes, openapi.json, the api layering pin, the agent port gate and nomenclature still pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_readme_api.py tests/test_api_sessions.py tests/test_agent_port.py tests/test_api_agent.py tests/test_nomenclature.py]
- ac8: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/api/agent.py`
- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/db/sessions.py`
- `openapi.json`
- `README.md`
- `MEMORY.md`
- `tests/test_agent_session_messaging.py`

## Interfaces

- `GET /agent/v1/sessions` -> 200 `{"sessions": [{"slug", "preset_name", "leader_present"}]}`.
- `POST /agent/v1/sessions/{slug}/messages` body `{"text"}` -> 202 `{"message_id"}`; error codes per design D7.
- Contract with any-mcp (task anymcp-session-tools): tool `sessions_list` -> `GET /agent/v1/sessions`; tool `session_send(slug, text)` -> `POST /agent/v1/sessions/{slug}/messages` with body `{"text"}`. Keep these paths exact.
- Uses `db/queue.py:enqueue_message(..., sender_session_id=, sender_slug=, hop=)` from task orch-session-message-sender.

## Expected outcome

An opted-in leader can list the other opted-in sessions and queue a message to one of them; every refusal of design D7 answers its code and queues nothing; a same-turn ping-pong stops at the hop limit, a cross-turn ping-pong at the pair budget, and a flood at the rate limit or queue cap.

## Steps

- Red: write `tests/test_agent_session_messaging.py` with the six tests named in the acceptance conditions (agent-port client fixtures as in `tests/test_api_agent.py`, `tests/test_agent_scale.py`); run `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_agent_session_messaging.py`: fails (404 routes).
- Green: add the routes and DB helpers; regenerate `openapi.json`; update README and MEMORY; run the task's verify: passes.
- Run ac7 and ac8 commands: pass.

## Notes

- Rulings and their pin tests: check order (ac3, ac4: a caller failing several checks gets the first code); self-send refused (ac4); alone session agent counts as leader (ac2); hop derived only from the caller's current turn, never from the request body (ac5, `extra="forbid"` on the body); deleting sessions excluded from the list (ac1); rate window 60 seconds counting rows of any status (ac6).
- `require_agent` already scopes the caller to its session; this is the first agent route that names another session, so look the target up by slug with `sessions_repo.get_by_slug` and never trust a session id from the body.
- Reuse: `_require_open_session` semantics (api/messages.py:52) for deleting; `leadership.current_leader` (db/leadership.py:64); `agents_repo.list_members` for live agents. The duplicated leader check and member lookup in this file (:185, :193, :324, :329) may be folded into one helper (boy-scout, same file).
- Layering pin `tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper`: api modules must not import k8s, reconciler or wrapper.
- Do not write the word "cluster" in new lines (nomenclature guard).
- Orchestrator tests need Docker; run with `VIRTUAL_ENV` unset; `uv sync` if the `.venv` shebang is stale.
