---
title: history scan off event loop
status: done
repo: claude-code-wrapper
value: backward history paging cannot stall the service
files: [src/claude_code_wrapper/events.py, src/claude_code_wrapper/api/events.py, tests/test_history_backward.py]
verify: "uv run pytest tests/test_history_backward.py tests/test_event_log.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [idle-since-in-snapshot, user-message-event, history-before-seq-and-types, peer-mesh-view-route, statusline-relay, context-in-snapshot-and-sse, on-start-instance-hook]
model: ""
review: ""
verified_head: d41dd76a6710d1ffe7121ad1817075acdd6ec3ce
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 4
actual_tokens: 702621
actual_roles: "impl 2, review 2"
actual_role_tokens: "impl 385918, review 316703"
---

# history scan off event loop

## Requirement

Security finding (medium): EventLog.page_before (events.py:259-278) and page with types (:247-254) parse the whole JSONL file synchronously on the event loop when the ring misses, so repeated authenticated calls can stall the service. Run the file scan off the event loop (asyncio.to_thread from the API handler, or an async variant) and bound the bytes scanned per request (read the file backwards in chunks, stopping once limit matches are collected), keeping results identical.

## Acceptance conditions

- AC1: a history request whose scan reads the file does not block the event loop (a concurrent request completes while the scan runs) [evidence: test:tests/test_history_backward.py::test_file_scan_runs_off_event_loop]
- AC2: page_before stops reading once limit matches are collected, results unchanged [evidence: test:tests/test_history_backward.py::test_page_before_bounded_scan]

## Files

- `src/claude_code_wrapper/events.py`
- `src/claude_code_wrapper/api/events.py`
- `tests/test_history_backward.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The requirement above holds, pinned by the acceptance tests.

What is true and observable when the task is done.

## Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
