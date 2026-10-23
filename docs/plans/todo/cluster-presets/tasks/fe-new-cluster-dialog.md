---
title: fe new cluster dialog
status: todo
repo: agent-orchestrator
value: "New cluster in the UI is one preset choice and an optional slug, and each tab shows its preset"
files: [frontend/src/api/client.ts, frontend/src/clusters/NewClusterDialog.tsx, frontend/src/clusters/NewClusterDialog.test.tsx, frontend/src/App.tsx, frontend/src/App.test.tsx, frontend/src/layout/TopBar.tsx, frontend/src/layout/TopBar.test.tsx]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/clusters/NewClusterDialog.test.tsx src/App.test.tsx src/layout/TopBar.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: [create-cluster-from-preset]
owns: [fe-preset-client]
uses: [orch-presets-api, orch-cluster-create-api]
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

# fe new cluster dialog

## Requirement

Schedule clusters from a preset in the UI and show where a cluster came from (design D6; user Q1, Q9), test-first. Builds on the merged web-ui-cluster-tabs-with-fil `App.tsx`, `TopBar.tsx` and their tests.

- `frontend/src/api/client.ts` (part `fe-preset-client`): type aliases `PresetView`, `PresetIn`, `CopyPreset` from `./schema`; `listPresets()`, `getPreset(id)`, `createPreset(body)`, `updatePreset(id, body)`, `deletePreset(id)`, `copyPreset(id, body?)` on `/presets`; `createCluster` takes the new `CreateCluster` body.
- New `frontend/src/clusters/NewClusterDialog.tsx`: `NewClusterDialog({open, onClose, onCreated})`. On open it loads `listPresets()`; a preset `Select` (label "Preset") lists every preset by name with the default preselected; an optional "Slug" field with helper text saying an empty slug is generated from the preset name; a non-empty slug longer than `MAX_SLUG` blocks Create. Create posts `{preset_id}` plus `slug` only when non-empty, then calls `onCreated(cluster)`. There is no other field. A server error (404, 409, 422, the 422 naming the preset) shows in an outlined Alert and the dialog stays open.
- `frontend/src/App.tsx`: New cluster opens `NewClusterDialog` instead of `ClusterForm mode="create"`; on create the new cluster's tab is selected.
- `frontend/src/layout/TopBar.tsx`: a cluster tab shows `preset_name` as a caption under the slug when it is set; there is no marker for later preset changes (Q9).
- Tests: new `frontend/src/clusters/NewClusterDialog.test.tsx`; `frontend/src/App.test.tsx` `create_and_discard_from_top_bar` drives the new dialog; `frontend/src/layout/TopBar.test.tsx` gains `tab_shows_preset_name`. All pass `designRules`.

## Acceptance conditions

- AC1: the dialog lists presets with the default preselected and has no field besides Preset and Slug [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/clusters/NewClusterDialog.test.tsx -t preselects_default_and_only_preset_and_slug]
- AC2: Create sends only preset_id when the slug is empty and preset_id with slug when given, then calls onCreated [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/clusters/NewClusterDialog.test.tsx -t sends_preset_id_and_optional_slug]
- AC3: a server 422 naming the preset is shown and the dialog stays open; an over-long slug blocks Create [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/clusters/NewClusterDialog.test.tsx -t shows_server_error_and_blocks_long_slug]
- AC4: New cluster in the top bar opens the preset dialog and selects the created cluster; Discard still opens the discard dialog [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t create_and_discard_from_top_bar]
- AC5: a cluster tab shows its preset_name caption [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/TopBar.test.tsx -t tab_shows_preset_name]
- AC6: the preset client functions call the documented routes [evidence: symbol:frontend/src/api/client.ts::listPresets]
- AC7: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/clusters/NewClusterDialog.test.tsx src/App.test.tsx src/layout/TopBar.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

## Files

- `frontend/src/api/client.ts`
- `frontend/src/clusters/NewClusterDialog.tsx`
- `frontend/src/clusters/NewClusterDialog.test.tsx`
- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`
- `frontend/src/layout/TopBar.tsx`
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
