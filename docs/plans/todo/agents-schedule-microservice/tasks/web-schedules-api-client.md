---
title: web schedules api client
status: todo
repo: agents-web
value: the UI talks to the schedule API with generated types through one client module
files: [openapi/agents-schedule.json, src/api/scheduleSchema.d.ts, src/api/schedules.ts, src/api/schedules.test.ts, package.json]
verify: "npx vitest run src/api/schedules.test.ts && npm run lint && npm run check:api"
depends_on: [api-docs-and-openapi]
owns: [web-schedules-client]
uses: [agents-schedule-api, web-backends-config, web-openapi-vendoring]
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

# web schedules api client

## Requirement

Add the schedule API client in agents-web (design D12; approval A4), following the frontend-decoupling contracts `web-openapi-vendoring` (vendored `openapi/<service>.json` recording its source commit, `gen:api` and `check:api` per backend) and `web-backends-config` (runtime `config.json` backends `{id, label, basePath, ...}`).

- Vendor `code/agents-schedule/openapi.json` as `openapi/agents-schedule.json` with its source commit; generate `src/api/scheduleSchema.d.ts` with openapi-typescript; extend `gen:api`/`check:api` in package.json.
- `src/api/schedules.ts`: base path from the `schedules` backend entry of `config.json` (relative URL, never absolute); `listSchedules`, `getSchedule`, `createSchedule`, `updateSchedule`, `deleteSchedule`, `previewSchedule`, `runScheduleNow`, `listScheduleRuns`, `listRuns`, `getRun`; errors surface `{code, message}` from the error envelope.
- `schedulesEnabled()` is false when config.json has no `schedules` backend.

## Acceptance conditions

- AC1: every client function calls the documented method and relative path under the configured base [evidence: command:npx vitest run src/api/schedules.test.ts -t 'routes']
- AC2: API errors surface code and message [evidence: command:npx vitest run src/api/schedules.test.ts -t 'errors']
- AC3: without a schedules backend the client reports disabled [evidence: command:npx vitest run src/api/schedules.test.ts -t 'disabled']
- AC4: the vendored schema and generated types agree [evidence: command:npm run check:api]

## Files

- `openapi/agents-schedule.json`
- `src/api/scheduleSchema.d.ts`
- `src/api/schedules.ts`
- `src/api/schedules.test.ts`
- `package.json`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
