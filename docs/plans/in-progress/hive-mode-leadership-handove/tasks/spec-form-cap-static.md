---
title: spec form cap static
status: in-progress
repo: agent-orchestrator
value: users set the replica cap and the static switch in the preset and cluster forms
files: [frontend/src/clusters/clusterSpecForm.ts, frontend/src/presets/PresetForm.tsx, frontend/src/presets/PresetForm.test.tsx]
verify: "cd frontend && npx vitest run src/presets/PresetForm.test.tsx src/clusters/NewClusterDialog.test.tsx && npm run lint"
depends_on: [spec-cap-static]
owns: []
uses: [orch-spec-cap-static]
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

# spec form cap static

## Requirement

UI for the spec fields owned by this epic (S2, S3, X2 parity: the fields are already settable through the API). In the preset editor and the new-cluster dialog (`clusters/clusterSpecForm.ts`, `presets/PresetForm.tsx`):

- "Max replicas" number input: 1..`meta.caps.max_replicas`, at least replicas, empty means "same as replicas" and stays unset in the sparse spec unless edited; helper text "More than 1 makes the cluster a hive".
- "Static (scaling disabled)" switch mapping to `spec.static`; inline error when static and max replicas differs from replicas.
- Both map to `spec.max_replicas` and `spec.static` and are part of `SetKey`.

## Acceptance conditions

- AC1: max replicas renders, validates its bounds and maps to spec.max_replicas only when set [evidence: command:cd frontend && npx vitest run src/presets/PresetForm.test.tsx -t "max replicas"]
- AC2: the static switch maps to spec.static and shows the inline error when max replicas differs from replicas [evidence: command:cd frontend && npx vitest run src/presets/PresetForm.test.tsx -t "static"]
- AC3: the new-cluster dialog tests, lint and build pass [evidence: command:cd frontend && npx vitest run src/clusters/NewClusterDialog.test.tsx && npm run lint && npm run build]

## Files

- `frontend/src/clusters/clusterSpecForm.ts`
- `frontend/src/presets/PresetForm.tsx`
- `frontend/src/presets/PresetForm.test.tsx`

## Interfaces

- Uses `ClusterSpec.max_replicas` and `static` through `frontend/src/api/schema.d.ts`.

## Expected outcome

The preset editor and the new-cluster dialog set the cap and the static switch.

## Steps

- Red: add the "max replicas" and "static" cases to `PresetForm.test.tsx`; run `cd frontend && npx vitest run src/presets/PresetForm.test.tsx`: fails.
- Green: extend `FormValues`, `SetKey`, validation and the form; run the verify command: passes.

## Notes

- `clusterSpecForm.ts` holds form state and the sparse mapping; `PresetForm.tsx:133` renders replicas.
