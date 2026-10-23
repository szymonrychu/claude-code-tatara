---
title: fe panel workspace
status: todo
repo: agent-orchestrator
value: "each cluster tab is a resizable files, chat and terminal workspace that remembers its layout"
files: [frontend/src/layout/Workspace.tsx, frontend/src/layout/panelLayout.ts, frontend/src/layout/Workspace.test.tsx, frontend/src/App.tsx]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/Workspace.test.tsx src/App.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: [fe-retire-ribbon, fe-deps-and-storage]
owns: [fe-workspace-slots]
uses: [fe-deps, fe-storage]
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

# fe panel workspace

## Requirement

The three-panel cluster workspace (design D7; user Q11, Q12), test-first.

- New `frontend/src/layout/panelLayout.ts`: pure layout state per cluster: `sizes` (three percentages, default `[25, 45, 30]`), `collapsed` (set of `files`, `chat`, `terminal`). Rules: `minimize(p)` is refused when it would leave no expanded panel (so at most two are minimized); `maximize(p)` collapses the other two and expands `p`; `restore(p)` expands `p`; `reset()` returns to the default sizes with nothing collapsed. Serialised and validated for storage.
- New `frontend/src/layout/Workspace.tsx`: `Workspace({clusterId, files, chat, terminal})` where the three props are React nodes (slots). Desktop and tablet: a `react-resizable-panels` `Group` (horizontal) of three collapsible `Panel`s with two `Separator`s; each expanded panel has a small header with its name and minimize and maximize `IconButton`s (`@mui/icons-material`, `aria-label`s "Minimize <name>", "Maximize <name>"); a minimized panel renders as a narrow vertical strip with its name and a restore button ("Restore <name>"); double-click on a separator calls `reset()`. Layout and collapsed set persist per cluster with `saveJson`/`loadJson` under `orch:layout:<clusterId>` and are restored when the tab is shown again. Phone: one panel at a time with a three-way `ToggleButtonGroup` (Files, Chat, Terminal), default Chat.
- `frontend/src/App.tsx` renders `Workspace` for the selected cluster with `chat` = `ChatView`, and placeholder text nodes for `files` and `terminal` (the next tasks fill them).

## Acceptance conditions

- AC1: minimize is refused for the last expanded panel, so at most two are minimized [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/Workspace.test.tsx -t at_most_two_minimized]
- AC2: maximize collapses the other two and restore expands a panel [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/Workspace.test.tsx -t maximize_and_restore]
- AC3: a minimized panel renders as a strip with its name and a restore button [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/Workspace.test.tsx -t minimized_strip_has_name_and_restore]
- AC4: double-click on a separator resets to 25/45/30 [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/Workspace.test.tsx -t separator_double_click_resets]
- AC5: layout persists per cluster and survives a remount; corrupt stored data falls back to the default [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/Workspace.test.tsx -t layout_persists_per_cluster]
- AC6: phone shows one panel at a time with a three-way switch, Chat by default [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/Workspace.test.tsx -t phone_three_way_switch]
- AC7: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/Workspace.test.tsx src/App.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

## Files

- `frontend/src/layout/Workspace.tsx`
- `frontend/src/layout/panelLayout.ts`
- `frontend/src/layout/Workspace.test.tsx`
- `frontend/src/App.tsx`

## Interfaces

- `Workspace({clusterId, files, chat, terminal})` slots (owns part `fe-workspace-slots`, consumed by fe-filesystem-panel and fe-terminal-panel).
- `panelLayout.ts` pure functions; uses `loadJson`/`saveJson` (part `fe-storage`) and `react-resizable-panels` 4 (`Group`, `Panel` with `collapsible`, `collapsedSize`, `panelRef` `collapse()`/`expand()`, `Separator`, `onLayoutChanged`) (part `fe-deps`).

## Expected outcome

Each cluster tab is a resizable three-panel workspace with chat in the middle, and its arrangement is remembered per cluster.

## Steps

- Write `frontend/src/layout/Workspace.test.tsx` (jsdom; mock `react-resizable-panels` with thin components that expose the imperative handle, or stub `ResizeObserver` if the real library works; titles as in the AC refs) and pure tests of `panelLayout.ts` in the same file; run `mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/Workspace.test.tsx`: fails.
- Implement `panelLayout.ts`, `Workspace.tsx`, wire `App.tsx`; run the verify command: passes.

## Notes

- react-resizable-panels v4 renamed components (`Group`, `Panel`, `Separator`); v3 examples with `PanelGroup`/`PanelResizeHandle` do not apply. Numbers are pixels, unit-less strings are percent.
- Keep `App.test.tsx` green (it now sees the workspace around ChatView).
