---
title: web matrix api client
status: done
repo: agents-web
value: the UI calls the connector API with types generated from its committed schema
files: [openapi/matrix.json, openapi/matrix.source, scripts/sync-api.mjs, scripts/sync-api.test.mjs, package.json, src/api/matrix-schema.d.ts, src/matrix/api.ts, src/matrix/api.test.ts]
verify: "npm ci --no-audit --no-fund && node --test scripts/sync-api.test.mjs && npx vitest run src/matrix/api.test.ts && npm run check:api && npm run lint"
depends_on: []
model: sonnet
review: ""
verified_head: e679002beb6fb5e1d769896760d972ffa00f11a2
points: 3
expected_minutes: 7
expected_tokens: 907602
points_actual: 3
actual_minutes: 4
actual_tokens: 460985
actual_roles: "impl 3, review 1"
actual_role_tokens: "impl 366214, review 94771"
---

# web matrix api client

## Requirement

Vendor the connector API and write its client (design D11, D12; contract `agents-web-openapi-vendor`). Paths are in code/agents-web.

- `scripts/sync-api.mjs`: backend id `matrix` maps to the `agents-matrix-connector` repo (default `--from ../agents-matrix-connector`); `scripts/sync-api.test.mjs` covers it.
- `openapi/matrix.json` and `openapi/matrix.source` (`agents-matrix-connector <sha40>`) from `npm run sync:api -- matrix` against the agents-matrix-connector checkout of this epic.
- `package.json`: `gen:api` and `check:api` also generate and check `src/api/matrix-schema.d.ts` from `openapi/matrix.json`.
- `src/matrix/api.ts`: functions over the `matrix` backend's `basePath` from the runtime config (never an absolute URL), typed from `matrix-schema.d.ts`: `getMeta()`, `listRooms({kind?, access?})`, `getRoom(roomId)`, `setRoomSettings(roomId, {preset_id, trigger})`, `listRoomMessages(roomId, {limit?, beforeId?})`, `listUsers({q?, limit?})`, `listRules()`, `addRule({list, kind, value, note?})`, `deleteRule(id)`, `getSettings()`, `setSettings({default_preset_id})`, `listMessages({status?, roomId?, limit?, beforeId?})`; room ids are URL-encoded in paths; errors surface the backend's `{error: {code, message}}`.
- `src/matrix/api.test.ts`: each call hits the right method, path (encoded room id), query and body; errors parse.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: sync-api maps the matrix backend to the agents-matrix-connector repo [evidence: command:node --test scripts/sync-api.test.mjs]
- AC2: every client call hits the matrix basePath with the right method, encoded path, query and body [evidence: command:npx vitest run src/matrix/api.test.ts -t "calls the matrix API under the configured basePath"]
- AC3: backend errors surface their code and message [evidence: command:npx vitest run src/matrix/api.test.ts -t "surfaces backend error codes"]
- AC4: the generated schema matches the vendored openapi and lint passes [evidence: command:npm run check:api && npm run lint]

## Files

- `openapi/matrix.json`
- `openapi/matrix.source`
- `scripts/sync-api.mjs`
- `scripts/sync-api.test.mjs`
- `package.json`
- `src/api/matrix-schema.d.ts`
- `src/matrix/api.ts`
- `src/matrix/api.test.ts`

## Interfaces

- `src/matrix/api.ts` (used by web-chats-rooms-page and web-chats-access-panels); `openapi/matrix.json` vendored from contract `matrix-connector-api`.

## Expected outcome

The UI can call every connector route with generated types.

## Steps

- Red: extend `scripts/sync-api.test.mjs`; write `src/matrix/api.test.ts` (describe/it names as in the ACs). Both fail.
- Green: map the backend, vendor the schema, generate types, write `api.ts`. Run the verify.

## Notes

- Same shape as agents-webhook-microservice task web-webhook-api-client and `src/webhooks/api.ts`.
- 2026-10-25 split: depends_on mxc-openapi-and-readme live in epic agents-matrix-connector; that epic is a blocker of this one, so they are done before this task runs.

- 2026-10-26 done
