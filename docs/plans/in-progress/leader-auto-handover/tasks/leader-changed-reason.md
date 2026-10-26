---
title: leader changed reason
status: in-progress
repo: agents-orchestrator
value: API and stream clients see why leadership moved
files: [src/agents_orchestrator/db/leadership.py, src/agents_orchestrator/api/streams.py, tests/test_leader_views.py, tests/test_leadership_pass.py, README.md]
verify: "uv run --frozen pytest -q tests/test_leader_views.py tests/test_leadership_pass.py tests/test_hive_push.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [leadership-auto-handover, reconciler-leader-pod-hold]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 6
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# leader changed reason

## Requirement

Goal G5, verbatim: "the UI, API and stream show automatic handovers with their reason (compaction, scale-down); documented API and API-only e2e test."

Design D10, verbatim: the two new `session_leaders.reason` values are `compaction` and `scale_down` (bare, like `lease_expired`; `handover: <reason>` stays for agent-requested handovers). `_set_leader`'s `NOTIFY leader_changed` payload and the `/api/v1/stream` `leader_changed` frame gain `reason` (additive). The session view's `leader_reason` already carries it. README documents every reason the code writes: `initial`, `user`, `handover: <reason>`, `leader_lost`, `lease_expired`, `scale_down`, `compaction` (discovery fix-as-ac: README lists `start` and omits values).

Scope:
- `src/agents_orchestrator/db/leadership.py` `_set_leader`: the NOTIFY payload is `{session_id, agent_id, epoch, reason}`.
- `src/agents_orchestrator/api/streams.py`: the `leader_changed` frame data is `{session_id, agent_id, epoch, reason}`.
- README: the Events table row of `leader_changed` (`{"session_id", "agent_id", "epoch", "reason"}`), `Every change sends NOTIFY leader_changed {...}` in Leadership, the session view's `leader_since` and `leader_reason` text (the full reason list above), and the `session_leaders` row of the tables list (the full reason list).
- Tests: a new test in `tests/test_leader_views.py` that a pass-driven change (for example reason `scale_down`) reaches the `/api/v1/stream` frame with its reason, and that the session view's `leader_reason` reads it.
- Tests no longer accurate, to update (they pin the payload without `reason`):
  - `tests/test_leader_views.py::test_leader_changed_frame`: its hand-sent NOTIFY and the expected frame gain `reason`.
  - `tests/test_leadership_pass.py`: the exact-payload assertions in `test_concurrent_passes_single_change` area (around lines 420-424) and the lease test around line 534 gain `reason`.

Notes: the hive push wakes on `leader_changed` regardless of payload (`tests/test_hive_push.py::test_dispatcher_run_pushes_on_leader_changed` must stay green). openapi.json is unchanged (the stream frame is documented in README only); `tests/test_readme_api.py` checks every frame is documented.

## Acceptance conditions

- AC1: the `leader_changed` NOTIFY payload carries the change reason [evidence: command:uv run --frozen pytest -q tests/test_leadership_pass.py]
- AC2: the `/api/v1/stream` `leader_changed` frame carries `reason` [evidence: test:tests/test_leader_views.py::test_leader_changed_frame]
- AC3: a `scale_down` change made by the pass reaches the stream frame and the session view's `leader_reason` [evidence: test:tests/test_leader_views.py::test_auto_handover_reason_in_frame_and_view]
- AC4: the hive push still wakes on leader changes [evidence: test:tests/test_hive_push.py::test_dispatcher_run_pushes_on_leader_changed]
- AC5: README lists every reason and the frame's fields and stays in sync [evidence: command:uv run --frozen pytest -q tests/test_readme_api.py && grep -q "lease_expired., .scale_down., .compaction" README.md]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/db/leadership.py`
- `src/agents_orchestrator/api/streams.py`
- `tests/test_leader_views.py`
- `tests/test_leadership_pass.py`
- `README.md`

## Interfaces

See the Requirement and the acceptance conditions above.

## Expected outcome

See the Requirement and the acceptance conditions above.

## Steps

- Red: add `test_auto_handover_reason_in_frame_and_view` and update the named payload assertions (`test_leader_changed_frame`, the exact payloads in `tests/test_leadership_pass.py`); run `uv run --frozen pytest -q tests/test_leader_views.py tests/test_leadership_pass.py`: they fail (no `reason`).
- Green: add `reason` to the `_set_leader` NOTIFY and the stream frame, update README; run the task's verify command: passes.

## Notes

See the Requirement and the acceptance conditions above.
