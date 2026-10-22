---
title: fe cluster form
status: todo
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
worktree: ""
branch: ""
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
- max attempts, auto-compact percent, CPU and memory requests and limits

Submit calls `createCluster` or `patchCluster` and shows server 409 and 422 messages at the field or in an Alert.

`DiscardClusterDialog.tsx`:
- Built on ConfirmDialog.
- States that the workspace PVC and its files are deleted.
- Requires typing the slug to enable Discard.
- Offers `Also delete history`, which purges once the cluster is deleted.
- Calls `deleteCluster`.

The Ribbon header gains a `New cluster` button. ClusterRow gains a menu with Edit and Discard.

## Acceptance conditions

- AC1: creating a cluster posts the full spec [evidence: test:frontend/src/clusters/ClusterForm.test.tsx::creates cluster with full spec]
- AC2: invalid slug and secret env keys are rejected inline [evidence: test:frontend/src/clusters/ClusterForm.test.tsx::validates slug and env keys]
- AC3: editing patches the spec with slug and PVC size locked [evidence: test:frontend/src/clusters/ClusterForm.test.tsx::edit patches spec]
- AC4: server 409 and 422 errors are shown [evidence: test:frontend/src/clusters/ClusterForm.test.tsx::shows server errors]
- AC5: discard requires the typed slug and names the PVC deletion [evidence: test:frontend/src/clusters/ClusterForm.test.tsx::discard requires typed slug]
- AC6: design rules still hold [evidence: test:frontend/src/layout/designRules.test.ts::source files follow the design rules]

## Files

- `frontend/src/clusters/ClusterForm.tsx`
- `frontend/src/clusters/DiscardClusterDialog.tsx`
- `frontend/src/ribbon/Ribbon.tsx`
- `frontend/src/ribbon/ClusterRow.tsx`
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
