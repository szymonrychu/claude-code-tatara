---
title: agents pod ip observe
status: done
repo: agent-orchestrator
value: the orchestrator knows which pod is calling it
files: [src/agent_orchestrator/reconciler/loop.py, src/agent_orchestrator/db/agents.py, tests/test_reconciler.py]
verify: "uv run pytest tests/test_reconciler.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [migration-0003-hive]
model: ""
review: ""
verified_head: 155cfb2ed7feb3dfa110f2e980ffb3b9f6a3a84f
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 7
actual_tokens: 421405
actual_roles: "impl 2, review 2"
actual_role_tokens: "impl 286061, review 135344"
---

# agents pod ip observe

## Requirement

Foundation part F4 identity source (D1). The reconciler's `_observe` (`reconciler/loop.py:273-309`) stores each pod's `status.podIP` in `agents.pod_ip` through `db/agents.upsert_agent(..., pod_ip=...)`: null while the pod has no IP, updated when a restarted pod gets a new IP. `mark_gone` sets `pod_ip` to null so a reused IP never authenticates a gone agent. The fake kube pods in tests carry `status.podIP`.

## Acceptance conditions

- AC1: an observed pod's IP lands in agents.pod_ip [evidence: test:tests/test_reconciler.py::test_observe_stores_pod_ip]
- AC2: a pod that comes back with a new IP updates the column [evidence: test:tests/test_reconciler.py::test_observe_updates_pod_ip]
- AC3: a gone agent has a null pod_ip [evidence: test:tests/test_reconciler.py::test_gone_agent_clears_pod_ip]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/reconciler/loop.py`
- `src/agent_orchestrator/db/agents.py`
- `tests/test_reconciler.py`

## Interfaces

- Writes `agents.pod_ip` (part `orch-hive-tables`); `db/agents.upsert_agent(..., pod_ip)`, `mark_gone` clears it.

## Expected outcome

Every live agent row carries its pod IP.

## Steps

- Red: add the three tests to `tests/test_reconciler.py`; run `uv run pytest tests/test_reconciler.py -q`: fails.
- Green: pass `status.podIP` through `_observe`; run the verify command: passes.

## Notes

- `_observe` at `reconciler/loop.py:273-309`; `upsert_agent` and `mark_gone` at `db/agents.py:71-102`. The fake kube lives in `tests/fakes/fake_kube.py`.
