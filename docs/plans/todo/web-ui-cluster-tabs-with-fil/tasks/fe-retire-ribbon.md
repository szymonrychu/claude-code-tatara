---
title: fe retire ribbon
status: todo
repo: agent-orchestrator
value: the UI navigates clusters by top tabs and the left ribbon is gone
files: [frontend/src/App.tsx, frontend/src/App.test.tsx, frontend/src/layout/Shell.tsx, frontend/src/ribbon/Ribbon.tsx, frontend/src/ribbon/ClusterRow.tsx, frontend/src/ribbon/Ribbon.test.tsx, frontend/src/clusters/ClusterForm.test.tsx]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/App.test.tsx src/clusters/ClusterForm.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: [fe-top-bar]
owns: []
uses: [fe-sessions-menu]
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

# fe retire ribbon

## Requirement

Replace the left ribbon with the top bar in the app and retire the ribbon (user Q1, Q15; design D10), with retirement tests.

- `frontend/src/App.tsx` renders `TopBar` (task fe-top-bar) above the main area on every layout (phone, tablet, desktop); the hamburger opens `SessionsMenu` with an empty `settingsCategories`. App hosts the dialogs the ribbon owned: New cluster opens `ClusterForm mode="create"` (on save the new cluster's tab is selected); tab Discard opens `DiscardClusterDialog`. The main area renders `ChatView` for the selected cluster (the workspace panels arrive in fe-panel-workspace); with no clusters it shows "No clusters yet" and the New cluster button stays in the bar; the list load error is shown as before.
- Selection default (D10): when no tab is selected and clusters exist, the first cluster by slug is selected; when the selected cluster disappears, the first remaining one is.
- `frontend/src/layout/Shell.tsx` no longer renders an aside or the `ribbon-aside`/`ribbon-drawer` test ids (rewrite as the top-bar shell or delete it).
- Deleted: `frontend/src/ribbon/Ribbon.tsx`, `frontend/src/ribbon/ClusterRow.tsx`, `frontend/src/ribbon/Ribbon.test.tsx`; the "Ribbon wiring" test in `frontend/src/clusters/ClusterForm.test.tsx` is removed (its create and discard coverage moves to `App.test.tsx`). No UI path opens `ClusterForm mode="edit"`; the edit mode code itself and `patchCluster` stay (the cluster-presets epic removes them).

## Acceptance conditions

- AC1: the app shows the top bar with one tab per cluster and the selected cluster's chat, and no aside [evidence: test:frontend/src/App.test.tsx::top_bar_replaces_ribbon]
- AC2: with no selection the first cluster by slug is selected, also after the selected one disappears [evidence: test:frontend/src/App.test.tsx::first_tab_selected_by_default]
- AC3: New cluster opens the create form and selects the created cluster; Discard opens the discard dialog [evidence: test:frontend/src/App.test.tsx::create_and_discard_from_top_bar]
- AC4: no Edit entry point exists in the rendered UI [evidence: test:frontend/src/App.test.tsx::no_edit_entry_point]
- AC5: Ribbon.tsx, ClusterRow.tsx and Ribbon.test.tsx are gone from git ls-files [evidence: test:frontend/src/App.test.tsx::ribbon_files_retired]
- AC6: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/App.test.tsx src/clusters/ClusterForm.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

## Files

- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`
- `frontend/src/layout/Shell.tsx`
- `frontend/src/ribbon/Ribbon.tsx`
- `frontend/src/ribbon/ClusterRow.tsx`
- `frontend/src/ribbon/Ribbon.test.tsx`
- `frontend/src/clusters/ClusterForm.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
