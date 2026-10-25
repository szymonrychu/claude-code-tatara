---
title: scale down drain
status: done
repo: agent-orchestrator
value: shrinking a hive never cuts an agent off mid-turn
files: [src/agent_orchestrator/reconciler/loop.py, src/agent_orchestrator/settings.py, README.md, MEMORY.md, tests/test_reconciler.py]
verify: "uv run --frozen pytest -q tests/test_reconciler.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: opus
review: ""
verified_head: e91c1bba8febbc434c5c80f8f25c214068d62c8c
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 7
actual_tokens: 1850279
actual_roles: "impl 5, review 2"
actual_role_tokens: "impl 1687464, review 162815"
---

# scale down drain

## Requirement

Drain on scale-down so a busy agent finishes its turn before its pod goes (design D3; user S1, Q4; foundation D3, D4). In `src/agent_orchestrator/reconciler/loop.py` `_converge`: agents with `ordinal >= spec.replicas` that are not gone are draining. An agent is busy when its `agent_status.state` is `busy` or a `messages` row with its `agent_id` is `dispatching` or `verifying`. The StatefulSet is applied with replicas `max(spec.replicas, 1 + highest busy draining ordinal)`, so idle agents above the highest busy one go at once (StatefulSet removes from the top) and the rest go as they become idle. The drain deadline is the new setting `scale_drain_seconds` (`ORCH_SCALE_DRAIN_SECONDS`, default 900, > 0) counted from the first tick that saw the drain; after it the StatefulSet gets `spec.replicas` regardless and an interrupted turn takes the existing verify path. Render with `cluster.model_copy` overriding only `spec.replicas`, so only `StatefulSet.spec.replicas` differs from the target render. `clusters.status` gains `drain: {target, since, waiting: [ordinals]}` while draining and drops it when done; `status.replicas` and phase math keep using the target `spec.replicas`; the message adds `draining <n> agents`. Draining agents stay `ready = false` (the existing `_observe` rule), so the dispatcher, leader selection and session bootstrap never pick them. Raising replicas during a drain ends it with no pod restart. README: the setting in `## Configuration` and a drain paragraph in `### Reconcile loop`; MEMORY.md dated entry with the why (a removed pod mid-turn loses the turn; the bound keeps a stuck turn from pinning capacity).

## Acceptance conditions

- AC1: a busy draining agent keeps its pod until idle, then the StatefulSet drops to the target [evidence: test:tests/test_reconciler.py::test_scale_down_keeps_busy_agent_until_idle]
- AC2: idle draining agents above the highest busy one are removed in the first tick [evidence: test:tests/test_reconciler.py::test_scale_down_removes_idle_agents_at_once]
- AC3: after ORCH_SCALE_DRAIN_SECONDS the StatefulSet gets spec.replicas even with a busy agent [evidence: test:tests/test_reconciler.py::test_scale_down_drain_deadline]
- AC4: raising replicas during a drain clears status.drain and deletes no pod [evidence: test:tests/test_reconciler.py::test_scale_up_cancels_drain]
- AC5: during a drain only StatefulSet.spec.replicas differs from the target render; ConfigMap, Secret, Service and pod template are identical [evidence: test:tests/test_reconciler.py::test_drain_changes_only_statefulset_replicas]
- AC6: status.drain carries target, since and waiting while draining and is absent afterwards [evidence: test:tests/test_reconciler.py::test_drain_status_reported]
- AC7: the existing scale-down gone marking stays green [evidence: test:tests/test_reconciler.py::test_scale_down_marks_gone]
- AC8: README documents ORCH_SCALE_DRAIN_SECONDS and the drain [evidence: command:grep -q "ORCH_SCALE_DRAIN_SECONDS" README.md]
- AC9: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/reconciler/loop.py`
- `src/agent_orchestrator/settings.py`
- `README.md`
- `MEMORY.md`
- `tests/test_reconciler.py`

## Interfaces

- Builds `clusters.status.drain {target, since, waiting}` (part `scale-drain-status`, reconciler-written) and setting `Settings.scale_drain_seconds` / `ORCH_SCALE_DRAIN_SECONDS`.
- Reads `agent_status.state` (ingester-written) and `messages.status`/`agent_id` (dispatcher-written); writes only `clusters.status` and `agents` rows as today.
- Keeps the hive hash invariant: render input differs only in `spec.replicas`.

## Expected outcome

After a scale-down an agent in the middle of a turn finishes it, then its pod goes; idle agents above it go at once; nothing waits longer than the drain bound.

## Steps

- Red: add the six tests to `tests/test_reconciler.py` using the existing fake kube and `env` fixture (set `agent_status.state` and a `dispatching` message directly); run `uv run --frozen pytest -q tests/test_reconciler.py -k "drain or scale"`: they fail.
- Green: compute the effective replicas and status.drain in `_converge`; add the setting with its validator; README and MEMORY.md; run the verify command.

## Notes

- `drain.since` lives in `status` so it survives a reconciler failover; compare with `now()` from the database or the loop clock consistently with existing status timestamps.
- `_observe` keeps using the target `spec.replicas` for readiness, so draining agents are never `ready`; do not change that rule.
- The hive dispatcher's lost-leader fallback and `hive_state` push react to the gone marking; nothing to add there.
- The unchanged-status test (`test_unchanged_status_is_not_rewritten`) must stay green: write `status.drain` only when it changes.
