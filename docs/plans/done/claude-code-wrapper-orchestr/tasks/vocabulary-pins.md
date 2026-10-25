---
title: vocabulary pins
status: done
repo: claude-code-wrapper
value: the wrapper full suite is green with the new hook and event vocabulary
files: [tests/test_command_vocabulary.py, tests/test_event_log.py, src/claude_code_wrapper/hooks.py, src/claude_code_wrapper/events.py]
verify: "uv run pytest tests/test_command_vocabulary.py tests/test_event_log.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [history-scan-off-event-loop, statusline-absolute-command, statusline-input-validation, idle-since-in-snapshot, user-message-event, history-before-seq-and-types, peer-mesh-view-route, statusline-relay, context-in-snapshot-and-sse, on-start-instance-hook]
model: ""
review: ""
verified_head: 4d1989edeb1f30843536f0ab583b5d2d5484c445
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 3
actual_tokens: 545223
actual_roles: "impl 2, review 2"
actual_role_tokens: "impl 355351, review 189872"
---

# vocabulary pins

## Requirement

The epic full suite fails 2 exact-vocabulary pin tests (1576 passed): tests/test_command_vocabulary.py::test_hook_events_include_command_hooks and tests/test_event_log.py::test_event_types_exact. Read each assertion against the code: where the new vocabulary is intended (onStart instance hook event from on-start-instance-hook; user_message and context event types from user-message-event and context-in-snapshot-and-sse), update the pinned lists; where the code broke an invariant the pin protects (for example onStart wrongly listed as a command hook), fix the code instead. State which applied for each in the notes. Full-suite log: /private/tmp/claude-501/-Users-szymonri-Documents-claude-code-tatara/21d1a847-8d6b-4ee4-a271-ba52ec27cf3b/scratchpad/orch/run-claude-code-wrapper-orchestr/full-suite.log.

## Acceptance conditions

- AC1: the hook-event vocabulary pin passes and matches the intended vocabulary [evidence: test:tests/test_command_vocabulary.py::test_hook_events_include_command_hooks]
- AC2: the event-type vocabulary pin passes and includes user_message and context [evidence: test:tests/test_event_log.py::test_event_types_exact]

## Files

- `tests/test_command_vocabulary.py`
- `tests/test_event_log.py`
- `src/claude_code_wrapper/hooks.py`
- `src/claude_code_wrapper/events.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The wrapper full suite is green.

What is true and observable when the task is done.

## Steps

- Red already seen in the epic full suite (assert 21 == 20; event list diff at context).
- Reconcile pins or code per the requirement; run green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Ruling

- 2026-10-22 accepted: false gate-repeat: verifier hit a stale pytest assertion-rewrite .pyc (20->21 edit keeps file size, cache reused). Hand-verified on 4d1989e after deleting the .pyc: 'uv run pytest tests/test_command_vocabulary.py tests/test_event_log.py -p no:cacheprovider' -> 31 passed; ruff check and format clean. Red is in the epic full-suite log (assert 21 == 20).

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
