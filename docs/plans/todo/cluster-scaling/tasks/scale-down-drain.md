---
title: scale down drain
status: todo
repo: agent-orchestrator
value: shrinking a hive never cuts an agent off mid-turn
files: [src/agent_orchestrator/reconciler/loop.py, src/agent_orchestrator/settings.py, README.md, MEMORY.md, tests/test_reconciler.py]
verify: "uv run --frozen pytest -q tests/test_reconciler.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [scale-drain-status]
uses: []
model: opus
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
