---
title: scale ui control
status: done
repo: agent-orchestrator
value: users grow or shrink a cluster from the cluster view within its cap
files: [frontend/src/chat/ScaleControl.tsx, frontend/src/chat/ScaleControl.test.tsx, frontend/src/chat/ChatView.tsx, frontend/src/api/client.ts]
verify: "cd frontend && npx vitest run src/chat/ScaleControl.test.tsx && npm run lint"
depends_on: [public-scale-route]
model: ""
review: ""
verified_head: b484c95d547ff7f70f72ebe5969a717407413621
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 3
actual_tokens: 656326
actual_roles: "impl 2, review 1"
actual_role_tokens: "impl 556543, review 99783"
---

# scale ui control

## Requirement

Add the scale control to the cluster view (design D5; user S2, S3, X2). New `frontend/src/chat/ScaleControl.tsx`, rendered by `frontend/src/chat/ChatView.tsx` in the header next to the agents strip for the selected cluster. It shows `<spec.replicas> of <spec.max_replicas> agents` and two IconButtons, aria-labels "Remove an agent" and "Add an agent", that call the new `scaleCluster(clusterId, {replicas})` in `frontend/src/api/client.ts` (`POST /clusters/{id}/scale`, typed from `schema.d.ts`) with replicas minus or plus one. Buttons are disabled at the bounds (1 and max_replicas) and while a request is in flight. A static cluster shows the count with both buttons disabled and the tooltip "Static cluster: scaling is off"; an alone cluster (max_replicas 1) renders no control. The control does not update optimistically: the count follows the cluster view from the status stream. An API error is shown inline under the control with the API message; for `leader_would_leave` the text adds "Make another agent leader first."

## Acceptance conditions

- AC1: clicking Add an agent posts replicas + 1 to /clusters/{id}/scale and Remove an agent posts replicas - 1 [evidence: command:cd frontend && npx vitest run src/chat/ScaleControl.test.tsx -t "posts scale"]
- AC2: the buttons are disabled at 1, at max_replicas and while a request is in flight [evidence: command:cd frontend && npx vitest run src/chat/ScaleControl.test.tsx -t "bounds"]
- AC3: a static cluster shows disabled buttons with the static tooltip and an alone cluster renders no control [evidence: command:cd frontend && npx vitest run src/chat/ScaleControl.test.tsx -t "static and alone"]
- AC4: an API error is shown inline, with the make-leader hint for leader_would_leave [evidence: command:cd frontend && npx vitest run src/chat/ScaleControl.test.tsx -t "errors"]
- AC5: lint and typecheck build pass [evidence: command:cd frontend && npm run lint && npm run build]

## Files

- `frontend/src/chat/ScaleControl.tsx`
- `frontend/src/chat/ScaleControl.test.tsx`
- `frontend/src/chat/ChatView.tsx`
- `frontend/src/api/client.ts`

## Interfaces

- Consumes `POST /api/v1/clusters/{cluster_id}/scale` (part `orch-cluster-scale-api`) via `frontend/src/api/client.ts::scaleCluster`, and `ClusterView.spec.replicas`, `max_replicas`, `static`.

## Expected outcome

The chat header of a scalable cluster shows the agent count with add and remove buttons that scale it through the public API.

## Steps

- Red: write `frontend/src/chat/ScaleControl.test.tsx` with the four cases (mock `fetch` like the existing component tests); run `cd frontend && npx vitest run src/chat/ScaleControl.test.tsx`: fails.
- Green: add `scaleCluster`, the component and its mount in ChatView; run the verify command and `npm run build`.

## Notes

- Reuse the MUI IconButton and Tooltip patterns of `layout/TopBar.tsx` and the TOKENS font sizes.
- No new route or field: the control reads the cluster view it already has.
