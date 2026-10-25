---
title: web webhooks session fields
status: todo
repo: agents-web
value: "the Webhooks events table shows each run's session"
files: [openapi/webhooks.json, openapi/webhooks.source, src/api/webhooks-schema.d.ts, src/webhooks/, src/nomenclature.test.ts]
verify: "npx tsc -b && npx vitest run src/webhooks src/nomenclature.test.ts && npm run check:api && npm run lint"
depends_on: [web-workspace-sessions, webhook-session-columns]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web webhooks session fields

## Requirement

Show the webhook run's session in the Webhooks UI (design D2, D14; contract `webhook-events-session-fields`). Paths are in code/agents-web. Starts after webhook-event-filters merged (gate Q6).

- `npm run sync:api -- webhooks` against the agents-webhook integration tree after webhook-session-columns: `openapi/webhooks.json`, `openapi/webhooks.source`; `npm run gen:api` regenerates `src/api/webhooks-schema.d.ts`.
- `src/webhooks/EventsTable.tsx` (and any other file under `src/webhooks/` reading the run): column "Session" from `session_slug`/`session_id`; texts say session.
- `src/webhooks/WebhooksPage.test.tsx` (test first): the events table shows the Session column and slug.
- `src/nomenclature.test.ts`: guard all of `src/`.

## Acceptance conditions

- AC1: the events table shows each run's session [evidence: test:src/webhooks/WebhooksPage.test.tsx::events show the session]
- AC2: the vendored webhooks openapi matches the generated types [evidence: command:npm run check:api]
- AC3: all of src names the unit session only [evidence: command:npx vitest run src/nomenclature.test.ts]
- AC4: the UI type-checks, the webhooks tests and lint pass [evidence: command:npx tsc -b && npx vitest run src/webhooks && npm run lint]

## Files

- `openapi/webhooks.json`
- `openapi/webhooks.source`
- `src/api/webhooks-schema.d.ts`
- `src/webhooks/`
- `src/nomenclature.test.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
