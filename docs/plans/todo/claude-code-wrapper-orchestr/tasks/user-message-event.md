---
title: User message event
status: todo
repo: claude-code-wrapper
value: Chat UI shows every prompt including peer and restart prompts
files: [src/claude_code_wrapper/router.py, src/claude_code_wrapper/events.py, README.md, tests/test_user_message_event.py]
verify: "uv run pytest tests/test_user_message_event.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [idle-since-in-snapshot]
owns: [wrapper-user-message-event]
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# User message event

## Requirement

A new SSE/history event type `user_message` with data `{turn_id, origin, text, files}`, emitted by the router every time a prompt is pasted into the session. `origin` reuses the Origin values of turns.py:27 (`client`, `initial`, `agent`, `peer`) plus `restart` (the continue or resume prompt pasted after a claude restart) and `command` (a slash command line). `turn_id` is null for `command`. `turn_started.data.text` stays unchanged. The type is added to events.py EVENT_TYPES and documented in README.md (event table and origin values; tests/test_readme_api.py enforces it). Additive only. The event rides the normal ring and rotation like every other event (my call).

Emitting paths (exhaustive; line numbers at checkout c53f7ed):

- Fresh submit: `Session.submit` (session.py:762) sets state busy (session.py:796, so `session_state busy` is already logged) and pastes (session.py:801); `Router.submit_turn` then emits `user_message` immediately before `turn_started` (router.py:809), origin = the record's origin (`client`, `initial`, `agent` or `peer`). This also covers the peer path, because `peer_inbox.py:297` goes through `router.submit_turn(..., origin="peer")`; `text` is the framed peer message, `files` empty.
- Continue paths, all through `Session.continue_turn` (session.py:680, paste at session.py:700): the post-command continuation (router.py:1039, emitted next to `turn_resumed` cause command) and the post-restart continuation (`Session._continue_held`, session.py:678, with `on_turn_resumed` at router.py:1403/1410). The Stop-hook block path (`turn_continued`, router.py:676) pastes nothing, the reason goes back as the hook answer, so it emits no `user_message`. A command continuation uses the turn's own origin and `text` is the continue prompt. On a restart continue, `text` is the continue prompt (`sessions.restart_continue_prompt`) and origin is `restart`.
- Slash commands: `Session.send_command` (session.py:1056, called from router.py:1218) emits `user_message` with origin `command`, `turn_id` null and `text` the rendered command line.

Order within the log: `session_state busy` < `user_message` < `turn_started` (fresh submit) and `user_message` < `turn_completed` for the same turn_id.
Existing contract pinned, no new feature: turn events keep `origin`, `final_text` and `usage` (the `record` is a TurnRecord dump, `_emit_turn_event`, router.py:731-732; fields turns.py:90, 93, 95), and the snapshot keeps `current_turn_id`, `model` and `workdir` (manager.py:1436, 1438, 1445). AC9 pins them with a test.

## Acceptance conditions

- AC1: a client-origin turn emits user_message with text, files and origin client after session_state busy and before turn_started [evidence: test:tests/test_user_message_event.py::test_user_turn_emits_user_message]
- AC2: a peer-origin turn (via peer_inbox.py:297) emits user_message with origin peer [evidence: test:tests/test_user_message_event.py::test_peer_origin]
- AC3: a restart continue emits user_message with origin restart whose text is the restart continue prompt [evidence: test:tests/test_user_message_event.py::test_restart_continue_origin_and_text]
- AC4: a command-continuation paste (router.py:1039 path) emits user_message with the continue prompt and the turn's origin [evidence: test:tests/test_user_message_event.py::test_command_continuation_paste]
- AC5: a slash command emits user_message with origin command and turn_id null [evidence: test:tests/test_user_message_event.py::test_slash_command_origin_command]
- AC6: user_message is ordered after session_state busy and before turn_completed of the same turn [evidence: test:tests/test_user_message_event.py::test_event_order]
- AC7: turn_started text is unchanged [evidence: test:tests/test_user_message_event.py::test_turn_started_text_unchanged]
- AC8: user_message is in EVENT_TYPES and documented in README.md [evidence: test:tests/test_readme_api.py::test_every_event_type_documented]
- AC9: turn_completed.data.record carries origin, final_text and usage, and the session snapshot carries current_turn_id, model and workdir [evidence: test:tests/test_user_message_event.py::test_turn_and_snapshot_fields_pinned]

## Files

- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/events.py`
- `README.md`
- `tests/test_user_message_event.py`

## Interfaces

events.py EVENT_TYPES gains user_message; data {turn_id, origin, text, files}. Contract wrapper-user-message-event.

## Expected outcome

After a prompt is pasted the event log holds user_message with turn_id, origin, text, files; turn_started is unchanged.

## Steps

- Write tests/test_user_message_event.py with the fake claude; run it and see it fail (unknown event type).
- Add user_message to events.py EVENT_TYPES; emit in router.py at paste time (router.py:810 is where turn_started is emitted); update README.md.
- Run `uv run pytest tests/test_user_message_event.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`.

## Notes

Emit when the prompt is actually pasted, not on accept. Shares events.py/router.py with other tasks: this is why the chain is ordered. The Stop-hook block (turn_continued, router.py:676) is deliberately not a paste. The `user_message` for slash commands is emitted in the router where `send_command` is called (router.py:1216-1218), after `command_started`. Origin is the turns.py:27 Literal extended by `restart` and `command`; do not widen `TurnRecord.origin`, only the event data.
