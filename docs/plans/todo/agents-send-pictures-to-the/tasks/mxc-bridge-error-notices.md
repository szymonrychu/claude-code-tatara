---
title: mxc bridge error notices
status: todo
repo: agents-matrix-connector
value: "a send the bridge could not deliver to Messenger shows failed with the bridge's reason instead of a silent sent"
files: [src/agents_matrix_connector/discovery.py, src/agents_matrix_connector/sync.py, src/agents_matrix_connector/db/runs.py, src/agents_matrix_connector/db/sends.py, README.md, MEMORY.md, tests/test_discovery.py, tests/test_sync.py]
verify: "uv run --frozen pytest tests/test_discovery.py tests/test_sync.py tests/test_readme_api.py && mise run lint"
depends_on: [mxc-bot-image-upload]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1901552
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc bridge error notices

## Requirement

README Goal G4, verbatim: "limits and failures are explicit: unsupported type, too large, missing file and rate (5 pictures a minute per session inside the 20 sends a minute) refuse synchronously with a named error; upload failures and bridge error notices mark the send failed, visible in orchestrator_chat_status."

Design D6, verbatim: "Before the bridge-bot skip in the sync loop (discovery.py:132, sync.py:470), the bot checks one thing: a bridge-bot `m.notice` whose `m.relates_to.m.in_reply_to.event_id` equals a sent outbound row of an agent send. On a match the outbound row goes sent->failed and the send sent->failed with reason `bridge: <notice body>`, both guarded; orchestrator_chat_status shows it. Applies to all agent sends, not only images. parse_message stays unchanged. User Q6."

Open question Q6 (planned on its recommended answer): "A bridge error notice marks any agent send failed, text included? [recommended: yes]"

brief-docs fix-as-ac, verbatim: "The connector stops ignoring the bridge bot's error `m.notice` for its own outbound images (at least logs/records the failure for that run); today `discovery.py:132` drops it, so a failed bridge is silent."

brief-cartographer fix-as-ac, verbatim: "Inbound non-text messages are dropped silently (`discovery.py:141`, `sync.py:515` `unsupported_content`): if pictures add an image event kind, keep inbound images classified explicitly (not a regression of the ignore path)."

Scope (agents-matrix-connector):
- `discovery.py`: a pure `bridge_notice_reply(event, bridge_bots) -> tuple[str, str] | None`: the replied event id and the body of an `m.room.message` from a bridge bot with msgtype `m.notice` and a string `m.relates_to.m.in_reply_to.event_id`. `parse_message` unchanged.
- `sync.py`: in the room timeline pass, before `parse_message` skips the event, a match fails the outbound row carrying that `event_id` when it is `sent` and belongs to a send (guarded `sent -> failed`), and, when that send is `sent`, the send too (guarded `sent -> failed`), reason `bridge: <body>` truncated to 500 characters (my call: bounded status text), in the sync transaction. A send still `sending` is failed by the sender's settle from the failed row, keeping its binding (review fix below). A notice replying to a run's reply or notice, an unknown event or an already failed row changes nothing. No binding changes (my call: the event reached the room). No inbound row is stored for the notice (as today).
- `db/runs.py`: the guarded outbound `sent -> failed` by event id for send rows. `db/sends.py`: the guarded send `sent -> failed`.
- README: the reason `bridge: <notice body>` and the behaviour; MEMORY.md: the sync loop writes these two transitions inside the one bot process under the singleton lock (bot.py), so the bot stays the one writer of `outbound` and `sends` transitions; the table comments stay.

Review fix, interrogate 2026-10-29 Act on 2 (bridge notice vs settle binding release is timing-dependent), verbatim: "a row failed by a bridge notice counts as having reached the room for the binding: settle releases the initiation only when no row reached the room; AC covers both orders." For this task: a row reached the room when it carries an `event_id` (sent, or failed by a bridge notice); `sends.ended` reports that count and `Sender._settle` (sender.py, today `done.sent == 0`) calls `release_initiation` only when it is 0, so a notice that fails the only row keeps the binding whether it lands while the send is still `sending` or after settle marked it `sent`. `refuse_sending`'s count and `release_initiation`'s later-send check use the same reached rule (my call: one rule for every release decision, so no order of notice and tracker changes the binding).

## Acceptance conditions

- ac1: bridge_notice_reply returns the replied event id and body for a bridge-bot m.notice with m.in_reply_to, and None for another sender, m.text, no relation or a non-string id (pure test) [evidence: test:tests/test_discovery.py::test_bridge_notice_reply]
- ac2: parse_message is unchanged: bridge-bot events stay Skip and an inbound m.image stays Unsupported, the existing test passing unedited [evidence: test:tests/test_discovery.py::test_parse_message]
- ac3: a bridge notice replying to a sent row of a sent agent send fails the row and the send with reason "bridge: <body>", for a message send and an image send, and GET /chat/v1/messages/s<n> shows failed with that reason [evidence: test:tests/test_sync.py::test_bridge_notice_fails_agent_send]
- ac4: a notice replying to a row of a send still sending fails the row, and the sender's settle then fails the send with that reason without releasing its binding [evidence: test:tests/test_sync.py::test_bridge_notice_during_sending]
- ac5: a notice replying to a run reply, an unknown event or an already failed row changes nothing, stores no inbound row and changes no binding [evidence: test:tests/test_sync.py::test_bridge_notice_ignored_otherwise]
- ac6: README names the reason and MEMORY.md records the writer ruling [evidence: command:grep -qF '`bridge: ' README.md && grep -q 'bridge notice' MEMORY.md]
- ac7: the targeted tests and lint pass (DB tests in CI) [evidence: command:uv run --frozen pytest tests/test_discovery.py tests/test_sync.py tests/test_readme_api.py && mise run lint]
- ac8: both orders keep the binding: an agent-initiated send whose only row is failed by a bridge notice keeps the room bound to its session when the notice lands before settle (send sending) and when it lands after settle (send sent); a send whose only row failed without an event id still releases its binding as today [evidence: test:tests/test_sync.py::test_bridge_notice_keeps_binding_either_order]

## Files

- `src/agents_matrix_connector/discovery.py`
- `src/agents_matrix_connector/sync.py`
- `src/agents_matrix_connector/db/runs.py`
- `src/agents_matrix_connector/db/sends.py`
- `README.md`
- `MEMORY.md`
- `tests/test_discovery.py`
- `tests/test_sync.py`

## Interfaces

- `discovery.bridge_notice_reply(event: dict, bridge_bots: Sequence[str]) -> tuple[str, str] | None`.
- `db/runs.py`: guarded outbound `sent -> failed` by event id for send rows; `db/sends.py`: guarded `sent -> failed`.
- Reason text `bridge: <notice body>` (at most 500 characters of body).

## Expected outcome

A picture or message the bridge could not deliver to Messenger shows as failed with the bridge's words in `orchestrator_chat_status`, instead of a silent `sent`.

## Steps

- Red: `test_bridge_notice_reply` (pure) and the three sync tests (the fake homeserver's `post` injects the bridge notice into the timeline); run `uv run --frozen pytest tests/test_discovery.py`: fails (no function); the sync tests error locally.
- Green: the helper, the sync-loop check, the two guarded transitions, README and MEMORY.md; run the task's verify; quote the local summary line and the CI run.

## Notes

- DB-backed tests (testcontainers Postgres) need Docker; agent pods have none, so they error here (baseline 2026-10-29: 182 Docker errors) and CI on the PR is the gate for them (recurring retro). Run the verify, quote the local summary line and the CI run of the pushed head. Keep each pure helper covered by a non-DB test so the local run has signal.
- The notice shape is mautrix/go bridgev2 `messagestatus.go` `ToNoticeEvent` (`SetReplyTo(SourceEventID)`), per brief-docs; the bridge bot ids come from `MATRIX_BRIDGE_BOTS`.
- The check runs before the bridge-bot skip and does not change what `parse_message` returns (D6).
- Shared files with mxc-send-images-schema and mxc-bot-image-upload (`db/runs.py`, `db/sends.py`, README, MEMORY.md): build on their commits.

- 2026-10-29 amended: interrogate 2026-10-29 act on 2
