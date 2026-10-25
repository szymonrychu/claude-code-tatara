---
title: web webhook api client
status: in-progress
repo: agents-web
value: the UI calls the webhook API with types generated from its committed schema
files: [openapi/webhooks.json, openapi/webhooks.source, scripts/sync-api.mjs, scripts/sync-api.test.mjs, package.json, src/api/webhooks-schema.d.ts, src/webhooks/api.ts, src/webhooks/api.test.ts]
verify: "npm ci --no-audit --no-fund && node --test scripts/sync-api.test.mjs && npx vitest run src/webhooks/api.test.ts && npm run check:api && npm run lint"
depends_on: [webhook-openapi-readme]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web webhook api client

## Requirement

Vendor the webhook API and write its client (design D11, D14; contract `agents-web-openapi-vendor`). Paths are in code/agents-web.

- `scripts/sync-api.mjs`: backend id `webhooks` maps to the `agents-webhook` repo (default `--from ../agents-webhook`); `scripts/sync-api.test.mjs` covers it.
- `openapi/webhooks.json` and `openapi/webhooks.source` (`agents-webhook <sha40>`) from `npm run sync:api -- webhooks` against agents-webhook main.
- `package.json`: `gen:api` and `check:api` also generate and check `src/api/webhooks-schema.d.ts` from `openapi/webhooks.json`.
- `src/webhooks/api.ts`: functions over the `webhooks` backend's `basePath` from the runtime config (never an absolute URL): `listEvents({status?, source?, limit?, beforeId?})`, `getEvent(id)`, `listMappings()`, `createMapping(body)`, `deleteMapping(id)`, `getMeta()`; typed from `webhooks-schema.d.ts`; errors surface the backend's `{error: {code, message}}`.
- `src/webhooks/api.test.ts`: each call hits `<basePath>/events...` etc. with the right method, query and body; errors parse.

## Acceptance conditions

- AC1: sync-api knows the webhooks backend [evidence: command:node --test scripts/sync-api.test.mjs]
- AC2: the vendored schema matches the generated types [evidence: command:npm run check:api]
- AC3: every client call uses the configured relative base path, method, query and body [evidence: command:npx vitest run src/webhooks/api.test.ts]
- AC4: types and lint pass [evidence: command:npx tsc -b && npm run lint]

## Files

- `openapi/webhooks.json`
- `openapi/webhooks.source`
- `scripts/sync-api.mjs`
- `scripts/sync-api.test.mjs`
- `package.json`
- `src/api/webhooks-schema.d.ts`
- `src/webhooks/api.ts`
- `src/webhooks/api.test.ts`

## Interfaces

- Owns `web-webhook-client`: `src/webhooks/api.ts`. Uses `webhook-api` (agents-webhook `openapi.json`).

## Expected outcome

The UI has a typed webhook client pinned to a recorded agents-webhook commit.

## Steps

- Red: `api.test.ts` and the sync-api case; run: fail.
- Green: script mapping, `npm run sync:api -- webhooks`, client; run the verify command.

## Notes

- Requires `code/agents-webhook` checked out next to `code/agents-web` with this epic's API merged to its main.
