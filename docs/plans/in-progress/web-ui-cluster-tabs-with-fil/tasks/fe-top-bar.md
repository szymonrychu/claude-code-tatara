---
title: fe top bar
status: done
repo: agent-orchestrator
value: clusters are tabs at the top with a hamburger menu of sessions and settings
files: [frontend/src/layout/TopBar.tsx, frontend/src/layout/SessionsMenu.tsx, frontend/src/layout/TopBar.test.tsx]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/TopBar.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: [fe-deps-and-storage]
owns: [fe-sessions-menu]
uses: [fe-deps]
model: ""
estimate: 5
estimate_by: formula
actual: 8
actual_roles: "impl 2, verify 4, review 1, fix 1, land 1"
review: ""
worktree: /home/user/claude-code-tatara/.claude/worktrees/web-ui-cluster-tabs-with-fil-fe-top-bar/agent-orchestrator
branch: web-ui-cluster-tabs-with-fil-fe-top-bar
verified_head: 997f078e838f0a9a51d8124d0c10ee202e7b87e9
run: web-ui-cluster-tabs-with-fil
provides: [sessions-menu]
acs_for_audit: []
process_gaps: []
fork_point: 093a155e09ab1248b87d755d1828432fc82b89e9
---

# fe top bar

## Requirement

Build the top bar and the hamburger sessions menu as standalone components (user Q1, Q14, Q15), test-first; wiring into App is task fe-retire-ribbon.

- New `frontend/src/layout/TopBar.tsx`: `TopBar({clusters, selectedId, onSelect, onNew, onDiscard, settingsCategories})`. Left to right: a hamburger `IconButton` (MUI `MenuIcon`, `aria-label="Open menu"`), a MUI `Tabs` `variant="scrollable"` with one tab per cluster in `sortedClusters` order (label: `StateMark`, slug, `ContextGauge` with the cluster's `context_pct_max` and auto-compact tick), the active tab = `selectedId`, then a "New cluster" button. Each tab has an actions button (`aria-label="Cluster actions"`) opening a `Menu` whose only item is "Discard" (calls `onDiscard(cluster)`); there is no Edit item. Tabs cannot be closed.
- New `frontend/src/layout/SessionsMenu.tsx`: `SessionsMenu({open, onClose, clusters, selectedId, onSelect, settingsCategories})`, a temporary MUI `Drawer` anchored left: a "Sessions" list from the top, one item per cluster (state mark and slug, the selected one marked), choosing one calls `onSelect(id)` and closes; a "Settings" section pinned to the bottom that renders one item per entry of `settingsCategories: {id, label, onOpen}[]` and the text "No settings yet" when the list is empty (this epic passes an empty list; the cluster-presets epic adds Presets).
- Both pass `designRules` (no colour literals, no decorative Unicode, no `title=` on buttons); icons come from `@mui/icons-material`.

## Acceptance conditions

- AC1: one tab per cluster in slug order with state mark, slug and gauge, the selected one active, and selecting a tab calls onSelect [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/TopBar.test.tsx -t tabs_one_per_cluster_in_slug_order]
- AC2: the tab actions menu offers Discard only, no Edit [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/TopBar.test.tsx -t tab_actions_offer_discard_only]
- AC3: New cluster calls onNew [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/TopBar.test.tsx -t new_cluster_button]
- AC4: the hamburger opens the drawer listing sessions from the top, and choosing one selects it and closes the drawer [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/TopBar.test.tsx -t hamburger_lists_sessions_and_selects]
- AC5: the settings section sits at the bottom, renders given categories and shows the empty state when none [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/TopBar.test.tsx -t settings_section_bottom_with_empty_state]
- AC6: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/TopBar.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

## Files

- `frontend/src/layout/TopBar.tsx`
- `frontend/src/layout/SessionsMenu.tsx`
- `frontend/src/layout/TopBar.test.tsx`

## Interfaces

- `TopBar` props as above; `SessionsMenu` props including `settingsCategories: {id: string, label: string, onOpen: () => void}[]` (owns part `fe-sessions-menu`, consumed by fe-retire-ribbon; cross-epic contract `orch-settings-menu`, consumed by cluster-presets).
- Uses `StateMark` (`ribbon/stateMark.tsx`), `ContextGauge` (`ribbon/ContextGauge.tsx`), `sortedClusters` and `ClusterEntry` (`ribbon/useClusters.ts`), part `fe-deps` (icons).

## Expected outcome

A tested top bar and drawer ready to replace the ribbon, with the settings area the presets epic will fill.

## Steps

- Write `frontend/src/layout/TopBar.test.tsx` (`// @vitest-environment jsdom`, stub `window.matchMedia` like the other tests; titles exactly as in the AC refs); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/TopBar.test.tsx`: fails.
- Implement `TopBar.tsx` and `SessionsMenu.tsx`; rerun: passes; run the verify command.

## Notes

- `StateMark`, `ContextGauge` and `useClusters.ts` stay where they are (under `ribbon/`); moving them is not in scope.
- The cluster-presets epic will add a Presets entry through `settingsCategories` and remove the ClusterForm edit code; keep that prop generic.
