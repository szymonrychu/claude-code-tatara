---
title: ui leader badge
status: todo
repo: agent-orchestrator
value: the user sees the leader in the agents strip and can make any agent leader
files: [frontend/src/chat/AgentsStrip.tsx, frontend/src/chat/AgentsStrip.test.tsx, frontend/src/api/client.ts, frontend/src/chat/useClusterChat.ts]
verify: "cd frontend && npx vitest run src/chat/AgentsStrip.test.tsx && npm run lint"
depends_on: [views-leader-stream]
owns: []
uses: [orch-leader-views]
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
