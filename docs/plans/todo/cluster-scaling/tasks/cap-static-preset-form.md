---
title: cap static preset form
status: todo
repo: agent-orchestrator
value: users set the agent cap and the static switch when they define a cluster
files: [frontend/src/clusters/clusterSpecForm.ts, frontend/src/presets/PresetForm.tsx, frontend/src/presets/PresetForm.test.tsx]
verify: "cd frontend && npx vitest run src/presets/PresetForm.test.tsx && npm run lint"
depends_on: []
owns: []
uses: []
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

# cap static preset form

## Requirement

Set the cap and the static switch at init in the preset form (design D5; user S2, S3, Q7, X2). In `frontend/src/clusters/clusterSpecForm.ts` add `maxReplicas` (string) and `static` (boolean) to the form values and `'maxReplicas' | 'static'` to `SetKey`; `stateFromPreset` reads `spec.max_replicas` and `spec.static`; `validate` requires `maxReplicas`, when set, to be an integer from the replicas value (or 1) up to `meta.caps.max_replicas` ("Max agents"), and `static` with a set `maxReplicas` different from replicas is an error; `toPresetSpec` emits `max_replicas` and `static` only when the user set them (presets keep only set fields). In `frontend/src/presets/PresetForm.tsx` render a "Max agents" number field and a "Static (no scaling)" switch; turning static on sets Max agents to the replicas value and disables it. Helper text: "Max agents 1 means one agent with no hive tools; a static cluster cannot be scaled; static with one agent is alone." Clusters scheduled from the preset snapshot these fields (existing create-from-preset path).

## Acceptance conditions

- AC1: Max agents and Static are saved into the preset spec as max_replicas and static only when set [evidence: command:cd frontend && npx vitest run src/presets/PresetForm.test.tsx -t "max agents and static"]
- AC2: Max agents below replicas or above caps.max_replicas, and static with Max agents different from replicas, show validation errors and block saving [evidence: command:cd frontend && npx vitest run src/presets/PresetForm.test.tsx -t "cap validation"]
- AC3: turning static on sets Max agents to replicas and disables the field [evidence: command:cd frontend && npx vitest run src/presets/PresetForm.test.tsx -t "static locks cap"]
- AC4: lint and typecheck build pass [evidence: command:cd frontend && npm run lint && npm run build]

## Files

- `frontend/src/clusters/clusterSpecForm.ts`
- `frontend/src/presets/PresetForm.tsx`
- `frontend/src/presets/PresetForm.test.tsx`

## Interfaces

- Consumes `ClusterSpec.max_replicas` and `static` (hive F3) through `schema.d.ts`, and `Meta.caps.max_replicas`.
- `clusterSpecForm.ts` `FormValues`, `SetKey`, `stateFromPreset`, `validate`, `toPresetSpec` gain the two fields.

## Expected outcome

A preset can define a hive cap and a static cluster, and clusters scheduled from it get those values.

## Steps

- Red: add the three cases to `frontend/src/presets/PresetForm.test.tsx`; run `cd frontend && npx vitest run src/presets/PresetForm.test.tsx -t "max agents"`: fails.
- Green: extend the form model and render the field and switch; run the verify command and `npm run build`.

## Notes

- agent-init-scripts also adds a field to these two files; whichever epic lands second rebases onto the other.
- Keep the existing `num()` helper pattern for the number field.
