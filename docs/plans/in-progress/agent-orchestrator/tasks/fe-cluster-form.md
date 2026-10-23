---
title: fe cluster form
status: in-progress
repo: agent-orchestrator
value: "Defines new clusters with their full config and discards them safely, from the UI."
files: [frontend/src/clusters/ClusterForm.tsx, frontend/src/clusters/DiscardClusterDialog.tsx, frontend/src/ribbon/Ribbon.tsx, frontend/src/ribbon/ClusterRow.tsx, frontend/src/clusters/ClusterForm.test.tsx]
verify: "cd frontend && npm ci --no-audit --no-fund && npx vitest run src/clusters/ClusterForm.test.tsx src/layout/designRules.test.ts && npm run lint"
depends_on: [fe-shell-and-ribbon]
owns: []
uses: [fe-api, fe-theme]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-fe-cluster-form/agent-orchestrator
branch: agent-orchestrator-fe-cluster-form
verified_head: ""
run: ""
provides: []
---

# fe cluster form

## Requirement

Cluster create, edit and discard (D6, D15).

`ClusterForm.tsx` is a dialog in create and edit modes, with defaults from `getMeta`. Fields:
- slug (create only; DNS-1123, at most 40 characters, validated inline)
- replicas (1-16), model (a select from meta models, or free text when none), effort, peers switch
- workdir, PVC size (create only)
- env as key and value rows (secret-looking keys rejected inline)
- any-mcp config (JSON textarea, validated)
- max attempts (default 5 from meta: automatic retries), auto-compact percent, CPU and memory requests and limits
- pre-discard webhook URL (`discard_hook_url`, optional, http or https validated inline)

Submit calls `createCluster` or `patchCluster` and shows server 409 and 422 messages at the field or in an Alert.

`DiscardClusterDialog.tsx`:
- Built on ConfirmDialog.
- States that everything is deleted: the agents, the workspace PVC and its files, and the cluster's whole chat history. There is no undo and no separate history option (D15).
- When a pre-discard hook applies (the cluster's `discard_hook_url`, or meta `discard_hook` not `none`), it states that the full history is exported to that hook first, and that a failing hook holds the discard. The cluster row shows `discard_hook_failed` from the status while that happens.
- Requires typing the slug to enable Discard.
- Calls `deleteCluster` (no purge parameter).

The Ribbon header gains a `New cluster` button. ClusterRow gains a menu with Edit and Discard.

## Acceptance conditions

- AC1: creating a cluster posts the full spec [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/clusters/ClusterForm.test.tsx -t 'creates cluster with full spec']
- AC2: invalid slug and secret env keys are rejected inline [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/clusters/ClusterForm.test.tsx -t 'validates slug and env keys']
- AC3: editing patches the spec with slug and PVC size locked [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/clusters/ClusterForm.test.tsx -t 'edit patches spec']
- AC4: server 409 and 422 errors are shown [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/clusters/ClusterForm.test.tsx -t 'shows server errors']
- AC5: discard requires the typed slug and names the PVC and history deletion [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/clusters/ClusterForm.test.tsx -t 'discard requires typed slug']
- AC7: the discard dialog names the pre-discard hook when one applies and the form validates discard_hook_url [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/clusters/ClusterForm.test.tsx -t 'discard names the export hook']
- AC6: design rules still hold [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/layout/designRules.test.ts -t 'source files follow the design rules']

## Files

- `frontend/src/clusters/ClusterForm.tsx`
- `frontend/src/clusters/DiscardClusterDialog.tsx`
- `frontend/src/ribbon/Ribbon.tsx`
- `frontend/src/ribbon/ClusterRow.tsx`
- `frontend/src/clusters/ClusterForm.test.tsx`

## Interfaces

- `frontend/src/clusters/ClusterForm.tsx:ClusterForm({mode, cluster?, onClose})`; `frontend/src/clusters/DiscardClusterDialog.tsx:DiscardClusterDialog({cluster, onClose})`

## Expected outcome

Clusters can be defined with their config, edited and discarded from the UI.

## Steps

- Write ClusterForm.test.tsx with the five named tests (jsdom, user-event, mocked client). Run it; expect failures.
- Implement both dialogs and the ribbon entry points.
- Rerun; expect `5 passed`.
- Run the designRules test and `npm run lint`.

## Notes

Form patterns come from ros2 map/MapsDialog.tsx and poi/PoiPanels.tsx. Spec field rules mirror ClusterSpec (clusters-repository); the server stays the authority.
