---
title: User message event
status: todo
repo: claude-code-wrapper
value: Chat UI shows every prompt including peer and restart prompts
files: [src/claude_code_wrapper/router.py, src/claude_code_wrapper/events.py, README.md, tests/test_user_message_event.py]
verify: "uv run pytest tests/test_user_message_event.py tests/test_readme_api.py -q && mise run lint"
depends_on: [idle-since-in-snapshot]
owns: [wrapper-user-message-event]
uses: []
model: ""
estimate: 39
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

A new SSE/history event type `user_message` with data `{turn_id, origin, text, files}` where origin is one of user, peer, hook, restart, command. It is emitted by the router at the moment the prompt is actually pasted into the session (not when the turn is accepted), so reprompts, peer-origin turns and restart-continue prompts are covered, which `turn_started` misses. `turn_started.data.text` stays unchanged for compatibility. The type is added to events.py EVENT_TYPES and documented in README.md (event table and origin values); tests/test_readme_api.py enforces the documentation. Additive only.

## Acceptance conditions

- AC1: a user-origin turn emits user_message with text and files after the paste [evidence: test:tests/test_user_message_event.py::test_user_turn_emits_user_message]
- AC2: peer and restart-continue prompts emit user_message with the matching origin [evidence: test:tests/test_user_message_event.py::test_peer_and_restart_origins]
- AC3: turn_started text is unchanged [evidence: test:tests/test_user_message_event.py::test_turn_started_text_unchanged]
- AC4: user_message is in EVENT_TYPES and documented in README.md [evidence: test:tests/test_readme_api.py::test_every_event_type_documented]

## Files

- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/events.py`
- `README.md`
- `tests/test_user_message_event.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
