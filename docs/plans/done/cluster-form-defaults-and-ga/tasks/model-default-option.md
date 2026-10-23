---
title: model default option
status: done
repo: agent-orchestrator
value: editing a cluster with no model shows its real value
files: [frontend/src/clusters/ClusterForm.tsx, frontend/src/clusters/ClusterForm.test.tsx]
verify: "cd frontend && npx vitest run src/clusters && npm run lint"
depends_on: [form-dropdowns-and-gauge-tic]
owns: []
uses: []
model: sonnet
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/cluster-form-defaults-and-ga-model-default-option/agent-orchestrator
branch: cluster-form-defaults-and-ga-model-default-option
verified_head: 34631bdb6477cad78277a8766ef29d9dd5376f2e
run: cluster-form-defaults-and-ga
provides: []
acs_for_audit: []
process_gaps: []
fork_point: c993d7c1e48faa40a81d4f87d79ee0836a479ea7
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
