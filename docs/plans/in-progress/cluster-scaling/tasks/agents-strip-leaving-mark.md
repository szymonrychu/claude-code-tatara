---
title: agents strip leaving mark
status: in-progress
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

- Consumes `ClusterView.status.drain.waiting` (part `scale-drain-status`) and `ClusterView.spec.replicas`.
- `AgentsStripProps` gains `replicas: number` and `drainWaiting?: number[]`.

## Expected outcome

During a scale-down the agents strip marks the leaving agents and those still finishing a turn.

## Steps

- Red: add the leaving cases to `frontend/src/chat/AgentsStrip.test.tsx`; run `cd frontend && npx vitest run src/chat/AgentsStrip.test.tsx -t leaving`: fails.
- Green: add the props and labels; pass them from ChatView; run the verify command and `npm run build`.

## Notes

- `status` is a free-form dict in the types; read `drain` defensively (absent when no drain).
