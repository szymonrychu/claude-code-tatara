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
- `sync.py`: in the room timeline pass, before `parse_message` skips the event, a match fails the outbound row carrying that `event_id` when it is `sent` and belongs to a send (guarded `sent -> failed`), and, when that send is `sent`, the send too (guarded `sent -> failed`), reason `bridge: <body>` truncated to 500 characters (my call: bounded status text), in the sync transaction. A send still `sending` is failed by the sender's settle from the failed row. A notice replying to a run's reply or notice, an unknown event or an already failed row changes nothing. No binding changes (my call: the event reached the room). No inbound row is stored for the notice (as today).
- `db/runs.py`: the guarded outbound `sent -> failed` by event id for send rows. `db/sends.py`: the guarded send `sent -> failed`.
- README: the reason `bridge: <notice body>` and the behaviour; MEMORY.md: the sync loop writes these two transitions inside the one bot process under the singleton lock (bot.py), so the bot stays the one writer of `outbound` and `sends` transitions; the table comments stay.

## Acceptance conditions

- ac1: bridge_notice_reply returns the replied event id and body for a bridge-bot m.notice with m.in_reply_to, and None for another sender, m.text, no relation or a non-string id (pure test) [evidence: test:tests/test_discovery.py::test_bridge_notice_reply]
- ac2: parse_message is unchanged: bridge-bot events stay Skip and an inbound m.image stays Unsupported, the existing test passing unedited [evidence: test:tests/test_discovery.py::test_parse_message]
- ac3: a bridge notice replying to a sent row of a sent agent send fails the row and the send with reason "bridge: <body>", for a message send and an image send, and GET /chat/v1/messages/s<n> shows failed with that reason [evidence: test:tests/test_sync.py::test_bridge_notice_fails_agent_send]
- ac4: a notice replying to a row of a send still sending fails the row, and the sender's settle then fails the send with that reason [evidence: test:tests/test_sync.py::test_bridge_notice_during_sending]
- ac5: a notice replying to a run reply, an unknown event or an already failed row changes nothing, stores no inbound row and changes no binding [evidence: test:tests/test_sync.py::test_bridge_notice_ignored_otherwise]
- ac6: README names the reason and MEMORY.md records the writer ruling [evidence: command:grep -qF '`bridge: ' README.md && grep -q 'bridge notice' MEMORY.md]
- ac7: the targeted tests and lint pass (DB tests in CI) [evidence: command:uv run --frozen pytest tests/test_discovery.py tests/test_sync.py tests/test_readme_api.py && mise run lint]

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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
