---
title: reconciler leader pod hold
status: todo
repo: agents-orchestrator
value: "the leader's pod is removed only after leadership has moved"
files: [src/agents_orchestrator/reconciler/loop.py, tests/test_reconciler.py, README.md]
verify: "uv run --frozen pytest -q tests/test_reconciler.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [scale-down-staying-peer]
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

# reconciler leader pod hold

## Requirement

Goal G2, verbatim: "a scale-down whose new replica count would remove the leader's pod first hands leadership to a ready agent that stays, then shrinks".

Design D8, verbatim: during a scale-down drain the current leader, when it is at or above the target, counts as busy in `_draining`, so `_drain_replicas` keeps the StatefulSet at least one above the leader's ordinal until the leader row names a staying agent. The existing `ORCH_SCALE_DRAIN_SECONDS` (900) deadline still applies the target regardless; the leader's pod then goes and the lost-leader step picks a successor. `status.drain.waiting` lists the leader's ordinal while it is held. A staying peer can become unready between the api's check and the pass's move (a pod restart); then the pass finds no eligible agent and the leader stays leading, busy or idle, and its pod is held until a peer is ready again (the pass retries and moves it) or until the drain deadline, whichever is first. At the deadline the pod goes, the leader becomes gone, and the lost-leader step picks the first staying agent that is ready; until one is, untargeted messages hold (the existing gone-leader rule). Targeted messages keep flowing throughout.

Scope:
- `src/agents_orchestrator/reconciler/loop.py` `_draining`: an agent at or above `replicas` that is the session's current leader (`session_leaders.agent_id`, read only) counts as busy. `_drain_replicas` is otherwise unchanged (never below the target, never above the replicas already applied, the deadline from `status.drain.since`).
- `tests/test_reconciler.py`: new tests (names in the acceptance conditions), including the busy-leader race: a busy leaving leader whose only staying peer became unready after the scale was accepted keeps its pod (busy and leading) until the deadline, and then the target applies.
- README: the scale-down drain paragraph (around README line 301) says the leader's pod is kept until leadership has moved, within the drain deadline; the sentence "Draining agents are never `ready`, so the dispatcher, leader selection and session bootstrap never pick them" also says leader selection skips agents at or above `spec.replicas` from the moment the count is written.

Notes: the reconciler only reads `session_leaders` (the dispatcher is its writer). Keep the hash invariant: only `StatefulSet.spec.replicas` differs (`tests/test_render.py::test_runtime_fields_change_only_statefulset_replicas`). The existing `test_scale_down_*` and `test_drain_status_reported` tests stay accurate.

## Acceptance conditions

- AC1: an idle leader at or above the target keeps its pod (StatefulSet replicas at least leader ordinal + 1) and its ordinal is in `status.drain.waiting` until the leader row names a staying agent, then the target applies [evidence: test:tests/test_reconciler.py::test_scale_down_holds_leader_pod_until_handover]
- AC2: after `scale_drain_seconds` from `status.drain.since` the target applies even while the leaving agent still leads [evidence: test:tests/test_reconciler.py::test_scale_down_leader_hold_bounded_by_deadline]
- AC3: a busy leaving leader whose only staying peer became unready after the scale was accepted keeps its pod until `scale_drain_seconds` from `status.drain.since`, then the target applies regardless [evidence: test:tests/test_reconciler.py::test_scale_down_busy_leader_peer_unready_bounded]
- AC4: the existing drain tests still pass [evidence: command:uv run --frozen pytest -q tests/test_reconciler.py tests/test_render.py]
- AC5: README documents the hold and stays in sync [evidence: command:uv run --frozen pytest -q tests/test_readme_api.py]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/reconciler/loop.py`
- `tests/test_reconciler.py`
- `README.md`

## Interfaces

See the Requirement and the acceptance conditions above.

## Expected outcome

See the Requirement and the acceptance conditions above.

## Steps

- Red: add the three new tests to `tests/test_reconciler.py`; run `uv run --frozen pytest -q tests/test_reconciler.py`: they fail (the leader's pod is removed at once).
- Green: count the leaving leader as busy in `_draining`, update README; run the task's verify command: passes.

## Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 amended: interrogate 2026-10-26 (fable, opus, sonnet): finding 5 (busy leader, peer unready race)
