---
title: vocabulary pins
status: escalated
repo: claude-code-wrapper
value: the wrapper full suite is green with the new hook and event vocabulary
files: [tests/test_command_vocabulary.py, tests/test_event_log.py, src/claude_code_wrapper/hooks.py, src/claude_code_wrapper/events.py]
verify: "uv run pytest tests/test_command_vocabulary.py tests/test_event_log.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [history-scan-off-event-loop, statusline-absolute-command, statusline-input-validation, idle-since-in-snapshot, user-message-event, history-before-seq-and-types, peer-mesh-view-route, statusline-relay, context-in-snapshot-and-sse, on-start-instance-hook]
owns: []
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/claude-code-wrapper-orchestr-vocabulary-pins/claude-code-wrapper
branch: "HEAD (worktree claude-code-wrapper-orchestr-vocabulary-pins), commit 4d1989e"
verified_head: 4d1989edeb1f30843536f0ab583b5d2d5484c445
run: claude-code-wrapper-orchestr
provides: []
acs_for_audit: []
process_gaps: ["No recorded red run for the 20 to 21 pin change. The pre-change failure is in full-suite.log, but tests.red is empty."]
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

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
