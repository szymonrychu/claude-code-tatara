---
title: ui leader badge
status: done
repo: agent-orchestrator
value: the user sees the leader in the agents strip and can make any agent leader
files: [frontend/src/chat/AgentsStrip.tsx, frontend/src/chat/AgentsStrip.test.tsx, frontend/src/api/client.ts, frontend/src/chat/useClusterChat.ts]
verify: "cd frontend && npx vitest run src/chat/AgentsStrip.test.tsx && npm run lint"
depends_on: [views-leader-stream]
model: ""
review: ""
verified_head: 1b1b6bbf40ba3f13faf4469eb9c5c5224974dae5
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 14
actual_tokens: 960546
actual_roles: "impl 13, review 1"
actual_role_tokens: "impl 847753, review 112793"
---

# ui leader badge

## Requirement

The UI shows and sets the leader (Q9, Q10). In the agents strip (`chat/AgentsStrip.tsx`): a "leader" badge on the leading agent with the epoch in its tooltip; each agent's context percent visible; an agent action "Make leader" on non-leader agents of hive clusters calling `POST /api/v1/clusters/{id}/leader` (`api/client.ts`), with errors shown inline. The strip updates from `leader_changed` and `agent_status` frames (`chat/useClusterChat.ts`). Alone clusters show neither badge nor action.

## Acceptance conditions

- AC1: the leader badge renders on the leader with the epoch tooltip and is absent on alone clusters [evidence: command:cd frontend && npx vitest run src/chat/AgentsStrip.test.tsx -t "leader badge"]
- AC2: Make leader calls the leader route for a non-leader agent and shows an error inline on failure [evidence: command:cd frontend && npx vitest run src/chat/AgentsStrip.test.tsx -t "make leader"]
- AC3: a leader_changed frame moves the badge and context percent is shown per agent [evidence: command:cd frontend && npx vitest run src/chat/AgentsStrip.test.tsx -t "leader_changed"]
- AC4: lint, build and the API drift check pass [evidence: command:cd frontend && npm run lint && npm run build && npm run check:api]

## Files

- `frontend/src/chat/AgentsStrip.tsx`
- `frontend/src/chat/AgentsStrip.test.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/chat/useClusterChat.ts`

## Interfaces

- Uses `ClusterView.leader_agent_id`, `AgentView.leader`, `context_pct`, the `leader_changed` frame and `POST /api/v1/clusters/{id}/leader`.

## Expected outcome

The agents strip shows the leader and offers "Make leader".

## Steps

- Red: add "leader badge", "make leader" and "leader_changed" cases to `AgentsStrip.test.tsx`; run `cd frontend && npx vitest run src/chat/AgentsStrip.test.tsx`: fails.
- Green: badge, action, client call, frame handling; run the verify command: passes.

## Notes

- Frontend commands: `npm --prefix frontend run test|lint|build`; `check:api` guards schema drift.
