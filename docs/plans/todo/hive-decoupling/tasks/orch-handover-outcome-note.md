---
title: orch handover outcome note
status: todo
repo: agents-orchestrator
value: a leader learns whether its handover request was applied or why it was rejected
files: [src/agents_orchestrator/dispatcher/hive.py, src/agents_orchestrator/dispatcher/loop.py, tests/test_hive_push.py, README.md, MEMORY.md]
verify: "uv run --frozen pytest tests/test_hive_push.py tests/test_leadership_pass.py tests/test_dispatcher_auto_handover.py && mise run lint"
depends_on: [orch-handover-due-note]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 936557
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch handover outcome note

## Requirement

README Goal G4, verbatim: "The leader briefs a chosen successor directly over ccw peer messaging, then hands over with `orchestrator_leadership_handover(to=..., epoch=...)`; the requester learns every handover request outcome (applied, or rejected with its reason) as a keyed `leadership_request` note."

Design D6, verbatim: "the push pass reads, per hive session, the `handover` requests decided (`status` applied or rejected) within the last 300 s (module constant `OUTCOME_WINDOW_SECONDS`, my call) and sends each `from_agent_id`, once per request id per dispatcher process (tracked in `HiveState`), a keyed note `leadership_request`: "handover request <id> applied: <pod> leads at epoch N" or "handover request <id> rejected: <reason>" (`not_leader`, `stale_epoch`, `target_not_ready`, `no_peers`). `_drain_leadership` sets the push wake after it ran a pass for any session (my call: no change to `leadership_pass`'s signature); the per-session 10 s throttle still applies. The DB read makes it work with any number of dispatchers (live: one dispatcher pod, chart default `components.dispatcher.replicas: 1`); a duplicate keyed note replaces itself in the wrapper inbox."

Fix-as-ac (brief), verbatim: "Plugin `leadership_handover` text claims "the outcome arrives as a hive-state note"; untrue for rejections: D6 and the text fix." (This task: the note; plugin-activity-tool: the text.)

Scope (agents-orchestrator):
- `src/agents_orchestrator/dispatcher/hive.py`: `OUTCOME_KEY = "leadership_request"`, `OUTCOME_WINDOW_SECONDS = 300`; the read of decided `kind = 'handover'` requests of the session within the window (`decided_at > now() - OUTCOME_WINDOW_SECONDS`). An applied request is rendered with the session's current leader row, "handover request <id> applied: <pod> leads at epoch N", which is true at push time even for an untargeted request (its row has no `to_agent_id`) or after a later change (design D6 my call). Notes go only to the request's `from_agent_id` when it is not gone and has a wrapper session; a per-process "sent" set of request ids in `HiveState`, pruned to the window; a failed push is retried next tick. `user` requests (no `from_agent_id`) get no note.
- `src/agents_orchestrator/dispatcher/loop.py` `_drain_leadership`: `self._push_wake.set()` after it ran a pass for at least one session, changed or not.
- `tests/test_hive_push.py`: the new tests below.
- `README.md` `### Leadership` step 2: the outcome note; the hive-state push paragraph lists it.
- `MEMORY.md`: dated entry (window constant, per-process tracking, why).

## Acceptance conditions

- ac1: an applied agent handover request gives its requester a keyed leadership_request note naming the request id, the new leader and the epoch [evidence: test:tests/test_hive_push.py::test_leadership_request_applied_note]
- ac2: a request the dispatcher rejects gives its requester a keyed leadership_request note naming the request id and the reason (target_not_ready and no_peers at least) [evidence: test:tests/test_hive_push.py::test_leadership_request_rejected_note]
- ac3: each outcome is sent once per request id; requests decided more than OUTCOME_WINDOW_SECONDS ago and user requests get no note [evidence: test:tests/test_hive_push.py::test_leadership_request_once_and_window]
- ac4: a running dispatcher pushes the outcome after a pass that rejected a request without a leader change, with no poll tick in between [evidence: test:tests/test_hive_push.py::test_dispatcher_run_pushes_after_decision]
- ac5: README documents the outcome note under Leadership step 2 [evidence: command:grep -q "leadership_request" README.md]
- ac6: MEMORY.md records the window and the tracking [evidence: command:grep -q "OUTCOME_WINDOW_SECONDS" MEMORY.md]
- ac7: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_hive_push.py tests/test_leadership_pass.py tests/test_dispatcher_auto_handover.py && mise run lint]

## Files

- `src/agents_orchestrator/dispatcher/hive.py`
- `src/agents_orchestrator/dispatcher/loop.py`
- `tests/test_hive_push.py`
- `README.md`
- `MEMORY.md`

## Interfaces

- Keyed note `leadership_request` to the request's `from_agent_id`: "handover request <id> applied: <pod> leads at epoch N" or "handover request <id> rejected: <reason>".
- `hive.OUTCOME_WINDOW_SECONDS = 300`; `Dispatcher._drain_leadership` sets `self._push_wake` after any pass.

## Expected outcome

A leader that asked for a handover always learns the outcome, within the push throttle, including rejections.

## Steps

- Red: the tests of ac1-ac4 in `tests/test_hive_push.py`; run `uv run --frozen pytest tests/test_hive_push.py`: they fail.
- Green: hive.py, loop.py, README, MEMORY; run the task's verify: passes. Quote the summary line.

## Notes

- `leadership_pass` keeps its signature; `_decide` already stamps `decided_at` and `reject_reason`.
- For ac4, follow `test_dispatcher_run_pushes_on_leader_changed`; force a dispatcher-side rejection with a `to_agent_id` target that goes unready after the API accepted the request.
- DB tests are CI-only in agent pods (no Docker); CI on the PR is the gate.
