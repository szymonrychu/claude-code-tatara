---
title: web vendor filters api
status: todo
repo: agents-web
value: "the UI has typed access to endpoint filters, their replacement and the filter preview"
files: [openapi/webhooks.json, openapi/webhooks.source, src/api/webhooks-schema.d.ts, src/webhooks/api.ts, src/webhooks/api.test.ts]
verify: "npm ci --no-audit --no-fund && npx vitest run src/webhooks/api.test.ts && npm run check:api && npx tsc -b && npm run lint"
depends_on: [api-endpoint-filters]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 9
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web vendor filters api

## Requirement

Vendor the extended webhook API into agents-web and expose it in the typed client (design D6, D8). User decision: "Configurable in the endpoints API and the agents-web Webhooks UI". Paths are in code/agents-web.

- `npm run sync:api -- webhooks --from ../agents-webhook` (the sibling agents-webhook checkout of this epic's integration tree, at the commit of api-endpoint-filters or later, with `openapi.json` committed): updates `openapi/webhooks.json`, `openapi/webhooks.source` and `src/api/webhooks-schema.d.ts`. No hand edits to the vendored files.
- `src/webhooks/api.ts`: exports types `Filters`, `FilterRule`, `FilterResult` from the schema, and `setEndpointFilters(endpointId: string, filters: Filters)` -> `PUT /endpoints/{id}/filters` returning `EndpointView`, the id URL-encoded like the other calls. `previewTemplate` keeps its name and now takes the optional `template` and `filters`.

## Acceptance conditions

- AC1: setEndpointFilters sends PUT /webhooks/api/v1/endpoints/<encoded id>/filters with the filters as the JSON body [evidence: command:npx vitest run src/webhooks/api.test.ts -t "replaces endpoint filters"]
- AC2: previewTemplate sends filters without a template [evidence: command:npx vitest run src/webhooks/api.test.ts -t "previews filters without a template"]
- AC3: the vendored document and generated types match agents-webhook's openapi.json and carry the filters route [evidence: command:npm run check:api && grep -q '/webhooks/api/v1/endpoints/{id}/filters' openapi/webhooks.json && grep -q 'agents-webhook ' openapi/webhooks.source]
- AC4: the api tests, type check and lint pass [evidence: command:npx vitest run src/webhooks/api.test.ts && npx tsc -b && npm run lint]

## Files

- `openapi/webhooks.json`
- `openapi/webhooks.source`
- `src/api/webhooks-schema.d.ts`
- `src/webhooks/api.ts`
- `src/webhooks/api.test.ts`

## Interfaces

- Contract `web-webhook-client` (`src/webhooks/api.ts`): adds `Filters`, `FilterRule`, `FilterResult`, `setEndpointFilters`; `EndpointView.filters`, `WebhookMeta.filter_fields`, `PreviewIn`/`PreviewOut` follow the schema. Consumed by web-filters-editor, web-create-endpoint-filters, web-edit-endpoint-filters.
- Consumes contract `webhook-api` (api-endpoint-filters) through `openapi/webhooks.json`.

## Expected outcome

The UI code can read and write endpoint filters and preview them with full types.

## Steps

- Run `npm ci --no-audit --no-fund`, then `npm run sync:api -- webhooks --from ../agents-webhook`; expect the three vendored files to change.
- Red: add the two tests to `src/webhooks/api.test.ts`; run `npx vitest run src/webhooks/api.test.ts`: they fail on the missing export.
- Green: the exports in `api.ts`. Run the verify: all pass.

## Notes

- `sync-api.mjs` refuses when the source `openapi.json` has uncommitted changes; the agents-webhook commit of api-endpoint-filters is already in the tree.
- Existing callers of `previewTemplate` (CreateEndpointDialog) still type-check because `template` stays accepted; their behaviour changes in web-create-endpoint-filters.
