---
title: leader routing
status: in-progress
repo: agent-orchestrator
value: the user talks to the leader by default while explicit targets still work
files: [src/agent_orchestrator/db/queue.py, tests/test_queue_leader_routing.py, README.md]
verify: "uv run pytest tests/test_queue_leader_routing.py tests/test_dispatch_queue.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [dispatcher-leadership-pass]
owns: []
uses: [orch-leadership-pass]
model: opus
estimate: 5
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

# leader routing

## Requirement

Leader-only routing (Q1). In `_claim_in_cluster` (`db/queue.py:245-283`): when the cluster has a `cluster_leaders` row, an untargeted queued message behaves as if targeted to the leader:

- it is dispatched only to the leader, through the same `_PICK` with the leader as target;
- while the leader is busy the untargeted head holds the cluster's untargeted FIFO (later untargeted messages wait), and later explicitly targeted messages to other free agents still dispatch;
- an explicit `target_agent_id` always wins;
- a gone leader does not fail untargeted messages with `target_gone`: they wait for the leadership pass fallback;
- with no leader row (alone clusters, or a hive before its first pass) the pick stays today's free-the-longest.

`_PICK` is unchanged. Peer-delivered turns never pass the dispatcher (documented). README `### Routing` states the rule.

## Acceptance conditions

- AC1: an untargeted message goes to the leader even when another agent has been free longer [evidence: test:tests/test_queue_leader_routing.py::test_untargeted_goes_to_leader]
- AC2: a busy leader holds later untargeted messages while a targeted message to a free member dispatches [evidence: test:tests/test_queue_leader_routing.py::test_busy_leader_holds_untargeted_only]
- AC3: an explicit target wins over the leader [evidence: test:tests/test_queue_leader_routing.py::test_explicit_target_wins]
- AC4: a gone leader leaves untargeted messages queued, not failed [evidence: test:tests/test_queue_leader_routing.py::test_gone_leader_waits]
- AC5: after a handover the next untargeted message goes to the new leader [evidence: test:tests/test_queue_leader_routing.py::test_new_leader_after_handover]
- AC6: clusters without a leader row keep the existing behaviour [evidence: command:uv run pytest tests/test_dispatch_queue.py -q]
- AC7: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/db/queue.py`
- `tests/test_queue_leader_routing.py`
- `README.md`

## Interfaces

- Changes `db/queue.py` `_claim_in_cluster`; `_PICK` unchanged; reads `cluster_leaders`.

## Expected outcome

Untargeted messages of a hive reach only the leader.

## Steps

- Red: write `tests/test_queue_leader_routing.py` for AC1-AC5; run `uv run pytest tests/test_queue_leader_routing.py -q`: fails.
- Green: leader-as-target in `_claim_in_cluster`; run the verify command: passes, including `tests/test_dispatch_queue.py`.

## Notes

- `_claim_in_cluster` at `db/queue.py:245-283`: keep the FIFO hold for untargeted heads and the skip for busy targeted messages.
