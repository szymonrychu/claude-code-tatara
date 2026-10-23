---
title: discard quiesce before export
status: todo
repo: agent-orchestrator
value: "a discarded cluster's exported history includes every event"
files: [src/agent_orchestrator/reconciler/loop.py, src/agent_orchestrator/reconciler/discard_hook.py, tests/test_discard_hook.py, README.md]
verify: "uv run pytest tests/test_discard_hook.py tests/test_reconciler.py -q && mise run lint"
depends_on: []
owns: []
uses: []
model: ""
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

# discard quiesce before export

## Requirement

Panel finding (medium, opus): reconciler/loop.py:312-323 runs the pre-discard export while agents may still have turns in flight, so events committed after the export query are cascade-deleted unexported. User requirement: discard deletes everything, history uploadable through the hook. Fix: on discard, first scale the StatefulSet to 0 (or interrupt agents) and wait until no agent pod is running and the ingester has drained their streams (bounded wait, then proceed and log), then export and run the hook, then delete. README Discard section states the order.

## Acceptance conditions

- AC1: discard scales agents to zero and waits before exporting [evidence: test:tests/test_discard_hook.py::test_discard_quiesces_before_export]
- AC2: events written before quiesce completes are in the export [evidence: test:tests/test_discard_hook.py::test_export_contains_in_flight_events]
- AC3: README Discard documents quiesce, export, hook, delete [evidence: doc-section:README.md#Discard]

## Files

- `src/agent_orchestrator/reconciler/loop.py`
- `src/agent_orchestrator/reconciler/discard_hook.py`
- `tests/test_discard_hook.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
