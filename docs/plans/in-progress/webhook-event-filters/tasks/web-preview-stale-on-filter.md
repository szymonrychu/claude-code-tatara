---
title: web preview stale on filter edit
status: todo
repo: agents-web
value: the create dialog never shows a stale filter verdict
files: [src/webhooks/CreateEndpointDialog.tsx, src/webhooks/Endpoints.test.tsx]
verify: "npx vitest run src/webhooks/Endpoints.test.tsx && npx tsc -b && npm run lint"
depends_on: []
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 689196
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web preview stale on filter edit

## Requirement

Epic whole-diff review 2026-10-25 (medium, /Users/szymonri/Documents/claude-code-tatara/.scratchpad/wef-epic-review.md): in agents-web src/webhooks/CreateEndpointDialog.tsx the FiltersEditor is wired as `onChange={setFilters}`, so editing a rule does not clear the preview's `filterResult` or `rendered`. Template edits do clear them, and so does FiltersDialog's edit. After a Preview shows "Passes the filters", changing a deny rule so it would match leaves the stale green verdict until Preview is pressed again, so the user can create the endpoint believing it. Fix: any filter change clears the preview result and the rendered prompt, the same way a template edit does. Add a test: preview passes, a rule is edited, and the verdict and the rendered prompt are gone.

## Acceptance conditions

- AC1: editing a filter rule clears the create dialog's preview verdict and rendered prompt [evidence: test:src/webhooks/Endpoints.test.tsx::clears the preview result when a filter rule changes]
- AC2: the suite, typecheck and lint pass [evidence: command:npx vitest run && npx tsc -b && npm run lint]

## Files

- `src/webhooks/CreateEndpointDialog.tsx`
- `src/webhooks/Endpoints.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
