---
title: fe shell and ribbon
status: todo
repo: agent-orchestrator
value: "The left ribbon of clusters and agents with working or waiting state, pod counts and context gauges, live."
files: [frontend/src/App.tsx, frontend/src/layout/Shell.tsx, frontend/src/ribbon/Ribbon.tsx, frontend/src/ribbon/ClusterRow.tsx, frontend/src/ribbon/AgentRow.tsx, frontend/src/ribbon/useClusters.ts, frontend/src/components/StatusItem.tsx, frontend/src/ribbon/Ribbon.test.tsx]
verify: "cd frontend && npm ci --no-audit --no-fund && npx vitest run src/ribbon/Ribbon.test.tsx src/layout/designRules.test.ts && npm run lint"
depends_on: [fe-theme-port, fe-api-client-and-stream, fe-context-gauge]
owns: []
uses: [fe-theme, fe-api, context-gauge]
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

# fe shell and ribbon

## Requirement

The application shell and ribbon (D13).

`layout/Shell.tsx`:
- On desktop and tablet, a permanent left aside, modelled on ros2 MapSidebar: clamp width, panel background, 1 px border.
- On phone, a temporary Drawer behind a menu button in a dense top bar.
- A `main` pane to the right.

`ribbon/useClusters.ts`:
- A hand-rolled reducer, fed by the initial `listClusters` plus `listAgents` per cluster.
- It applies `/api/v1/stream` events (`snapshot`, `cluster_status`, `agent_status`, `message_status`) through openStream.
- It also keeps the selected cluster id.

`ribbon/Ribbon.tsx` lists clusters; an empty list shows an empty state.

`ribbon/ClusterRow.tsx` shows:
- a working or waiting mark (plus booting, error and deleting)
- the slug
- `ready/replicas`
- a ContextGauge of `summary.context_pct_max`, ticked at `summary.auto_compact_pct`
- an expand toggle

Selecting a row selects the cluster.

`ribbon/AgentRow.tsx` shows the ordinal, the pod name, the state mark, its own gauge, and free-since time for idle agents.

`components/StatusItem.tsx` is ported from ros2.

`App.tsx` renders the Shell with the Ribbon and a main pane. With no cluster selected the pane shows a prompt; otherwise it shows the selected slug.

## Acceptance conditions

- AC1: clusters render with state mark, ready/replicas and gauge [evidence: test:frontend/src/ribbon/Ribbon.test.tsx::renders clusters with state count and gauge]
- AC2: expanding a cluster shows its agents with their own gauges [evidence: test:frontend/src/ribbon/Ribbon.test.tsx::expands to agents with own gauges]
- AC3: a stream delta updates a row's state and gauge [evidence: test:frontend/src/ribbon/Ribbon.test.tsx::applies stream deltas]
- AC4: selecting a row selects the cluster [evidence: test:frontend/src/ribbon/Ribbon.test.tsx::selecting a row selects the cluster]
- AC5: phone layout uses a temporary drawer [evidence: test:frontend/src/ribbon/Ribbon.test.tsx::phone layout uses temporary drawer]
- AC6: design rules still hold [evidence: test:frontend/src/layout/designRules.test.ts::source files follow the design rules]

## Files

- `frontend/src/App.tsx`
- `frontend/src/layout/Shell.tsx`
- `frontend/src/ribbon/Ribbon.tsx`
- `frontend/src/ribbon/ClusterRow.tsx`
- `frontend/src/ribbon/AgentRow.tsx`
- `frontend/src/ribbon/useClusters.ts`
- `frontend/src/components/StatusItem.tsx`
- `frontend/src/ribbon/Ribbon.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
