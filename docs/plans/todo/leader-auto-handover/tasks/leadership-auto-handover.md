---
title: leadership auto handover
status: todo
repo: agents-orchestrator
value: "a compacted or leaving leader passes leadership to an agent that stays, without the user acting"
files: [src/agents_orchestrator/db/leadership.py, tests/test_leadership_pass.py, README.md, MEMORY.md]
verify: "uv run --frozen pytest -q tests/test_leadership_pass.py tests/test_queue_leader_routing.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [compaction-status-projection]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1836811
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# leadership auto handover

## Requirement

Goals, verbatim:
- G1: when the leader of a hive is about to compact (auto or manual), the wrapper reports it before the compaction runs and the orchestrator moves leadership to another ready agent of the cluster; a busy leader moves at its turn boundary.
- G2 (dispatcher half): a scale-down whose new replica count would remove the leader's pod first hands leadership to a ready agent that stays, then shrinks.
- G3: the new leader is chosen among ready agents that stay in the cluster (never one about to be removed); with no eligible agent the leader keeps leading and the move is retried.
- G4: always on for every hive (max_replicas > 1); a cluster of one never hands over.

User calls (decisions.md): "Who takes over: the existing longest-free pick, restricted to agents that stay. With no eligible peer, the leader stays and the move is retried." "A busy leader moves at its turn boundary." "Auto handover is ALWAYS ON for hived agents (max_replicas > 1)."

Design, verbatim:
- D4: the leadership pass gets a compaction step: when the leader's `compaction_at` is later than its term's `since`, the leader is ready and not gone, and it is at its turn boundary (the existing `at_boundary`: state `idle` and no message `dispatching` or `verifying`), leadership moves to the staying agent free the longest (D7), at `epoch + 1`, reason `compaction`. A busy leader keeps leading until its turn ends, and the first pass after the turn moves it, before the next message is claimed. With no eligible agent the leader stays, nothing is written, and the session stays a leadership candidate so every pass retries; the retry lasts for the rest of the leader's term. A new term (any leader change) starts clean. `_CANDIDATES` gains the clause "the leader's `compaction_at` > `since`".
- D6: the leadership pass gets a scale-down step, run after the queued requests and before the lost-leader step: when the leader is not gone and its ordinal is at or above `spec.replicas`, leadership moves to the staying agent free the longest (D7), at `epoch + 1`, reason `scale_down`, without waiting for the leader's turn boundary. With no staying agent the leader stays and the pass retries (the session is a candidate while the leader is leaving). A gone leader keeps the lost-leader path (reason `leader_lost`). `_CANDIDATES` gains "the leader is not gone and its ordinal >= `spec.replicas`".
- D7: an agent stays when its ordinal is below the session's `spec.replicas`. `_FREE_LONGEST` (handover without a target, `leader_lost`, `lease_expired`, `compaction`, `scale_down`), `_target_ready` (named handover and user make-leader targets: a leaving target is rejected `target_not_ready`) and the initial election all filter on it. The order stays the existing one (idle first, then `free_since` ascending, then id). No context-aware choice.
- D9: both triggers apply to every session the pass already covers (`_HIVE`). No spec field. A session running one agent never hands over.
- D13: the README `### Leadership` lists every pass step in order: 1 initial, 2 queued requests, 3 scale-down, 4 lost leader, 5 compaction, 6 lease (it says "three steps" today and omits the lease). Compaction runs before the lease so a leader that both compacted and outlived its lease reads `compaction`. MEMORY.md gets dated entries amending hive D26 (a second system handover of the current term at a turn boundary, after `leader_lease_seconds`; never a takeover, hive D21 holds) and cluster-scaling D7 ("scaling never moves leadership") and its anti-goal "leadership moving because of scaling".
- D14: no change to the hive_state handover hint, the any-mcp tool text or `/agent/v1/me`.

Scope:
- `src/agents_orchestrator/db/leadership.py`: the staying filter (`ordinal < (spec->>'replicas')::int` of the session) in `_FREE_LONGEST`, `_target_ready` and the initial election; the two `_CANDIDATES` clauses; `_leader` exposes what the steps need (the leader's ordinal, whether it is leaving, whether `agent_status.compaction_at > since`); the scale-down step and the compaction step in the order above; module docstring and step comments updated. Keep the single transaction and the claim lock.
- `tests/test_leadership_pass.py`: new tests (names in the acceptance conditions). Existing tests stay accurate; none is edited to pass.
- README `### Leadership` (steps, the two reasons, the new candidate conditions, "always on for hives") and `### Leader lease` (now step 6).
- MEMORY.md: the two dated amendment entries (2026-10-26, epic leader-auto-handover).

Notes: reuse the lease step pattern (`db/leadership.py:320-332`), `_set_leader` (epoch bump, `unready_since` cleared, `leader_changed` NOTIFY, hive push and frame for free) and `at_boundary` (`leadership.py:143-146`). The column `agent_status.compaction_at` comes from task compaction-status-projection. The NOTIFY payload change (reason) belongs to task leader-changed-reason; do not change it here. The candidate query must not select a healthy, uncompacted, staying leader every poll (`test_candidates` and `test_lease_candidates` show the pattern).

## Acceptance conditions

- AC1: a leader whose `compaction_at` is after its `since` hands over at its turn boundary to the staying agent free the longest, at epoch + 1, reason `compaction` [evidence: test:tests/test_leadership_pass.py::test_compaction_hands_over_at_boundary]
- AC2: a busy compacted leader keeps leading until its turn ends, then moves on the next pass [evidence: test:tests/test_leadership_pass.py::test_compaction_waits_for_turn_boundary]
- AC3: a compacted leader with no eligible agent stays, nothing is written, and it moves on a later pass once an agent becomes ready; a new term clears the trigger [evidence: test:tests/test_leadership_pass.py::test_compaction_without_peer_retries]
- AC4: a compaction before the current term began (`compaction_at <= since`) and a compaction of a non-leader trigger nothing [evidence: test:tests/test_leadership_pass.py::test_compaction_before_term_ignored]
- AC5: a leader whose ordinal is at or above `spec.replicas` moves at once (even when busy) to a staying agent, reason `scale_down`; with none it stays and is retried [evidence: test:tests/test_leadership_pass.py::test_scale_down_hands_over_leader]
- AC6: `_FREE_LONGEST`, named handover targets, user targets and the initial election never pick an agent with `ordinal >= spec.replicas`, even while it is still ready [evidence: test:tests/test_leadership_pass.py::test_picks_skip_leaving_agents]
- AC7: the candidate query selects sessions with a compacted leader or a leaving leader, and not a hive whose leader is healthy, uncompacted and staying; an alone session is never a candidate [evidence: test:tests/test_leadership_pass.py::test_auto_handover_candidates]
- AC8: when the leader both compacted and outlived its lease the reason is `compaction` [evidence: test:tests/test_leadership_pass.py::test_compaction_before_lease]
- AC9: the existing leadership and routing tests still pass [evidence: command:uv run --frozen pytest -q tests/test_leadership_pass.py tests/test_queue_leader_routing.py tests/test_api_leadership.py]
- AC10: README Leadership lists the six steps and MEMORY.md records the D26 and D7 amendments [evidence: command:grep -q "scale_down" README.md && grep -q "compaction" README.md && grep -q "leader-auto-handover" MEMORY.md && uv run --frozen pytest -q tests/test_readme_api.py]
- AC11: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/db/leadership.py`
- `tests/test_leadership_pass.py`
- `README.md`
- `MEMORY.md`

## Interfaces

See the Requirement and the acceptance conditions above.

## Expected outcome

See the Requirement and the acceptance conditions above.

## Steps

- Red: add the new tests of the acceptance conditions to `tests/test_leadership_pass.py`; run `uv run --frozen pytest -q tests/test_leadership_pass.py`: they fail (no staying filter, no scale-down or compaction step).
- Green: add the staying filter, the two candidate clauses, the scale-down step (before the lost-leader step) and the compaction step (before the lease step) to `db/leadership.py`; run the same command: passes.
- Docs: rewrite README `### Leadership` and `### Leader lease`, add the two MEMORY.md entries; run the task's verify command: passes.

## Notes

See the Requirement and the acceptance conditions above.
