---
title: web clusters page
status: todo
repo: agents-web
value: "clusters get their own page in the hamburger menu, above Presets"
files: [src/clusters/ClustersPage.tsx, src/clusters/ClustersPage.test.tsx, src/App.tsx, src/App.test.tsx]
verify: "npx vitest run src/clusters/ClustersPage.test.tsx src/App.test.tsx && npm run lint"
depends_on: [web-form-config-fields]
owns: [web-settings-menu-order]
uses: [web-orch-schema-config, orch-cluster-config-api, orch-settings-menu]
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

# web clusters page

## Requirement

Give Clusters its own page in the hamburger menu, above Presets (design D7; approvals A5, A8).

- `src/App.tsx`: `settingsCategories` lists `{id: 'clusters', label: 'Clusters'}` first and Presets second; the `view` state gains `'clusters'`, which renders the Clusters page in the main area. The Sessions quick-switch list stays.
- `src/clusters/ClustersPage.tsx`: lists every cluster from `GET /api/v1/clusters` with slug, preset name, state, pods ready of replicas, created time and autoclose time left (from `closes_at`, "never" when null), refreshed like the Presets page; actions: open (selects the cluster and returns to the cluster view), new (opens `NewClusterDialog`) and discard (opens `DiscardClusterDialog`, which calls `DELETE /api/v1/clusters/{id}`).
- Tests in `src/clusters/ClustersPage.test.tsx` and `src/App.test.tsx`.

Interfaces: builds cross-epic contract `web-settings-menu-order` (Clusters first, Presets last; the webhook and schedule epics insert their entries between them); uses `web-orch-schema-config`, `orch-cluster-config-api` and the menu contract `orch-settings-menu`.

Notes: reuse `PresetsPage` layout patterns, `NewClusterDialog` and `DiscardClusterDialog` unchanged. Paths assume frontend-decoupling's layout (design D12).

## Acceptance conditions

- AC1: the Settings section lists Clusters first and Presets after it, and Clusters opens the Clusters page [evidence: command:npx vitest run src/App.test.tsx -t "clusters entry"]
- AC2: the page lists every cluster with slug, preset, state, ready of replicas, created and time left or never [evidence: command:npx vitest run src/clusters/ClustersPage.test.tsx -t "lists clusters"]
- AC3: open selects the cluster view, new opens the new cluster dialog, and discard opens the discard dialog that calls DELETE [evidence: command:npx vitest run src/clusters/ClustersPage.test.tsx -t "actions"]
- AC4: lint passes [evidence: command:npm run lint]

## Files

- `src/clusters/ClustersPage.tsx`
- `src/clusters/ClustersPage.test.tsx`
- `src/App.tsx`
- `src/App.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
