---
title: Idle since in snapshot
status: escalated
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
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/claude-code-wrapper-orchestr-idle-since-in-snapshot/claude-code-wrapper
branch: claude-code-wrapper-orchestr-idle-since-in-snapshot
verified_head: 9961bc9094a8a0bd2a7a92b12a9d6b83eb14661f
run: claude-code-wrapper-orchestr
provides: [wrapper-idle-since]
acs_for_audit: []
process_gaps: ["No red run: tests were written after the implementation, as the implementer disclosed", Branch not rebased onto origin/main before the PR]
---

# Idle since in snapshot

## Requirement

The session snapshot (manager.py snapshot dict, manager.py:1429-1453) gains `idle_since`: the ISO timestamp of the latest transition into the public state `ready`, and null in any other state. `idle_since` is set by every transition into ready: creating -> ready at boot (session.py:496-497), busy -> ready on turn completion (session.py:989 `_set_state(next_state)` and 1037), and the post-restart boot that reaches ready again. A turn start (busy) clears it. Stopped sessions loaded from disk report null.

Every `session_state` event data gains `since` (ISO timestamp of that transition), including the events emitted by `Router.on_state` (router.py:1355) and the restart event in `Router.on_restart` (router.py:1380-1390, whose `state` comes from `session.snapshot()` and may be creating or ready; its `since` is the time of that emit and equals the preceding transition). Both are additive; existing fields and events are unchanged.

Relation to `ready_at`: `ready_at` (session.py:381, set at session.py:496) is the time the latest boot of claude became ready and is not touched by turns; `idle_since` equals it right after boot and then moves forward on each turn completion. They are not merged; `ready_at` stays as is.

README.md documents `idle_since` in the snapshot table and `since` in the session_state event row (tests/test_readme_api.py enforces documented routes and events). The orchestrator uses idle_since to route to the agent free the longest.

## Acceptance conditions

- AC1: a freshly ready session snapshot has a non-null ISO idle_since equal to the creating -> ready transition [evidence: test:tests/test_idle_since.py::test_ready_session_has_idle_since]
- AC2: idle_since is null while busy and reset to the completion transition time on turn completion [evidence: test:tests/test_idle_since.py::test_idle_since_cleared_when_busy_and_reset_on_completion]
- AC3: every session_state event carries since, including the creating -> ready event and the on_restart event [evidence: test:tests/test_idle_since.py::test_session_state_event_carries_since]
- AC4: after a claude restart that reaches ready, idle_since equals the latest transition into ready and ready_at is the boot time [evidence: test:tests/test_idle_since.py::test_idle_since_after_restart_and_ready_at_relation]
- AC5: README documents idle_since and since [evidence: test:tests/test_readme_api.py::test_every_event_type_documented]

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

Reuse the existing now_iso helper (timeutil.py). Session.on_state is notified only when the public state changes (session.py:412-419), so `since` is stamped there, in one place, from the same clock reading that updates idle_since. Never run the full suite (11 min). The branch must be rebased on origin/main before the PR.
