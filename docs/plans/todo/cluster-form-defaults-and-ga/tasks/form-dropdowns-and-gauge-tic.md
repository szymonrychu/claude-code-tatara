---
title: form dropdowns and gauge tick
status: todo
repo: agent-orchestrator
value: "the form shows what a cluster will get, and the gauge tick sits on the ring"
files: [frontend/src/clusters/ClusterForm.tsx, frontend/src/clusters/ClusterForm.test.tsx, frontend/src/clusters/formModel.ts, frontend/src/ribbon/ContextGauge.tsx, frontend/src/ribbon/ContextGauge.test.tsx]
verify: "cd frontend && npx vitest run src/clusters src/ribbon && npm run lint"
depends_on: [meta-form-defaults]
owns: []
uses: []
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

# form dropdowns and gauge tick

## Requirement

ClusterForm (frontend/src/clusters/ClusterForm.tsx): Model and Effort are select dropdowns fed by /meta models and efforts (Effort includes an empty 'model default' entry; an edited cluster whose value is not in the list keeps it as an extra option). Every other field is prefilled from /meta defaults exactly the way Max attempts is (blankValues(meta)), including cpu/memory requests and limits, workdir, any-mcp config and the auto-compact percent. ContextGauge (frontend/src/ribbon/ContextGauge.tsx): the auto-compact tick is a short radial mark lying on the ring at autoCompactPct (rotated about the gauge centre, inside the gauge box), not a skewed bar outside the circle; pin its geometry in the test. Theme tokens only (designRules test stays green).

## Acceptance conditions

- AC1: Model and Effort render as selects with the /meta options [evidence: command:cd frontend && npx vitest run src/clusters/ClusterForm.test.tsx]
- AC2: create mode prefills every field from /meta defaults [evidence: command:cd frontend && npx vitest run src/clusters/ClusterForm.test.tsx]
- AC3: the gauge tick is a radial mark on the ring at the auto-compact percent [evidence: command:cd frontend && npx vitest run src/ribbon]
- AC4: frontend lint, tests and build pass [evidence: command:cd frontend && npm run lint && npm test && npm run build && npm run check:api]

## Files

- `frontend/src/clusters/ClusterForm.tsx`
- `frontend/src/clusters/ClusterForm.test.tsx`
- `frontend/src/clusters/formModel.ts`
- `frontend/src/ribbon/ContextGauge.tsx`
- `frontend/src/ribbon/ContextGauge.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
