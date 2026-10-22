---
title: Idle since in snapshot
status: todo
repo: claude-code-wrapper
value: Orchestrator can route to the agent idle the longest
files: [src/claude_code_wrapper/manager.py, src/claude_code_wrapper/router.py, README.md, tests/test_idle_since.py]
verify: "uv run pytest tests/test_idle_since.py tests/test_readme_api.py -q && mise run lint"
depends_on: []
owns: [wrapper-idle-since]
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

# Idle since in snapshot

## Requirement

The session snapshot (manager.py snapshot dict, ~line 1429-1453) gains `idle_since`: the ISO timestamp at which the session last became idle (state `ready`), and null in any other state. The `session_state` event data gains `since` (ISO timestamp of the transition). Both are additive; existing fields and events are unchanged. A session that is created and becomes ready has idle_since set at that moment; a turn start clears it; a turn completion sets it again. Stopped sessions loaded from disk report null. README.md documents `idle_since` in the snapshot table and `since` in the session_state event row (tests/test_readme_api.py enforces documented routes and events). The orchestrator uses idle_since to route to the agent free the longest.

## Acceptance conditions

- AC1: a freshly ready session snapshot has a non-null ISO idle_since [evidence: test:tests/test_idle_since.py::test_ready_session_has_idle_since]
- AC2: idle_since is null while busy and reset on turn completion [evidence: test:tests/test_idle_since.py::test_idle_since_cleared_when_busy_and_reset_on_completion]
- AC3: session_state event data carries since [evidence: test:tests/test_idle_since.py::test_session_state_event_carries_since]
- AC4: README documents idle_since and since [evidence: test:tests/test_readme_api.py::test_every_event_type_documented]

## Files

- `src/claude_code_wrapper/manager.py`
- `src/claude_code_wrapper/router.py`
- `README.md`
- `tests/test_idle_since.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
