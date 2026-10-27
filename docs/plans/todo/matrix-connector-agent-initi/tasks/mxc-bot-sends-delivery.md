---
title: mxc bot sends delivery
status: todo
repo: agents-matrix-connector
value: "accepted agent messages, quoted replies and reactions reach the chat at once, exactly once, even during a running chat turn"
files: [src/agents_matrix_connector/sender.py, src/agents_matrix_connector/bot.py, src/agents_matrix_connector/matrix.py, src/agents_matrix_connector/db/runs.py, src/agents_matrix_connector/db/sends.py, src/agents_matrix_connector/tracker.py, tests/test_sender.py, tests/test_matrix_client.py]
verify: "uv run pytest tests/test_sender.py tests/test_matrix_client.py tests/test_tracker.py && mise run lint"
depends_on: [mxc-sends-schema]
model: opus
review: ""
verified_head: ""
points: 8
expected_minutes: 14
expected_tokens: 3155191
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

Design D7, verbatim (the flow): "Flow: the api inserts `sends(queued)`; a new bot step (`sender.py`, run in the bot work loop between `Worker.tick` and `Tracker.tick`) claims queued rows `queued -> sending`, re-checks (a) (denied: `refused` with the policy reason, no outbound row), and inserts the outbound rows in the same transaction with transaction ids `mxa-<send id>-<n>` (message chunks) or `mxa-<send id>-r` (reaction); `Tracker._send_pending` sends every pending row with its own event type and content; before it sends a row of a send (kind `agent` or `reaction`) it re-checks (a) for that row's room, and when (a) now fails it marks every still-pending outbound row of that send `failed` with the policy reason and moves the send `sending -> refused` with the same reason, in one transaction, and sends nothing of it (interrogate Act 10: rows already pending while the homeserver was down are not delivered after the policy turned to deny; my call: chunks already sent stay sent); once every outbound row of a `sending` send has ended, the bot marks it `sent` (all sent, `event_id` of the first row) or `failed` (the first failed row's reason). Sends never wait on `inbound.rooms_ready`, so follow-ups go out while a chat run is in progress (G2). `sends` rows that ended are pruned with the existing daily retention."

Design D8, verbatim: "Reply: `m.room.message` `{msgtype: m.text, body, "m.relates_to": {"m.in_reply_to": {"event_id": E}}}` on the first chunk only, with no fallback body (fallbacks are best effort since MSC3676; removal proposed in MSC2781). Reaction: `m.reaction` `{"m.relates_to": {"rel_type": "m.annotation", "event_id": E, "key": <emoji>}}`. `MatrixClient.send_event(room_id, event_type, txn_id, content)` is the one PUT; `send_text` becomes a call of it."

Design D4, verbatim (the checks): "(a) R is policy-allowed for agent sends, checked when the api accepts the request, when the bot claims the send, and again right before each of its outbound rows is sent to the homeserver". "(a) defined [...] R is policy-allowed for agent sends when a room or alias rule allows it, or when the inbound policy would accept a message from at least one current non-bot member of R; any member matching a deny rule denies. [...] One function, `api/rooms.py:agent_room_decision(room, rule_list, settings) -> policy.Decision` [...] serves the api checks, the listing, the bot's claim and the send-time check (task mxc-agent-room-policy)."

Design D5, verbatim (chunking): "`text`: 1 to 16000 characters (same bound as `session_send`); split into chunks of `MATRIX_REPLY_CHUNK_CHARS` with `chunks.split`."

Interrogate verdict Act on 5, verbatim: "Tracker test spy (A high): mxc-bot-sends-delivery switches Tracker._send_pending to send_event but tests/test_tracker.py (SpyMatrix has only send_text/typing) is not in its files while ac10 demands it unchanged. Add the file and let the spy gain send_event; ac10 becomes "existing assertions unchanged"."

Interrogate verdict Act on 10, verbatim: "Policy re-check at send time (C medium): agent outbound rows already pending are delivered after a policy flip to deny when the homeserver was down. Re-check (a) when sending agent rows; refuse them (sends -> refused, reason policy) otherwise."

Scope (agents-matrix-connector): new bot module `sender.py` (claim, policy re-check through `agent_room_decision`, outbound rows, settle), its place in `bot.py:_work_loop` (worker, sender, tracker), `db/runs.py` (`OutboundRow` and `add_outbound` carry `send_id`, `event_type`, `relates_to` and the `agent`/`reaction` kinds with `mxa-` txn ids), any queries in `db/sends.py`, `tracker.py` (`_send_pending` sends each row with its event type and content through `send_event` and re-checks (a) before each agent row; `_prune_daily` prunes ended sends), `tests/test_sender.py`, `tests/test_tracker.py` (`SpyMatrix` gains `send_event`; its existing assertions unchanged). `MatrixClient.send_event` comes from mxc-matrix-send-event and `agent_room_decision` from mxc-agent-room-policy. The existing reply and notice path is unchanged.

## Acceptance conditions

- ac1: a queued message send becomes sending with outbound rows mxa-<id>-1..n of kind agent, the reply relation only on the first chunk and no fallback body, and the homeserver receives them in order [evidence: test:tests/test_sender.py::test_message_send_chunks_and_reply_relation]
- ac2: a queued reaction becomes one outbound row mxa-<id>-r of event type m.reaction with an m.annotation relation and the key, and the homeserver receives that content [evidence: test:tests/test_sender.py::test_reaction_send]
- ac3: at claim, a send whose room fails (a) through agent_room_decision (a member now matches a deny rule, or the room's allow rule was removed) is refused with the policy reason and gets no outbound row, while a room allowed only through a current member's facebook rule is delivered [evidence: test:tests/test_sender.py::test_policy_recheck_refuses]
- ac4: a send whose outbound rows are still pending when (a) turns to deny (the homeserver was down, then a deny rule was added) sends nothing further: its pending rows are failed with the policy reason and the send becomes refused with it, while reply and notice rows of runs are sent as before [evidence: test:tests/test_tracker.py::test_agent_rows_rechecked_before_send]
- ac5: a sending send becomes sent with the first row's event id once all its rows are sent, and failed with the first failed row's reason when one failed [evidence: test:tests/test_sender.py::test_settle_sent_and_failed]
- ac6: sends to a room whose chat run is still in progress are delivered before that run ends [evidence: test:tests/test_sender.py::test_sends_go_out_during_running_chat_run]
- ac7: a restart between the homeserver send and the sent mark resends the same txn id and the room gets each event once [evidence: test:tests/test_sender.py::test_restart_exactly_once]
- ac8: the bot work loop runs the worker, the sender and the tracker in that order each interval, and a sender failure other than a lost token does not stop the loop [evidence: test:tests/test_sender.py::test_bot_loop_runs_sender_between_worker_and_tracker]
- ac9: the daily prune also deletes ended sends older than the retention [evidence: test:tests/test_sender.py::test_daily_prune_includes_sends]
- ac10: the tracker sends reply and notice rows through send_event with the m.room.message content send_text sent, the test SpyMatrix records send_event calls, and the existing tracker test assertions are unchanged [evidence: command:uv run pytest tests/test_tracker.py]
- ac11: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_sender.py tests/test_tracker.py && mise run lint]

## Files

- `src/agents_matrix_connector/sender.py`
- `src/agents_matrix_connector/bot.py`
- `src/agents_matrix_connector/matrix.py`
- `src/agents_matrix_connector/db/runs.py`
- `src/agents_matrix_connector/db/sends.py`
- `src/agents_matrix_connector/tracker.py`
- `tests/test_sender.py`
- `tests/test_matrix_client.py`

## Interfaces

- `matrix.py:MatrixClient.send_event(room_id: str, event_type: str, txn_id: str, content: dict) -> str`; `send_text(room_id, txn_id, body)` calls it with `m.room.message` and `{"msgtype": "m.text", "body": body}`.
- `sender.py` (new): `class Sender(matrix, pool, settings, *, now=utcnow)` with `async tick()`: claim queued sends, re-check policy, insert outbound rows, settle sending sends whose rows all ended.
- `db/runs.py:add_outbound(conn, *, room_id, run_id=None, send_id=None, kind, chunks, event_type="m.room.message", relates_to=None)`; txn ids `mxc-<run>-<n>`, `mxc-<run>-notice` (unchanged), `mxa-<send>-<n>`, `mxa-<send>-r`. `OutboundRow` gains `send_id`, `event_type`, `relates_to`.
- `tracker.py:Tracker._send_pending` builds each row's content from `event_type`, `body` and `relates_to` and calls `send_event`.

## Expected outcome

Every accepted agent send reaches the room as a message (chunked, optionally a quoted reply) or a reaction, exactly once, at once, even while a chat run is in progress, and its status reports how it ended.

## Steps

- Red: write `tests/test_sender.py`, add `test_send_event_type_and_content`; run `uv run pytest tests/test_sender.py tests/test_matrix_client.py`: the new tests fail.
- Green: `matrix.py`, `db/runs.py`, `db/sends.py`, `sender.py`, `tracker.py`, `bot.py`; run the task's verify: passes. Quote the summary line with counts.

## Notes

- Reuse `MatrixClient._request` and its error taxonomy, `chunks.split`, the deterministic txn-id scheme and `Tracker._send_pending`'s ordering (an unavailable homeserver stops the pass; a lost token propagates) (discovery "reuse").
- The fake homeserver's `_send` (`fake_homeserver.py`) already accepts any event type and records content: assert relations on what it recorded.
- Typing stays keyed by run id; agent sends neither start nor stop typing.
- The policy re-check uses the same room subject as the api (`api/rooms.py:_room_subject`) and `rules.list_rules`.
- The bot is the only mover of `sends` and the only writer of `outbound` (D7); every status move goes through `queue.transition`.
- `tests/test_sender.py` and `tests/test_tracker.py` are DB-backed (CI). `test_matrix_client.py` runs locally.

- 2026-10-27 amended: interrogate.md Acts 2, 5, 10: member-aware (a) at claim and send time, tests/test_tracker.py added with a send_event spy, send_event split out to mxc-matrix-send-event
