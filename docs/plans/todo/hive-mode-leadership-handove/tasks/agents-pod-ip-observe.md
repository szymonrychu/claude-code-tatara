---
title: agents pod ip observe
status: todo
repo: agent-orchestrator
value: the orchestrator knows which pod is calling it
files: [src/agent_orchestrator/reconciler/loop.py, src/agent_orchestrator/db/agents.py, tests/test_reconciler.py]
verify: "uv run pytest tests/test_reconciler.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [migration-0003-hive]
owns: []
uses: [orch-hive-tables]
model: ""
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
