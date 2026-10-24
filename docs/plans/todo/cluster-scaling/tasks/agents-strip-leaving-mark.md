---
title: agents strip leaving mark
status: todo
repo: agent-orchestrator
value: users see which agents are leaving and which wait for their turn to finish
files: [frontend/src/chat/AgentsStrip.tsx, frontend/src/chat/AgentsStrip.test.tsx, frontend/src/chat/ChatView.tsx]
verify: "cd frontend && npx vitest run src/chat/AgentsStrip.test.tsx && npm run lint"
depends_on: [scale-down-drain, scale-ui-control]
owns: []
uses: [scale-drain-status]
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

# agents strip leaving mark

## Requirement

Show which agents are leaving during a scale-down (design D3, D5; user S1, X2). In `frontend/src/chat/AgentsStrip.tsx` an agent with `ordinal >= cluster.spec.replicas` that is not gone carries a "leaving" label (also in its aria-label); when `cluster.status.drain.waiting` includes its ordinal the label reads "leaving after its turn". `frontend/src/chat/ChatView.tsx` passes `replicas` and the drain waiting list from the cluster view. The strip keeps its existing filter behaviour. API callers derive the same from `ClusterView.spec.replicas`, `AgentView.ordinal` and `status.drain` (documented by the public scale route task).

## Acceptance conditions

- AC1: an agent above spec.replicas shows "leaving" and an agent in status.drain.waiting shows "leaving after its turn" [evidence: command:cd frontend && npx vitest run src/chat/AgentsStrip.test.tsx -t "leaving"]
- AC2: agents within spec.replicas show no leaving label and the filter toggle still works [evidence: command:cd frontend && npx vitest run src/chat/AgentsStrip.test.tsx]
- AC3: lint and typecheck build pass [evidence: command:cd frontend && npm run lint && npm run build]

## Files

- `frontend/src/chat/AgentsStrip.tsx`
- `frontend/src/chat/AgentsStrip.test.tsx`
- `frontend/src/chat/ChatView.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
