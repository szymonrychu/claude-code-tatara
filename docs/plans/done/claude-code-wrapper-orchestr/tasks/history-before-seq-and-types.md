---
title: History before_seq and types
status: done
repo: claude-code-wrapper
value: "Chat UI can load newest and scroll back, headless clients can filter"
files: [src/claude_code_wrapper/events.py, src/claude_code_wrapper/api/events.py, README.md, tests/test_history_backward.py]
verify: "uv run pytest tests/test_history_backward.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [user-message-event]
model: ""
review: ""
verified_head: e6c6e4be81099264628a95b4e3d26e8d443c7991
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 3
actual_tokens: 532785
actual_roles: "impl 2, review 1"
actual_role_tokens: "impl 408272, review 124513"
---

# History before_seq and types

## Requirement

`GET /v1/sessions/{id}/history` accepts `before_seq=N`, `limit` (max 1000, as today) and `types=a,b` (comma list). `types` is validated against `EVENT_TYPES` (events.py:20), which by then includes the new `user_message` and `context` types; an unknown type returns 400 invalid_request. With before_seq it returns the events with seq < N, the newest page selected but returned in ascending seq order, plus `prev_seq` (the seq to pass as before_seq for the next older page; null when `has_more_before` is false) and `has_more_before`. `types` filters before paging, also for the forward (after_seq) mode. Combining before_seq with after_seq returns 400 invalid_request. Works for stopped (readonly) sessions and reads the rotated events.jsonl correctly. Implementation lives in EventLog (events.py, a new page_before method beside `page` at events.py:236) and api/events.py (history at api/events.py:35). README.md documents the parameters and response fields. Additive: the existing response shape is unchanged without before_seq.

## Acceptance conditions

- AC1: before_seq returns the newest older page in ascending order with prev_seq and has_more_before [evidence: test:tests/test_history_backward.py::test_before_seq_pages_backwards]
- AC2: types filters in both directions [evidence: test:tests/test_history_backward.py::test_types_filter]
- AC3: before_seq with after_seq is 400 and an unknown type is 400 [evidence: test:tests/test_history_backward.py::test_invalid_combinations_are_400]
- AC4: works on a stopped session and after log rotation [evidence: test:tests/test_history_backward.py::test_stopped_session_and_rotation]
- AC5: README documents before_seq, types, prev_seq, has_more_before [evidence: test:tests/test_readme_api.py::test_every_public_route_documented]
- AC6: prev_seq is null when has_more_before is false; types accepts user_message and context and rejects an unknown type with 400 [evidence: test:tests/test_history_backward.py::test_prev_seq_null_and_types_validated_against_event_types]

## Files

- `src/claude_code_wrapper/events.py`
- `src/claude_code_wrapper/api/events.py`
- `README.md`
- `tests/test_history_backward.py`

## Interfaces

events.py EventLog.page_before(before_seq, limit, types) -> (events, has_more_before); api/events.py query params. Contract wrapper-history-backward.

## Expected outcome

Backward pages work with before_seq and types, with prev_seq and has_more_before; invalid combinations are 400.

## Steps

- Write tests/test_history_backward.py; run it and see it fail (param ignored).
- Add EventLog.page_before in events.py and wire before_seq/types in api/events.py; update README.md.
- Run `uv run pytest tests/test_history_backward.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`.

## Notes

Existing page() takes the ring fast path only when ring[0].seq <= after_seq+1; backward paging must fall back to _read_file when the ring does not cover the range. Rotation drops the oldest half of events.jsonl (events.py:212-225).

- 2026-10-23 run claude-code-wrapper-orchestr: dependency-failed on user-message-event
