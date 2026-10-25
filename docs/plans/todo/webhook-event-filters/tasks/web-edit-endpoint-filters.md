---
title: web edit endpoint filters
status: todo
repo: agents-web
value: "an existing endpoint's filters change without recreating it, checked against an example first"
files: [src/webhooks/FiltersDialog.tsx, src/webhooks/FiltersDialog.test.tsx, src/webhooks/EndpointsList.tsx, src/webhooks/Endpoints.test.tsx, MEMORY.md]
verify: "npm ci --no-audit --no-fund && npx vitest run src/webhooks/FiltersDialog.test.tsx src/webhooks/Endpoints.test.tsx && npx tsc -b && npm run lint"
depends_on: [web-filters-editor, web-create-endpoint-filters]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web edit endpoint filters

## Requirement

Edit an existing endpoint's filters from the endpoints list (design D6, D8). User decision: "Configurable in the endpoints API and the agents-web Webhooks UI, including in the existing example-JSON preview flow if cheap: show whether the example passes the filters." Paths are in code/agents-web.

- `src/webhooks/EndpointsList.tsx`: each row gets a "Filters (n)" button (n = allow plus deny rules) before Rotate credentials; it opens `FiltersDialog` for that endpoint.
- New `src/webhooks/FiltersDialog.tsx`, `FiltersDialog({endpoint, fields, open, onClose, onSaved})`: `FiltersEditor` prefilled from `endpoint.filters`; an Example JSON field prefilled with `sampleFor(endpoint.type)` and a Check button that calls the preview with `type`, `example` and `filters` only and shows "Passes the filters" or "Ignored: <reason>"; Save calls `setEndpointFilters` and on success calls `onSaved` (the list refreshes) and closes; a 422 shows its message through `FormError` and keeps the dialog open; Cancel discards.
- The list gets `fields` from `getMeta().filter_fields`.
- `MEMORY.md`: a dated line: endpoint filters are edited in a dialog from the endpoints list through `PUT /endpoints/{id}/filters`; the field catalogue comes from `GET /meta` and the UI never validates RE2 patterns itself; why.

## Acceptance conditions

- AC1: each endpoint row shows Filters with its rule count and opens the dialog prefilled with the endpoint's rules [evidence: command:npx vitest run src/webhooks/FiltersDialog.test.tsx -t "opens prefilled from the list"]
- AC2: Save sends PUT /endpoints/<id>/filters with the edited rules, closes and refreshes the list [evidence: command:npx vitest run src/webhooks/FiltersDialog.test.tsx -t "saves and refreshes"]
- AC3: a 422 answer shows its message and keeps the dialog open [evidence: command:npx vitest run src/webhooks/FiltersDialog.test.tsx -t "shows the backend error"]
- AC4: Check previews the example with the filters only and shows Ignored with the reason [evidence: command:npx vitest run src/webhooks/FiltersDialog.test.tsx -t "checks the example"]
- AC5: Cancel sends nothing [evidence: command:npx vitest run src/webhooks/FiltersDialog.test.tsx -t "cancel sends nothing"]
- AC6: MEMORY.md records the edit flow and why [evidence: command:grep -q 'filters' MEMORY.md && grep -q 'PUT' MEMORY.md]
- AC7: the dialog and endpoints tests, type check and lint pass [evidence: command:npx vitest run src/webhooks/FiltersDialog.test.tsx src/webhooks/Endpoints.test.tsx && npx tsc -b && npm run lint]

## Files

- `src/webhooks/FiltersDialog.tsx`
- `src/webhooks/FiltersDialog.test.tsx`
- `src/webhooks/EndpointsList.tsx`
- `src/webhooks/Endpoints.test.tsx`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
