---
title: web schedules api client
status: in-progress
repo: agents-web
value: the UI talks to the schedule API with generated types through one client module
files: [openapi/schedules.json, openapi/schedules.source, scripts/sync-api.mjs, scripts/sync-api.test.mjs, package.json, src/api/schedules-schema.d.ts, src/schedules/api.ts, src/schedules/api.test.ts]
verify: "npm ci --no-audit --no-fund && node --test scripts/sync-api.test.mjs && npx vitest run src/schedules/api.test.ts && npm run check:api && npm run lint"
depends_on: []
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 678580
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web schedules api client

## Requirement

Add the schedule API client in agents-web (design D12; approval A4), following the frontend-decoupling contracts `agents-web-openapi-vendor` (vendored `openapi/<id>.json` plus `openapi/<id>.source` `<repo> <sha40>`, `npm run sync:api -- <backend-id> [--from <checkout>]`) and `agents-web-backends-config` (runtime `config.json` backends `{id, label, basePath}`, `src/config/backends.ts:backendBase(id)`, `isConfigured(id)`).

- `scripts/sync-api.mjs` maps backend id `schedules` to the `agents-schedule` repo (default `--from ../agents-schedule`); `scripts/sync-api.test.mjs` covers it.
- Run `npm run sync:api -- schedules` to vendor `openapi/schedules.json` and `openapi/schedules.source`; `package.json` `gen:api` and `check:api` also generate and check `src/api/schedules-schema.d.ts` from it.
- `src/schedules/api.ts`: base path `backendBase('schedules')` at call time (relative URL, never absolute); `listSchedules`, `getSchedule`, `createSchedule`, `updateSchedule`, `deleteSchedule`, `previewSchedule`, `runScheduleNow`, `listScheduleRuns`, `listRuns`, `getRun`; errors surface `{code, message}` from the error envelope; `schedulesEnabled()` is `isConfigured('schedules')`.

## Acceptance conditions

- AC1: every client function calls the documented method and relative path under the configured base [evidence: command:npx vitest run src/schedules/api.test.ts -t 'routes']
- AC2: API errors surface code and message [evidence: command:npx vitest run src/schedules/api.test.ts -t 'errors']
- AC3: without a schedules backend the client reports disabled [evidence: command:npx vitest run src/schedules/api.test.ts -t 'disabled']
- AC4: sync:api knows the schedules backend [evidence: command:node --test scripts/sync-api.test.mjs]
- AC5: the vendored schema, its source line and the generated types agree [evidence: command:npm run check:api && grep -Eq '^agents-schedule [0-9a-f]{40}$' openapi/schedules.source]

## Files

- `openapi/schedules.json`
- `openapi/schedules.source`
- `scripts/sync-api.mjs`
- `scripts/sync-api.test.mjs`
- `package.json`
- `src/api/schedules-schema.d.ts`
- `src/schedules/api.ts`
- `src/schedules/api.test.ts`

## Interfaces

- `src/schedules/api.ts` exports above, typed from `src/api/schedules-schema.d.ts` (part `web-schedules-client`).

## Expected outcome

The UI has a typed client for every schedule route, configured at runtime.

## Steps

- Write src/schedules/api.test.ts and the sync-api case; both fail.
- Extend sync-api.mjs, run `npm run sync:api -- schedules --from ../agents-schedule`, write api.ts; the tests pass.
- `npm run lint` and `npm run check:api` clean.

## Notes

- Layout per agents-webhook's `src/webhooks/api.ts` (contract `web-webhook-client`): one folder per backend.
- No CORS: the API is same-origin under its path prefix.
- Split 2026-10-25: depends_on `api-docs-and-openapi` stays satisfied by the epic blocker agents-schedule-microservice, which owns that task.
