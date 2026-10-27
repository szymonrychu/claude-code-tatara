# Interrogate verdict: matrix-connector-agent-initi plan (2026-10-27)

Panel: A fable, B opus, C sonnet. Lead: orchestrator session. Agreement: all three accept the entry point, token handling, single-writer sends queue and deterministic mxa- txn ids; they converge on the failed-send suppression (A,B,C), the preset contradiction (B,C) and the sender-None policy evaluation (A,C).

## Act on (amend the plan before the gate)
1. Preset contradiction (B,C high): D9/mxc-route-last-speaker keep `no_preset` before routing while B5/Q9 promise routing to a running last speaker without a preset. Build B5: routing to a running last speaker happens before the preset check; a preset is needed only to start a new mx- session; follow runs need a non-null runs.preset_id: use the target session's preset (GET /api/v1/sessions/{id}); if that is null too, define the value explicitly (no NOT NULL violation possible). ACs pin both paths.
2. Policy for agent sends with sender None (A,C high/medium): `policy.evaluate(_room_subject(room))` makes rooms allowed only by facebook:/user: rules default-deny for agents, and ignores deny rules on members. Define D4(a) precisely (my call): a room is policy-allowed for agent sends when a room/alias rule allows it, or when the inbound policy would accept a message from at least one current non-bot member; any member matching a deny rule denies. ACs: room allowed via facebook: rule passes; group with a denied member fails under default allow.
3. Failed send suppresses the final answer (A,B,C medium): D10 matching must count only sends that reached the user. My call: match only `sent` sends; a matching send still `queued`/`sending` when the final answer is ready delays the close until it settles (bounded by the run timeout), and if it ends `failed` the final answer is posted. AC for failed and for queued-then-failed.
4. Reaction and reply room authorisation (A high): ACs proving a reaction, and a reply whose room comes from `reply_to`, are refused when the referenced message's room fails (a) or (b), including `m<n>` ids of ignored inbound rows in denied rooms.
5. Tracker test spy (A high): mxc-bot-sends-delivery switches Tracker._send_pending to send_event but tests/test_tracker.py (SpyMatrix has only send_text/typing) is not in its files while ac10 demands it unchanged. Add the file and let the spy gain send_event; ac10 becomes "existing assertions unchanged".
6. Size caps (A,C medium): 16000 characters can exceed the orchestrator's 32 KiB body cap. Make the relay cap cover the worst case (4 bytes per character plus JSON overhead, e.g. 80 KiB) with an AC sending 16000 4-byte characters end to end.
7. Preamble lost on resume (B medium): Worker._resume renders first=False; a follow run into a session new to the room must keep the PREAMBLE on the retry path too, excluding the run itself from "no earlier run in this room". Add Worker._resume to the task and an AC.
8. Last-speaker ordering (B medium): order by when each speaker last spoke in the room: a run counts at its final answer's delivery (outbound sent_at) or its start when no answer was posted yet; a send at its sent_at. AC for: chat run starts, session B sends, chat answer posts, user replies -> chat session.
9. Duplicate send on timeout retry (C medium): an agent retrying after 503 chat_unavailable can post twice. My call: the connector returns the existing s<n> (no new row) for an identical (session, room, kind, text or key, reply_to) queued or sent within the last 60 s. AC.
10. Policy re-check at send time (C medium): agent outbound rows already pending are delivered after a policy flip to deny when the homeserver was down. Re-check (a) when sending agent rows; refuse them (sends -> refused, reason policy) otherwise.

## Consider (to the user at the gate)
- Binding never expires (C; A declined): a session that posted once stays bound; turning the flag off does not unbind. Revocation is a deny rule or deleting the session. Q10.
- Busy hive leader as last speaker (C): the user's answer is delivered as a follow message, but the reply tracking times out after 30 min and holds later messages in that room (rooms_ready) meanwhile. Covered by rewording Q2.
- "While it runs" means the session exists with desired state active, not mid-turn (A). Reword Q2.

## Noted
- Error codes reveal whether an m<n> id exists and whether its room passes policy: minor.
- Token-only agent port reachable by any in-cluster pod: 256-bit token, same as the orchestrator service port.
- Reaction outbound rows shown as messages in the UI feed: cosmetic.

## Dismissed
- Policy flip between claim and send as "same window as today": superseded by Act 10.
