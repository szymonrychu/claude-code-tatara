---
title: fe shell and ribbon
status: in-progress
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
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-fe-shell-and-ribbon/agent-orchestrator
branch: agent-orchestrator-fe-shell-and-ribbon
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

- AC1: clusters render with state mark, ready/replicas and gauge [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/ribbon/Ribbon.test.tsx -t 'renders clusters with state count and gauge']
- AC2: expanding a cluster shows its agents with their own gauges [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/ribbon/Ribbon.test.tsx -t 'expands to agents with own gauges']
- AC3: a stream delta updates a row's state and gauge [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/ribbon/Ribbon.test.tsx -t 'applies stream deltas']
- AC4: selecting a row selects the cluster [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/ribbon/Ribbon.test.tsx -t 'selecting a row selects the cluster']
- AC5: phone layout uses a temporary drawer [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/ribbon/Ribbon.test.tsx -t 'phone layout uses temporary drawer']
- AC6: design rules still hold [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/layout/designRules.test.ts -t 'source files follow the design rules']

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

- `frontend/src/ribbon/useClusters.ts:useClusters() -> {clusters, agentsByCluster, selectedId, select}`
- `frontend/src/layout/Shell.tsx:Shell({aside, children})`

## Expected outcome

Opening the UI shows every cluster with live state, pod count and context.

## Steps

- Write Ribbon.test.tsx with the five named tests (jsdom, mocked client and stream). Run it; expect failures.
- Implement the files.
- Rerun; expect `5 passed`.
- Run the designRules test and `npm run lint`.

## Notes

No permanent left ribbon exists in ros2; the docked-column pattern is layout/MapSidebar.tsx:13,37-52 (brief-ui section 1). State is hand-rolled reducers, no react-query (D12).
