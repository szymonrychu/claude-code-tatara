---
title: fe retire ribbon
status: done
repo: agent-orchestrator
value: the UI navigates clusters by top tabs and the left ribbon is gone
files: [frontend/src/App.tsx, frontend/src/App.test.tsx, frontend/src/layout/Shell.tsx, frontend/src/ribbon/Ribbon.tsx, frontend/src/ribbon/ClusterRow.tsx, frontend/src/ribbon/Ribbon.test.tsx, frontend/src/clusters/ClusterForm.test.tsx]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/App.test.tsx src/clusters/ClusterForm.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: [fe-top-bar]
model: ""
review: ""
verified_head: c58e22096af1d5588687a3032307037e81b20fee
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 11
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# fe retire ribbon

## Requirement

Replace the left ribbon with the top bar in the app and retire the ribbon (user Q1, Q15; design D10), with retirement tests.

- `frontend/src/App.tsx` renders `TopBar` (task fe-top-bar) above the main area on every layout (phone, tablet, desktop); the hamburger opens `SessionsMenu` with an empty `settingsCategories`. App hosts the dialogs the ribbon owned: New cluster opens `ClusterForm mode="create"` (on save the new cluster's tab is selected); tab Discard opens `DiscardClusterDialog`. The main area renders `ChatView` for the selected cluster (the workspace panels arrive in fe-panel-workspace); with no clusters it shows "No clusters yet" and the New cluster button stays in the bar; the list load error is shown as before.
- Selection default (D10): when no tab is selected and clusters exist, the first cluster by slug is selected; when the selected cluster disappears, the first remaining one is.
- `frontend/src/layout/Shell.tsx` no longer renders an aside or the `ribbon-aside`/`ribbon-drawer` test ids (rewrite as the top-bar shell or delete it).
- Deleted: `frontend/src/ribbon/Ribbon.tsx`, `frontend/src/ribbon/ClusterRow.tsx`, `frontend/src/ribbon/Ribbon.test.tsx`; the "Ribbon wiring" test in `frontend/src/clusters/ClusterForm.test.tsx` is removed (its create and discard coverage moves to `App.test.tsx`). No UI path opens `ClusterForm mode="edit"`; the edit mode code itself and `patchCluster` stay (the cluster-presets epic removes them).

## Acceptance conditions

- AC1: the app shows the top bar with one tab per cluster and the selected cluster's chat, and no aside [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t top_bar_replaces_ribbon]
- AC2: with no selection the first cluster by slug is selected, also after the selected one disappears [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t first_tab_selected_by_default]
- AC3: New cluster opens the create form and selects the created cluster; Discard opens the discard dialog [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t create_and_discard_from_top_bar]
- AC4: no Edit entry point exists in the rendered UI [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t no_edit_entry_point]
- AC5: Ribbon.tsx, ClusterRow.tsx and Ribbon.test.tsx are gone from git ls-files [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t ribbon_files_retired]
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

- Uses `TopBar` and `SessionsMenu` (part `fe-sessions-menu`), `ClusterForm`, `DiscardClusterDialog`, `useClusters`.

## Expected outcome

The running UI has tabs at the top and no left ribbon; the ribbon sources are gone from the repo.

## Steps

- Rewrite `frontend/src/App.test.tsx` with the five tests (titles as in the AC refs; the retirement test runs `git ls-files src/ribbon/Ribbon.tsx src/ribbon/ClusterRow.tsx src/ribbon/Ribbon.test.tsx` with `node:child_process` from the frontend dir and expects empty output); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/App.test.tsx`: fails.
- Rewire `App.tsx`, rewrite or delete `Shell.tsx`, delete the ribbon files with `git rm`, drop the Ribbon wiring test; rerun; run the verify command: passes.

## Notes

- Retirement tests assert on `git ls-files`, never on the filesystem (an untracked file can survive a merge). This task's deletions are pinned by `ribbon_files_retired`.
- `ribbon/AgentRow.tsx` stays for now (task fe-agents-strip retires it); `ribbon/useClusters.ts`, `stateMark.tsx`, `ContextGauge.tsx` stay.
- Keep `useLayout` breakpoints; on phone the top bar must still fit (tabs scroll).
