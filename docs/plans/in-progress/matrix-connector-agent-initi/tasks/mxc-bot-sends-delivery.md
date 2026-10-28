---
title: mxc bot sends delivery
status: in-progress
repo: agents-matrix-connector
value: "accepted agent messages, quoted replies and reactions reach the chat at once, exactly once, even during a running chat turn"
files: [src/agents_matrix_connector/sender.py, src/agents_matrix_connector/bot.py, src/agents_matrix_connector/db/runs.py, src/agents_matrix_connector/db/sends.py, src/agents_matrix_connector/db/bindings.py, src/agents_matrix_connector/tracker.py, tests/test_sender.py, tests/test_tracker.py]
verify: "uv run pytest tests/test_sender.py tests/test_tracker.py && mise run lint"
depends_on: [mxc-sends-schema, mxc-matrix-send-event, mxc-agent-room-policy]
model: opus
review: ""
verified_head: ""
points: 13
expected_minutes: 22
expected_tokens: 3916941
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc bot sends delivery

## Requirement

README Goals, verbatim:
- "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."
- "An agent can send several messages in a row without a user reply in between (follow-ups), including while a chat-started turn is still running."
- "An agent can reply to a specific chat message (quoted reply) and react to a message with an emoji."

Design D7, verbatim (the flow): "Flow: the api inserts `sends(queued)`; a new bot step (`sender.py`, run in the bot work loop between `Worker.tick` and `Tracker.tick`) claims queued rows `queued -> sending`, re-checks (a) (denied: `refused` with the policy reason, no outbound row) and (b) (D4; a room bound to another session, a session bound elsewhere or an unflagged unbound room: `refused` with reason `room_bound`, `session_bound` or `room_not_authorised`, no outbound row), binds an unbound flagged room to the send's session in the same transaction when (b) holds through the flag (D9), and inserts the outbound rows in the same transaction with transaction ids `mxa-<send id>-<n>` (message chunks) or `mxa-<send id>-r` (reaction); `Tracker._send_pending` sends every pending row with its own event type and content; before it sends a row of a send (kind `agent` or `reaction`) it re-checks (a) for that row's room, and when (a) now fails it marks every still-pending outbound row of that send `failed` with the policy reason and moves the send `sending -> refused` with the same reason, in one transaction, and sends nothing of it (interrogate Act 10: rows already pending while the homeserver was down are not delivered after the policy turned to deny; my call: chunks already sent stay sent); once every outbound row of a `sending` send has ended, the bot marks it `sent` (all sent, `event_id` of the first row) or `failed` (the first failed row's reason); a send that ends `failed` or `refused` with none of its outbound rows sent releases, in that transaction, the binding it created (`send_failed`, D9). Sends never wait on `inbound.rooms_ready`, so follow-ups go out while a chat run is in progress (G2). `sends` rows that ended and released `room_bindings` rows are pruned with the existing daily retention. "

User decision (final gate, 2026-10-27), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go".

Design D9, verbatim (agent initiation): "Agent initiation in an unbound flagged room: the api accepts the send (D4 (b), advisory); the bot's sender, in the transaction that claims the send `queued -> sending`, inserts the active `agent` binding (session id and slug of the send, its send id) when the room is still unbound, still flagged `agents_may_initiate` and the session still bound to no room. The unique indexes decide a race: a conflicting insert refuses the send (`room_bound` or `session_bound`), it never makes a second binding. If that send then ends with none of its outbound rows sent (`failed`, or `refused` at send time, D7), the settle transaction releases the binding it created (`send_failed`, my call: a binding message that never reached the user binds nothing). A send of a session into the room it is bound to binds nothing new."

Design D9, verbatim (conflicts): "an agent of session S trying to start a chat in a room bound to another session (or reserved by another session's first run in progress) is refused 409 `room_bound`, synchronously at the api, and at the sender's claim as `refused` with reason `room_bound` when the binding appeared after the api accepted the send; a session already bound to a room trying a second, unbound flagged room is refused 409 `session_bound` (claim: `refused`, `session_bound`). Neither stores an outbound row or changes any binding."

Design D7, verbatim (retention): "`sends` rows that ended and released `room_bindings` rows are pruned with the existing daily retention."

Design D8, verbatim: "Reply: `m.room.message` `{msgtype: m.text, body, "m.relates_to": {"m.in_reply_to": {"event_id": E}}}` on the first chunk only, with no fallback body (fallbacks are best effort since MSC3676; removal proposed in MSC2781). Reaction: `m.reaction` `{"m.relates_to": {"rel_type": "m.annotation", "event_id": E, "key": <emoji>}}`. `MatrixClient.send_event(room_id, event_type, txn_id, content)` is the one PUT; `send_text` becomes a call of it."

Design D4, verbatim (the checks): "(a) R is policy-allowed for agent sends, checked when the api accepts the request, when the bot claims the send, and again right before each of its outbound rows is sent to the homeserver". "(a) defined [...] R is policy-allowed for agent sends when a room or alias rule allows it, or when the inbound policy would accept a message from at least one current non-bot member of R; any member matching a deny rule denies. [...] One function, `api/rooms.py:agent_room_decision(room, rule_list, settings) -> policy.Decision` [...] serves the api checks, the listing, the bot's claim and the send-time check (task mxc-agent-room-policy)."

Design D5, verbatim (chunking): "`text`: 1 to 16000 characters (same bound as `session_send`); split into chunks of `MATRIX_REPLY_CHUNK_CHARS` with `chunks.split`."

Interrogate verdict Act on 5, verbatim: "Tracker test spy (A high): mxc-bot-sends-delivery switches Tracker._send_pending to send_event but tests/test_tracker.py (SpyMatrix has only send_text/typing) is not in its files while ac10 demands it unchanged. Add the file and let the spy gain send_event; ac10 becomes "existing assertions unchanged"."

Interrogate verdict Act on 10, verbatim: "Policy re-check at send time (C medium): agent outbound rows already pending are delivered after a policy flip to deny when the homeserver was down. Re-check (a) when sending agent rows; refuse them (sends -> refused, reason policy) otherwise."

Scope (agents-matrix-connector): new bot module `sender.py` (claim, policy re-check through `agent_room_decision`, the binding re-check and the initiation binding through `db/bindings.py`, outbound rows, settle and the release of a failed initiation), its place in `bot.py:_work_loop` (worker, sender, tracker), `db/runs.py` (`OutboundRow` and `add_outbound` carry `send_id`, `event_type`, `relates_to` and the `agent`/`reaction` kinds with `mxa-` txn ids), any queries in `db/sends.py`, `tracker.py` (`_send_pending` sends each row with its event type and content through `send_event` and re-checks (a) before each agent row; `_prune_daily` prunes ended sends and released bindings), `tests/test_sender.py`, `tests/test_tracker.py` (`SpyMatrix` gains `send_event`; its existing assertions unchanged). `MatrixClient.send_event` comes from mxc-matrix-send-event and `agent_room_decision` from mxc-agent-room-policy. The existing reply and notice path is unchanged.

## Acceptance conditions

- ac1: a queued message send into the room bound to its session becomes sending with outbound rows mxa-<id>-1..n of kind agent, the reply relation only on the first chunk and no fallback body, and the homeserver receives them in order [evidence: test:tests/test_sender.py::test_message_send_chunks_and_reply_relation]
- ac2: a queued reaction becomes one outbound row mxa-<id>-r of event type m.reaction with an m.annotation relation and the key, and the homeserver receives that content [evidence: test:tests/test_sender.py::test_reaction_send]
- ac3: at claim, a send whose room fails (a) through agent_room_decision (a member now matches a deny rule, or the room's allow rule was removed) is refused with the policy reason and gets no outbound row, while a room allowed only through a current member's facebook rule is delivered [evidence: test:tests/test_sender.py::test_policy_recheck_refuses]
- ac4: at claim, a send to an unbound flagged room from a session bound to no room binds that room to the send's session (origin agent, the send's id and slug) in the claim transaction and is delivered [evidence: test:tests/test_sender.py::test_claim_binds_unbound_flagged_room]
- ac5: at claim, a send whose room is now bound to or reserved by another session is refused room_bound, one whose session is now bound to another room session_bound, and one to an unbound room no longer flagged room_not_authorised; two queued sends of two sessions to one unbound flagged room bind it to the first claimed and refuse the other room_bound; none of the refused gets an outbound row or changes a binding [evidence: test:tests/test_sender.py::test_claim_refuses_binding_conflicts]
- ac6: a send that bound its room and ends failed or refused with none of its outbound rows sent releases that binding with reason send_failed in the settle transaction; one with a sent chunk keeps it, and a failed send into an already bound room releases nothing [evidence: test:tests/test_sender.py::test_failed_initiation_releases_binding]
- ac7: a send whose outbound rows are still pending when (a) turns to deny (the homeserver was down, then a deny rule was added) sends nothing further: its pending rows are failed with the policy reason and the send becomes refused with it, while reply and notice rows of runs are sent as before [evidence: test:tests/test_tracker.py::test_agent_rows_rechecked_before_send]
- ac8: a sending send becomes sent with the first row's event id once all its rows are sent, and failed with the first failed row's reason when one failed [evidence: test:tests/test_sender.py::test_settle_sent_and_failed]
- ac9: sends to a room whose chat run is still in progress are delivered before that run ends [evidence: test:tests/test_sender.py::test_sends_go_out_during_running_chat_run]
- ac10: a restart between the homeserver send and the sent mark resends the same txn id and the room gets each event once [evidence: test:tests/test_sender.py::test_restart_exactly_once]
- ac11: the bot work loop runs the worker, the sender and the tracker in that order each interval, and a sender failure other than a lost token does not stop the loop [evidence: test:tests/test_sender.py::test_bot_loop_runs_sender_between_worker_and_tracker]
- ac12: the daily prune also deletes ended sends and released bindings older than the retention [evidence: test:tests/test_sender.py::test_daily_prune_includes_sends]
- ac13: the tracker sends reply and notice rows through send_event with the m.room.message content send_text sent, the test SpyMatrix records send_event calls, and the existing tracker test assertions are unchanged [evidence: command:uv run pytest tests/test_tracker.py]
- ac14: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_sender.py tests/test_tracker.py && mise run lint]

## Files

- `src/agents_matrix_connector/sender.py`
- `src/agents_matrix_connector/bot.py`
- `src/agents_matrix_connector/db/runs.py`
- `src/agents_matrix_connector/db/sends.py`
- `src/agents_matrix_connector/db/bindings.py`
- `src/agents_matrix_connector/tracker.py`
- `tests/test_sender.py`
- `tests/test_tracker.py`

## Interfaces

- Uses `matrix.py:MatrixClient.send_event(room_id, event_type, txn_id, content) -> str` (mxc-matrix-send-event) and `api/rooms.py:agent_room_decision(room, rule_list, settings) -> policy.Decision` (mxc-agent-room-policy).
- `sender.py` (new): `class Sender(matrix, pool, settings, *, now=utcnow)` with `async tick()`: claim queued sends; per send, in its claim transaction, re-check (a) through `agent_room_decision`, then (b) through `db/bindings.py` (`active_for_room`, `active_for_session`, the room flag, and `bind_for_send` for an unbound flagged room), refusing `room_bound`, `session_bound` or `room_not_authorised`; insert outbound rows; settle sending sends whose rows all ended, releasing (`send_failed`) a binding the send created when none of its rows was sent.
- `tracker.py:Tracker._prune_daily` also calls `sends.prune` and `bindings.prune_released` with the existing retention.
- `db/runs.py:add_outbound(conn, *, room_id, run_id=None, send_id=None, kind, chunks, event_type="m.room.message", relates_to=None)`; txn ids `mxc-<run>-<n>`, `mxc-<run>-notice` (unchanged), `mxa-<send>-<n>`, `mxa-<send>-r`. `OutboundRow` gains `send_id`, `event_type`, `relates_to`.
- `tracker.py:Tracker._send_pending` builds each row's content from `event_type`, `body` and `relates_to` and calls `send_event`; for a row with a `send_id` it first re-checks (a) for the row's room (rules and the room loaded once per pass) and, when denied, fails the send's pending rows, moves the send `sending -> refused` with the policy reason and, when none of its rows was sent, releases a binding the send created (`send_failed`), in one transaction.
- `tests/test_tracker.py:SpyMatrix` gains `send_event`, recording `(room_id, event_type, txn_id, content)`.

## Expected outcome

Every accepted agent send reaches the room as a message (chunked, optionally a quoted reply) or a reaction, exactly once, at once, even while a chat run is in progress, and its status reports how it ended; an initiation binds its room to its session at claim, a send that lost a binding race is refused before anything is sent, and an initiation that never reached the user leaves the room unbound.

## Steps

- Red: write `tests/test_sender.py`, add `test_agent_rows_rechecked_before_send` and the `SpyMatrix.send_event` spy to `tests/test_tracker.py`; run `uv run pytest tests/test_sender.py tests/test_tracker.py`: the new tests fail.
- Green: `db/runs.py`, `db/sends.py`, `db/bindings.py` (only if a query is missing), `sender.py`, `tracker.py`, `bot.py`; run the task's verify: passes. Quote the summary line with counts.

## Notes

- Reuse `MatrixClient._request` and its error taxonomy, `chunks.split`, the deterministic txn-id scheme and `Tracker._send_pending`'s ordering (an unavailable homeserver stops the pass; a lost token propagates) (discovery "reuse").
- The fake homeserver's `_send` (`fake_homeserver.py`) already accepts any event type and records content: assert relations on what it recorded.
- Typing stays keyed by run id; agent sends neither start nor stop typing.
- Every (a) check (claim and send time) calls `api/rooms.py:agent_room_decision` with `rules.list_rules` and the settings, the same function as the api; never `policy.evaluate` on the room subject alone (interrogate Act 2).
- The bot is the only mover of `sends` and the only writer of `outbound` and `room_bindings` (D7, D9); every status move goes through `queue.transition`. A unique-index conflict in `bind_for_send` is mapped to a refusal inside a savepoint, so the claim transaction of the other sends in the batch survives.
- `tests/test_sender.py` and `tests/test_tracker.py` are DB-backed (CI). Keep the content builder (event type, body, relation) a pure function with a non-DB test in `tests/test_sender.py` so the local run has signal.
- `tests/test_tracker.py`: the spy gains `send_event`; no existing assertion is edited (interrogate Act 5).

- 2026-10-27 amended: interrogate.md Acts 2, 5, 10: member-aware (a) at claim and send time, tests/test_tracker.py added with a send_event spy, send_event split out to mxc-matrix-send-event

- 2026-10-27 amended: final gate 2026-10-27: hard 1:1 room-session binding replaces last-speaker routing (D9): binding at claim, claim-time refusals, release of a failed initiation, prune
