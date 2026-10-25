---
title: web create endpoint filters
status: in-progress
repo: agents-web
value: filters are set when creating an endpoint and the example preview says whether it passes
files: [src/webhooks/CreateEndpointDialog.tsx, src/webhooks/samples.ts, src/webhooks/Endpoints.test.tsx, src/webhooks/WebhooksPage.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/webhooks/Endpoints.test.tsx src/webhooks/WebhooksPage.test.tsx && npx tsc -b && npm run lint"
depends_on: [web-filters-editor]
model: sonnet
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

# web create endpoint filters

## Requirement

Set filters when creating an endpoint and check them in the example-JSON preview (design D8). User decision, verbatim: "Configurable in the endpoints API and the agents-web Webhooks UI, including in the existing example-JSON preview flow if cheap: show whether the example passes the filters." Paths are in code/agents-web.

- `src/webhooks/CreateEndpointDialog.tsx`: embeds `FiltersEditor` below the prompt template, its `fields` from `getMeta().filter_fields[type]` (fetched once when the dialog opens); a type change passes the new type and fields (the editor drops inapplicable rules). The create body carries `filters` when any rule exists.
- Preview: the button is enabled when the template is non-empty or any rule exists; it sends `template` only when non-empty and `filters` only when a rule exists. The result shows the rendered prompt when one was returned, and for `filters` either "Passes the filters" or "Ignored: <reason>" (the backend's reason text). A 422 shows through `FormError` as today.
- `src/webhooks/samples.ts`: the PR/MR samples carry branches (GitHub `head.ref`/`base.ref`, GitLab `source_branch`/`target_branch`) and every forge sample carries one label, the Grafana sample `commonLabels` with `env` and `severity`, so the preview exercises the D3 fields.

## Acceptance conditions

- AC1: creating with a deny rule sends filters in the POST body; creating without rules sends no filters key [evidence: command:npx vitest run src/webhooks/Endpoints.test.tsx -t "sends filters on create"]
- AC2: the editor offers the fields of meta.filter_fields for the chosen type [evidence: command:npx vitest run src/webhooks/Endpoints.test.tsx -t "offers the meta fields of the type"]
- AC3: preview with rules and no template sends filters without template and shows Ignored with the reason [evidence: command:npx vitest run src/webhooks/Endpoints.test.tsx -t "previews filters without a template"]
- AC4: preview of a passing example shows Passes the filters next to the rendered prompt [evidence: command:npx vitest run src/webhooks/Endpoints.test.tsx -t "shows passes the filters"]
- AC5: the PR/MR samples carry branches and every sample carries labels [evidence: command:grep -q 'head' src/webhooks/samples.ts && grep -q 'source_branch' src/webhooks/samples.ts && grep -q 'commonLabels' src/webhooks/samples.ts]
- AC6: the endpoints tests, type check and lint pass [evidence: command:npx vitest run src/webhooks/Endpoints.test.tsx src/webhooks/WebhooksPage.test.tsx && npx tsc -b && npm run lint]

## Files

- `src/webhooks/CreateEndpointDialog.tsx`
- `src/webhooks/samples.ts`
- `src/webhooks/Endpoints.test.tsx`
- `src/webhooks/WebhooksPage.test.tsx`

## Interfaces

- Uses `FiltersEditor`, `EMPTY_FILTERS` (web-filters-editor), `getMeta`, `createEndpoint`, `previewTemplate` (web-vendor-filters-api). `CreateEndpointDialogProps` unchanged.

## Expected outcome

The New endpoint dialog sets allow and deny rules, and Preview answers whether the example JSON passes them, with or without a template.

## Steps

- Red: add the four tests to `src/webhooks/Endpoints.test.tsx` (its fetch mock gains `GET /meta` with `filter_fields`). Run `npx vitest run src/webhooks/Endpoints.test.tsx`: they fail (no editor, preview disabled without a template).
- Green: the dialog and samples changes. Run the verify: all pass, including the existing create, error and credentials tests.

## Notes

- Existing tests that preview a template keep passing: the request still carries `template`, and `filters` is omitted when there are no rules.
- `WebhooksPage.test.tsx` renders the dialog through the page; its fetch mock may need the `/meta` route too.
