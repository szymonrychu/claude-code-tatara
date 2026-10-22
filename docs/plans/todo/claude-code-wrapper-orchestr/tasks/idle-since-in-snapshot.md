---
title: Idle since in snapshot
status: todo
repo: claude-code-wrapper
value: Orchestrator can route to the agent idle the longest
files: [src/claude_code_wrapper/manager.py, src/claude_code_wrapper/router.py, README.md, tests/test_idle_since.py]
verify: "uv run pytest tests/test_idle_since.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [wrapper-idle-since]
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

manager.py snapshot dict (~1429-1453) gains idle_since; router.py session_state data gains since. Contract wrapper-idle-since.

## Expected outcome

GET /v1/sessions/{id} shows idle_since while ready and null otherwise; session_state events carry since.

## Steps

- Write tests/test_idle_since.py; run `uv run pytest tests/test_idle_since.py -q` and see it fail (no idle_since key).
- Implement in manager.py snapshot and the router session_state emit; update README.md.
- Run `uv run pytest tests/test_idle_since.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`; expect all passed.

## Notes

Reuse the existing now_iso helper (timeutil.py). Never run the full suite (11 min). The branch must be rebased on origin/main before the PR.
