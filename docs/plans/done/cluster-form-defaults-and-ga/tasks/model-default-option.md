---
title: model default option
status: done
repo: agent-orchestrator
value: editing a cluster with no model shows its real value
files: [frontend/src/clusters/ClusterForm.tsx, frontend/src/clusters/ClusterForm.test.tsx]
verify: "cd frontend && npx vitest run src/clusters && npm run lint"
depends_on: [form-dropdowns-and-gauge-tic]
model: sonnet
review: ""
verified_head: 34631bdb6477cad78277a8766ef29d9dd5376f2e
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# model default option

## Requirement

ClusterForm.tsx: the Model select gets an empty "default" option like Effort, so an edited cluster with a null model shows that option instead of a blank select; the create form still preselects meta.defaults.model.

## Acceptance conditions

- AC1: Model select offers an empty default option and an edited cluster with a null model shows it [evidence: command:cd frontend && npx vitest run src/clusters/ClusterForm.test.tsx]

## Files

- `frontend/src/clusters/ClusterForm.tsx`
- `frontend/src/clusters/ClusterForm.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The Model select lists a default (empty) option followed by meta.models; null model in edit mode selects it.

## Steps

- Add the AC1 test, run `cd frontend && npx vitest run src/clusters/ClusterForm.test.tsx`: it fails.
- Add the empty option to the Model select, reuse the Effort select's pattern; rerun: passes; `npm run lint` clean.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
