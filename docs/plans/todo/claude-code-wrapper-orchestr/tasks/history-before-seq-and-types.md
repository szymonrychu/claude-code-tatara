---
title: History before_seq and types
status: todo
repo: claude-code-wrapper
value: "Chat UI can load newest and scroll back, headless clients can filter"
files: [src/claude_code_wrapper/events.py, src/claude_code_wrapper/api/events.py, README.md, tests/test_history_backward.py]
verify: "uv run pytest tests/test_history_backward.py tests/test_readme_api.py -q && mise run lint"
depends_on: [user-message-event]
owns: [wrapper-history-backward]
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

# History before_seq and types

## Requirement

`GET /v1/sessions/{id}/history` accepts `before_seq=N`, `limit` (max 1000, as today) and `types=a,b` (comma list of event types; unknown type returns 400 invalid_request). With before_seq it returns the events with seq < N, newest page first selected but returned in ascending seq order, plus `prev_seq` (the seq to pass as before_seq for the next older page) and `has_more_before`. `types` filters before paging, also for the forward (after_seq) mode. Combining before_seq with after_seq returns 400 invalid_request. Works for stopped (readonly) sessions and reads the rotated events.jsonl correctly. Implementation lives in EventLog (events.py, a new page_before method beside `page`) and api/events.py. README.md documents the parameters and response fields. Additive: the existing response shape is unchanged without before_seq.

## Acceptance conditions

- AC1: before_seq returns the newest older page in ascending order with prev_seq and has_more_before [evidence: test:tests/test_history_backward.py::test_before_seq_pages_backwards]
- AC2: types filters in both directions [evidence: test:tests/test_history_backward.py::test_types_filter]
- AC3: before_seq with after_seq is 400 and an unknown type is 400 [evidence: test:tests/test_history_backward.py::test_invalid_combinations_are_400]
- AC4: works on a stopped session and after log rotation [evidence: test:tests/test_history_backward.py::test_stopped_session_and_rotation]
- AC5: README documents before_seq, types, prev_seq, has_more_before [evidence: test:tests/test_readme_api.py::test_every_public_route_documented]

## Files

- `src/claude_code_wrapper/events.py`
- `src/claude_code_wrapper/api/events.py`
- `README.md`
- `tests/test_history_backward.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
