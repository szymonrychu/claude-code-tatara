---
title: fe top bar
status: todo
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
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# fe top bar

## Requirement

Build the top bar and the hamburger sessions menu as standalone components (user Q1, Q14, Q15), test-first; wiring into App is task fe-retire-ribbon.

- New `frontend/src/layout/TopBar.tsx`: `TopBar({clusters, selectedId, onSelect, onNew, onDiscard, settingsCategories})`. Left to right: a hamburger `IconButton` (MUI `MenuIcon`, `aria-label="Open menu"`), a MUI `Tabs` `variant="scrollable"` with one tab per cluster in `sortedClusters` order (label: `StateMark`, slug, `ContextGauge` with the cluster's `context_pct_max` and auto-compact tick), the active tab = `selectedId`, then a "New cluster" button. Each tab has an actions button (`aria-label="Cluster actions"`) opening a `Menu` whose only item is "Discard" (calls `onDiscard(cluster)`); there is no Edit item. Tabs cannot be closed.
- New `frontend/src/layout/SessionsMenu.tsx`: `SessionsMenu({open, onClose, clusters, selectedId, onSelect, settingsCategories})`, a temporary MUI `Drawer` anchored left: a "Sessions" list from the top, one item per cluster (state mark and slug, the selected one marked), choosing one calls `onSelect(id)` and closes; a "Settings" section pinned to the bottom that renders one item per entry of `settingsCategories: {id, label, onOpen}[]` and the text "No settings yet" when the list is empty (this epic passes an empty list; the cluster-presets epic adds Presets).
- Both pass `designRules` (no colour literals, no decorative Unicode, no `title=` on buttons); icons come from `@mui/icons-material`.

## Acceptance conditions

- AC1: one tab per cluster in slug order with state mark, slug and gauge, the selected one active, and selecting a tab calls onSelect [evidence: test:frontend/src/layout/TopBar.test.tsx::tabs_one_per_cluster_in_slug_order]
- AC2: the tab actions menu offers Discard only, no Edit [evidence: test:frontend/src/layout/TopBar.test.tsx::tab_actions_offer_discard_only]
- AC3: New cluster calls onNew [evidence: test:frontend/src/layout/TopBar.test.tsx::new_cluster_button]
- AC4: the hamburger opens the drawer listing sessions from the top, and choosing one selects it and closes the drawer [evidence: test:frontend/src/layout/TopBar.test.tsx::hamburger_lists_sessions_and_selects]
- AC5: the settings section sits at the bottom, renders given categories and shows the empty state when none [evidence: test:frontend/src/layout/TopBar.test.tsx::settings_section_bottom_with_empty_state]
- AC6: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/TopBar.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

## Files

- `frontend/src/layout/TopBar.tsx`
- `frontend/src/layout/SessionsMenu.tsx`
- `frontend/src/layout/TopBar.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
