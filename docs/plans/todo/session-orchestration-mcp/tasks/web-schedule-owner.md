---
title: web schedule owner
status: todo
repo: agents-web
value: the user sees which session created a schedule
files: [openapi/schedules.json, openapi/schedules.source, src/api/schedules-schema.d.ts, src/schedules/SchedulesPage.tsx, src/schedules/SchedulesPage.test.tsx]
verify: "npx vitest run src/schedules && npm run lint"
depends_on: [sched-schedule-owner, web-created-by]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web schedule owner

## Requirement

README Goal G6, verbatim: "agents-web has the \"Session orchestration\" switch on the preset form (sessions take the flag from their preset), and shows \"created by <slug>\" on sessions, presets and schedules."

Open question Q7 (pending; the plan follows the recommended answer), verbatim: "agents-web shows 'created by <slug>' on sessions, presets and schedules?" recommended "yes".

Design D7, verbatim: "The UI API is unchanged except the schedule view gains `owner_slug` (additive)".

Needs a merged upstream: agents-schedule main carrying sched-schedule-owner.

Scope (agents-web): `openapi/schedules.json` and `openapi/schedules.source` (`npm run sync:api -- schedules`), `src/api/schedules-schema.d.ts`, `src/schedules/SchedulesPage.tsx` ("created by <slug>" for owned schedules), `src/schedules/SchedulesPage.test.tsx`.

## Acceptance conditions

- ac1: the schedules list shows "created by <slug>" on a schedule with owner_slug and nothing on one without [evidence: command:npx vitest run src/schedules/SchedulesPage.test.tsx -t "created by"]
- ac2: the vendored schedules OpenAPI document and the generated types match, schedules.source names an agents-schedule main commit, and the document carries owner_slug [evidence: command:npm run check:api && grep -q '^agents-schedule [0-9a-f]\{40\}$' openapi/schedules.source && grep -q owner_slug openapi/schedules.json]
- ac3: the schedules tests and lint pass [evidence: command:npx vitest run src/schedules && npm run lint]

## Files

- `openapi/schedules.json`
- `openapi/schedules.source`
- `src/api/schedules-schema.d.ts`
- `src/schedules/SchedulesPage.tsx`
- `src/schedules/SchedulesPage.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
