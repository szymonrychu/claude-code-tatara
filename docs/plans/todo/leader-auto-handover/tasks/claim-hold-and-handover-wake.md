---
title: claim hold and handover wake
status: todo
repo: agents-orchestrator
value: "a compacted or leaving leader never takes another untargeted message that a staying agent could take, and moves without waiting for the poll"
files: [src/agents_orchestrator/db/queue.py, tests/test_queue_leader_routing.py, tests/test_dispatcher_auto_handover.py, README.md]
verify: "uv run --frozen pytest -q tests/test_queue_leader_routing.py tests/test_dispatcher_auto_handover.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [compaction-status-projection, leadership-auto-handover, scale-down-staying-peer]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# claim hold and handover wake

## Requirement

Goal G1: "the orchestrator then moves leadership to another ready agent of the cluster at the leader's turn boundary". Goal G3: "with no eligible agent the leader keeps leading and the move is retried." Interrogate finding 1 (2026-10-26): the pass runs once per drain and `_drain_messages` then loops `claim_and_pick`; `_claim_in_session` routes untargeted messages to the leader without checking `compaction_at > since` (`dispatcher/loop.py:129-131,155-171`, `db/queue.py:245-279`). The claim path must never route an untargeted message to a leader whose compaction is pending. Interrogate finding 2: the compaction projection and `set_replicas` must wake the dispatcher.

Design D16, verbatim: `_claim_in_session` (`db/queue.py`) treats the leader like a gone leader (untargeted messages hold, targeted ones flow) while its handover is pending and possible: its `compaction_at` is later than `since` or it is leaving (not gone, `ordinal >= spec.replicas`), and an eligible staying agent exists by the same predicate the pass picks with (D7). With no eligible agent the leader keeps receiving untargeted messages (G3, "the leader keeps leading").

Design D15, verbatim: when the ingester projects a compaction (D3) it also sends `NOTIFY leadership_requested {session_id}`, and `set_replicas` sends it when it accepts a count at or below the leader's ordinal (D5). The dispatcher already listens on that channel (`dispatcher/loop.py:37`), so an idle compacted leader or a leaving leader moves on the wake, not on the next `ORCH_DISPATCH_POLL_SECONDS` poll. A busy compacted leader is moved on the `agent_free` wake at its turn end.

Scope:
- `src/agents_orchestrator/db/queue.py` `_claim_in_session`: the hold above, reading `session_leaders`, `agent_status.compaction_at`, `agents` and `sessions.spec` only; the eligible-agent predicate is the one `db/leadership.py` picks with (import or shared constant; mind that `db/leadership.py` imports `db/queue.py`, so the shared SQL lives where no import cycle appears).
- `tests/test_queue_leader_routing.py`: new tests (names in the acceptance conditions).
- `tests/test_dispatcher_auto_handover.py` (new): a running `Dispatcher` with `dispatch_poll_seconds` far above the test timeout (for example 60), so only a NOTIFY can wake it: (a) an idle hive leader gets `compaction_at` later than `since` through `db/status`'s setter plus `NOTIFY leadership_requested {session_id}` as the ingester sends it, and the leader moves with reason `compaction` within a few seconds; (b) `set_replicas` below the leader with a staying ready peer moves the leader with reason `scale_down` within a few seconds; (c) the race of finding 1: a busy compacted leader with an untargeted message queued turns idle (`agent_status` idle plus `agent_free` NOTIFY, as the ingester does) and the queued message is dispatched to the new leader, never to the compacted one (use the fake wrapper the other dispatcher tests use).
- README `### Routing`: the hold for a leader whose handover is pending; `### Leadership`: `leadership_requested` is sent by the api on a queued request, by the ingester on a compaction and by `set_replicas` on a scale-down below the leader.

Notes: the existing routing tests (`test_gone_leader_waits`, `test_new_leader_after_handover`) stay accurate. Find the dispatcher test harness in `tests/test_hive_push.py` (`test_dispatcher_run_pushes_on_leader_changed`) and the dispatcher send tests before writing the new file.

## Acceptance conditions

- AC1: an untargeted message is never claimed for an idle leader whose `compaction_at` is later than its `since` while a staying ready agent exists; targeted messages to other agents still dispatch [evidence: test:tests/test_queue_leader_routing.py::test_compacted_leader_holds_untargeted]
- AC2: a leaving leader (not gone, `ordinal >= spec.replicas`) with a staying ready agent holds untargeted messages the same way [evidence: test:tests/test_queue_leader_routing.py::test_leaving_leader_holds_untargeted]
- AC3: with no eligible staying agent, a compacted leader keeps receiving untargeted messages [evidence: test:tests/test_queue_leader_routing.py::test_compacted_leader_without_peer_keeps_leading]
- AC4: an idle leader that compacts moves with reason `compaction` on the `leadership_requested` wake, without waiting for the poll [evidence: test:tests/test_dispatcher_auto_handover.py::test_idle_compaction_moves_without_poll]
- AC5: a scale-down below the leader moves it with reason `scale_down` on the wake from `set_replicas`, without waiting for the poll [evidence: test:tests/test_dispatcher_auto_handover.py::test_scale_down_moves_without_poll]
- AC6: a message queued while a compacted leader is busy is dispatched to the new leader after the leader's turn ends, never to the compacted leader [evidence: test:tests/test_dispatcher_auto_handover.py::test_compacted_leader_never_takes_next_message]
- AC7: the existing routing tests and README stay green [evidence: command:uv run --frozen pytest -q tests/test_queue_leader_routing.py tests/test_readme_api.py]
- AC8: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/db/queue.py`
- `tests/test_queue_leader_routing.py`
- `tests/test_dispatcher_auto_handover.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
