---
title: orch-rollout-dispatch-reservation
status: todo
repo: agents-orchestrator
value: the replacer never deletes a pod that was just handed a turn
files: [src/agents_orchestrator/reconciler/rollout.py, tests/test_rollout.py, MEMORY.md]
verify: uv run pytest tests/test_rollout.py -q
depends_on: [orch-rollout-replacer]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 950968
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch-rollout-dispatch-reservation

## Requirement

The rollout replacer must never delete an agent pod that holds a dispatch reservation. Today `reconciler/rollout.py` (the `BUSY` predicate at about line 50, shared with the scale-down drain) treats an agent as idle when `agent_status.state` is not `busy` and it has no message in `dispatching`/`verifying`, but the dispatcher has already handed the agent a turn once its last dispatch is newer than the moment it became free (`free_since > last_dispatched_at` is the dispatcher's idle condition; read `db/queue.py` `_PICK` and the agent/agent_status columns for the exact names). Between the dispatch and the wrapper reporting busy, the replacer can delete the pod mid-handoff (epic review finding, .scratchpad/session-loss/review/orchestrator.md "Consider" rollout.py:50). Make the shared busy predicate also count an agent whose last dispatch is newer than its free_since (the same reservation the dispatcher honours), so neither the replacer nor the scale-down drain removes it. Test first. Record the decision in MEMORY.md with the date and why.

## Acceptance conditions

- AC1: an idle agent whose last dispatch is newer than its free_since is busy for the replacer and its pod is not deleted [evidence: test:tests/test_rollout.py::test_replacer_skips_agent_with_dispatch_reservation]
- AC2: an idle agent whose free_since is newer than its last dispatch is still replaced [evidence: test:tests/test_rollout.py::test_replacer_replaces_idle_agent_without_reservation]
- AC3: MEMORY.md records the dispatch reservation in the busy predicate [evidence: command:grep -q "dispatch reservation" MEMORY.md]

## Files

- `src/agents_orchestrator/reconciler/rollout.py`
- `tests/test_rollout.py`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
