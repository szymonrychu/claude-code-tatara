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

Design D7, verbatim (the flow): "Flow: the api inserts `sends(queued)`; a new bot step (`sender.py`, run in the bot work loop between `Worker.tick` and `Tracker.tick`) claims queued rows `queued -> sending`, re-checks (a) (denied: `refused` with the policy reason, no outbound row), and inserts the outbound rows in the same transaction with transaction ids `mxa-<send id>-<n>` (message chunks) or `mxa-<send id>-r` (reaction); `Tracker._send_pending` sends every pending row with its own event type and content; once every outbound row of a `sending` send has ended, the bot marks it `sent` (all sent, `event_id` of the first row) or `failed` (the first failed row's reason). Sends never wait on `inbound.rooms_ready`, so follow-ups go out while a chat run is in progress (G2). `sends` rows that ended are pruned with the existing daily retention."

Design D8, verbatim: "Reply: `m.room.message` `{msgtype: m.text, body, "m.relates_to": {"m.in_reply_to": {"event_id": E}}}` on the first chunk only, with no fallback body (fallbacks are best effort since MSC3676; removal proposed in MSC2781). Reaction: `m.reaction` `{"m.relates_to": {"rel_type": "m.annotation", "event_id": E, "key": <emoji>}}`. `MatrixClient.send_event(room_id, event_type, txn_id, content)` is the one PUT; `send_text` becomes a call of it."

Design D4, verbatim (delivery re-check): "(a) `policy.evaluate(room subject R)` is allow, checked when the api accepts the request and again when the bot delivers it".

Design D5, verbatim (chunking): "`text`: 1 to 16000 characters (same bound as `session_send`); split into chunks of `MATRIX_REPLY_CHUNK_CHARS` with `chunks.split`."

Scope (agents-matrix-connector): new bot module `sender.py` (claim, policy re-check, outbound rows, settle), its place in `bot.py:_work_loop` (worker, sender, tracker), `matrix.py:send_event`, `db/runs.py` (`OutboundRow` and `add_outbound` carry `send_id`, `event_type`, `relates_to` and the `agent`/`reaction` kinds with `mxa-` txn ids), any queries in `db/sends.py`, `tracker.py` (`_send_pending` sends each row with its event type and content; `_prune_daily` prunes ended sends). The existing reply and notice path is unchanged.

## Acceptance conditions

- ac1: `MatrixClient.send_event` PUTs the given event type, txn id and content and returns the event id, and `send_text` sends the same request it sent before through it [evidence: test:tests/test_matrix_client.py::test_send_event_type_and_content]
- ac2: a queued message send becomes sending with outbound rows mxa-<id>-1..n of kind agent, the reply relation only on the first chunk and no fallback body, and the homeserver receives them in order [evidence: test:tests/test_sender.py::test_message_send_chunks_and_reply_relation]
- ac3: a queued reaction becomes one outbound row mxa-<id>-r of event type m.reaction with an m.annotation relation and the key, and the homeserver receives that content [evidence: test:tests/test_sender.py::test_reaction_send]
- ac4: a send whose room the policy denies at delivery is refused with the policy reason and gets no outbound row [evidence: test:tests/test_sender.py::test_policy_recheck_refuses]
- ac5: a sending send becomes sent with the first row's event id once all its rows are sent, and failed with the first failed row's reason when one failed [evidence: test:tests/test_sender.py::test_settle_sent_and_failed]
- ac6: sends to a room whose chat run is still in progress are delivered before that run ends [evidence: test:tests/test_sender.py::test_sends_go_out_during_running_chat_run]
- ac7: a restart between the homeserver send and the sent mark resends the same txn id and the room gets each event once [evidence: test:tests/test_sender.py::test_restart_exactly_once]
- ac8: the bot work loop runs the worker, the sender and the tracker in that order each interval, and a sender failure other than a lost token does not stop the loop [evidence: test:tests/test_sender.py::test_bot_loop_runs_sender_between_worker_and_tracker]
- ac9: the daily prune also deletes ended sends older than the retention [evidence: test:tests/test_sender.py::test_daily_prune_includes_sends]
- ac10: the existing tracker behaviour (replies, notices, typing, send errors, prune) is unchanged [evidence: command:uv run pytest tests/test_tracker.py]
- ac11: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_sender.py tests/test_matrix_client.py tests/test_tracker.py && mise run lint]

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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
