---
title: leader lease expiry
status: in-progress
repo: agent-orchestrator
value: a hive rotates its leader after a set time without interrupting a turn
files: [src/agent_orchestrator/db/leadership.py, tests/test_leadership_pass.py, README.md, MEMORY.md]
verify: "uv run --frozen pytest -q tests/test_leadership_pass.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [spec-config-fields]
model: opus
review: full
verified_head: ""
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# leader lease expiry

## Requirement

Hand leadership over when a leader's lease runs out (design D4; approval A3; user decision and the hive "handover only, no takeovers" rule). In `src/agent_orchestrator/db/leadership.py`:

- `_CANDIDATES` adds clusters whose spec sets `leader_lease_seconds` and whose `cluster_leaders.since` is older than `now() - leader_lease_seconds` (database clock).
- `leadership_pass` gets step 4, after the lost-leader step and inside the same claim-lock transaction: when the spec sets `leader_lease_seconds`, the leader's term (`since`) is older than the lease, the leader is ready and not gone, the leader is at a turn boundary (its `agent_status.state` is `idle` and no `messages` row with its `agent_id` is `dispatching` or `verifying`), and `_free_longest(conn, cluster_id, leader)` finds another ready agent, then `_set_leader(conn, cluster_id, picked, "lease_expired")` moves leadership (epoch + 1, `since = now()`, NOTIFY `leader_changed`; the existing push loop sends `hive_state`). A busy leader keeps leadership and is handed over on the first pass after its turn ends. With no ready peer the leader stays, nothing is written, and the lease is re-checked on every pass. A leader chosen by a queued request in step 2 starts a fresh term. Nothing is interrupted, no message is re-routed, and no agent can trigger the change: it is a handover of the current leader's term, never a takeover.
- `LEADER_GRACE_SECONDS` stays the module constant 30 (hive D14).

README.md: `### Leader lease` under the hive `### Leadership` section: the field, the turn-boundary rule, reason `lease_expired`, the no-peer rule, and that clusters without the field keep today's indefinite leadership. MEMORY.md: a dated entry recording that the lease amends hive D26 ("no forced handover") for clusters that set `leader_lease_seconds`, keeps D21 (no takeovers), and why.

## Acceptance conditions

- AC1: an idle leader past its lease is replaced by the ready agent free the longest, with reason lease_expired, epoch plus one, a new since and a leader_changed notification [evidence: test:tests/test_leadership_pass.py::test_lease_expiry_hands_over_idle_leader]
- AC2: a leader that is busy, or has a dispatching or verifying message, keeps leadership past its lease and is handed over on the first pass after it is idle [evidence: test:tests/test_leadership_pass.py::test_lease_waits_for_turn_boundary]
- AC3: with no other ready agent the leader stays and the epoch does not change [evidence: test:tests/test_leadership_pass.py::test_lease_without_peer_keeps_leader]
- AC4: a cluster with an expired lease is a leadership candidate, and a cluster without leader_lease_seconds never rotates [evidence: test:tests/test_leadership_pass.py::test_lease_candidates]
- AC5: a queued handover in the same pass is judged first and its new leader starts a fresh term [evidence: test:tests/test_leadership_pass.py::test_queued_handover_before_lease]
- AC6: LEADER_GRACE_SECONDS stays the module constant 30 [evidence: command:grep -qx 'LEADER_GRACE_SECONDS = 30' src/agent_orchestrator/db/leadership.py]
- AC7: README documents the leader lease [evidence: doc-section:README.md#Leader lease]
- AC8: MEMORY.md records the amendment of hive D26 for opted-in clusters, with the date and why [evidence: judgement:MEMORY.md entry reviewed]
- AC9: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/db/leadership.py`
- `tests/test_leadership_pass.py`
- `README.md`
- `MEMORY.md`

## Interfaces

Builds part `orch-leader-lease` (reason `lease_expired` in `cluster_leaders.reason`); uses `orch-spec-config-fields` and the hive contract `orch-leadership-pass`.

## Expected outcome

In a hive with `leader_lease_seconds`, the cluster view shows a new leader with `leader_reason` `lease_expired` shortly after the lease runs out and the old leader's turn ends.

## Steps

- Red, add the five tests to `tests/test_leadership_pass.py` (backdate `cluster_leaders.since` with SQL; set `agent_status.state` and a `dispatching` message for the busy case)
- Green, implement step 4 and the candidate clause
- Run the verify command.

## Notes

The dispatcher runs `_drain_leadership` on every wake, at least every `dispatch_poll_seconds`, so no new timer is needed. Draining agents from cluster-scaling are never ready, so `_free_longest` never picks them. Concurrency-sensitive: keep every read inside the pass's transaction and lock.
