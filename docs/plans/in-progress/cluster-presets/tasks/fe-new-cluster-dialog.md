---
title: fe new cluster dialog
status: in-progress
repo: agent-orchestrator
value: "New cluster in the UI is one preset choice and an optional slug, and each tab shows its preset"
files: [frontend/src/api/client.ts, frontend/src/clusters/NewClusterDialog.tsx, frontend/src/clusters/NewClusterDialog.test.tsx, frontend/src/App.tsx, frontend/src/App.test.tsx, frontend/src/layout/TopBar.tsx, frontend/src/layout/TopBar.test.tsx]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/clusters/NewClusterDialog.test.tsx src/App.test.tsx src/layout/TopBar.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build && mise x node@24.20.0 -- npm --prefix frontend run check:api"
depends_on: [create-cluster-from-preset]
owns: [fe-preset-client]
uses: [orch-presets-api, orch-cluster-create-api]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /home/user/claude-code-tatara/.claude/worktrees/cluster-presets-fe-new-cluster-dialog/agent-orchestrator
branch: cluster-presets-fe-new-cluster-dialog
verified_head: ""
run: ""
provides: []
---

# fe new cluster dialog

## Requirement

Schedule clusters from a preset in the UI and show where a cluster came from (design D6; user Q1, Q9), test-first. Builds on the merged web-ui-cluster-tabs-with-fil `App.tsx`, `TopBar.tsx` and their tests.

- `frontend/src/api/client.ts` (part `fe-preset-client`): type aliases `PresetView`, `PresetIn`, `CopyPreset` from `./schema`; `listPresets()`, `getPreset(id)`, `createPreset(body)`, `updatePreset(id, body)`, `deletePreset(id)`, `copyPreset(id, body?)` on `/presets`; `createCluster` takes a body typed as the regenerated `CreateCluster` (exactly one of `spec` or `preset_id` at runtime); `ClusterForm` create mode, still in the tree, keeps compiling against it; every task leaves `npm run build` and `npm run check:api` green.
- New `frontend/src/clusters/NewClusterDialog.tsx`: `NewClusterDialog({open, onClose, onCreated})`. On open it loads `listPresets()`; a preset `Select` (label "Preset") lists every preset by name with the default preselected; an optional "Slug" field with helper text saying an empty slug is generated from the preset name; a non-empty slug longer than `MAX_SLUG` blocks Create. Create posts `{preset_id}` plus `slug` only when non-empty, then calls `onCreated(cluster)`. There is no other field. A server error (404, 409, 422, the 422 naming the preset) shows in an outlined Alert and the dialog stays open.
- `frontend/src/App.tsx`: New cluster opens `NewClusterDialog` instead of `ClusterForm mode="create"`; on create the new cluster's tab is selected.
- `frontend/src/layout/TopBar.tsx`: a cluster tab shows `preset_name` as a caption under the slug when it is set; no marker shows that the preset changed after create (Q9).
- Tests: new `frontend/src/clusters/NewClusterDialog.test.tsx`; `frontend/src/App.test.tsx` `create_and_discard_from_top_bar` drives the new dialog; `frontend/src/layout/TopBar.test.tsx` gains `tab_shows_preset_name`. All pass `designRules`.

## Acceptance conditions

- AC1: the dialog lists presets with the default preselected and has no field besides Preset and Slug [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/clusters/NewClusterDialog.test.tsx -t preselects_default_and_only_preset_and_slug]
- AC2: Create sends only preset_id when the slug is empty and preset_id with slug when given, then calls onCreated [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/clusters/NewClusterDialog.test.tsx -t sends_preset_id_and_optional_slug]
- AC3: a server 422 naming the preset is shown and the dialog stays open; an over-long slug blocks Create [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/clusters/NewClusterDialog.test.tsx -t shows_server_error_and_blocks_long_slug]
- AC4: New cluster in the top bar opens the preset dialog and selects the created cluster; Discard still opens the discard dialog [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t create_and_discard_from_top_bar]
- AC5: a cluster tab shows its preset_name caption [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/TopBar.test.tsx -t tab_shows_preset_name]
- AC6: the preset client functions call the documented routes [evidence: symbol:frontend/src/api/client.ts::listPresets]
- AC7: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/clusters/NewClusterDialog.test.tsx src/App.test.tsx src/layout/TopBar.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]
- AC8: createCluster takes the regenerated CreateCluster body, ClusterForm create mode still compiles, and build and check:api pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend run build && mise x node@24.20.0 -- npm --prefix frontend run check:api]

## Files

- `frontend/src/api/client.ts`
- `frontend/src/clusters/NewClusterDialog.tsx`
- `frontend/src/clusters/NewClusterDialog.test.tsx`
- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`
- `frontend/src/layout/TopBar.tsx`
- `frontend/src/layout/TopBar.test.tsx`

## Interfaces

- `api/client.ts` (part `fe-preset-client`): `PresetView`, `PresetIn`, `CopyPreset`, `listPresets`, `getPreset`, `createPreset`, `updatePreset`, `deletePreset`, `copyPreset`; consumed by fe-preset-form and fe-presets-page.
- `NewClusterDialog({open, onClose, onCreated: (cluster: ClusterView) => void})`.
- `TopBar` props unchanged; the tab label reads `cluster.preset_name`.

## Expected outcome

Clicking New cluster asks for a preset (Default preselected) and an optional slug, creates the cluster and opens its tab; every tab shows which preset it came from.

## Steps

- Write `NewClusterDialog.test.tsx` (`// @vitest-environment jsdom`, stub `window.matchMedia`, `vi.mock('../api/client')` like the other tests; titles as in the AC refs), update `App.test.tsx` and add `tab_shows_preset_name` to `TopBar.test.tsx`; run `mise x node@24.20.0 -- npm --prefix frontend test -- src/clusters/NewClusterDialog.test.tsx src/App.test.tsx src/layout/TopBar.test.tsx`: fails.
- Add the client functions, the dialog, the App wiring and the tab caption; run the verify command: passes.

## Notes

- `schema.d.ts` already carries the preset and create schemas (tasks preset-routes and create-cluster-from-preset); never hand-edit it.
- `ClusterForm` stays in the tree until fe-preset-form; App simply stops opening it.
- The tab caption must fit the phone top bar (tabs scroll); use `Typography variant="caption"`.
- Builder check ruling 9 (2026-10-23): createCluster takes a body typed as the regenerated CreateCluster (exactly one of spec or preset_id at runtime); ClusterForm create mode keeps compiling; every task leaves `npm run build` and `npm run check:api` green.

- 2026-10-23 amended: builder check ruling 9: createCluster typed as CreateCluster, build and check:api green (AC8 added)
