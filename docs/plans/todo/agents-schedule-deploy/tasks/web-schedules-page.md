---
title: web schedules page
status: todo
repo: agents-web
value: "a user manages every schedule from one page: enable, disable, run now, edit, delete"
files: [src/schedules/SchedulesPage.tsx, src/schedules/SchedulesPage.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/schedules/SchedulesPage.test.tsx && npm run lint"
depends_on: [web-schedule-form, web-schedule-runs-list]
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

# web schedules page

## Requirement

Add `SchedulesPage` (design D12; approvals A2, A4, gate Q6): a list of schedules (name, cron, timezone, preset name, next fire time, last run status) with per-row controls: enable/disable toggle (PUT with `enabled` flipped), Run now (POST run; the new run appears in its runs list), Edit (opens `ScheduleForm`), Delete (confirm dialog, then DELETE). A New schedule button opens an empty form. Expanding a row shows `ScheduleRuns`. Errors show the server's message. Empty state explains what a schedule does.

## Acceptance conditions

- AC1: the page lists schedules with next fire time and last run status [evidence: command:npx vitest run src/schedules/SchedulesPage.test.tsx -t 'lists']
- AC2: enable/disable and run now call the API and refresh the row [evidence: command:npx vitest run src/schedules/SchedulesPage.test.tsx -t 'controls']
- AC3: delete asks for confirmation before calling the API [evidence: command:npx vitest run src/schedules/SchedulesPage.test.tsx -t 'delete']
- AC4: new and edit open the form and the list updates on save [evidence: command:npx vitest run src/schedules/SchedulesPage.test.tsx -t 'form']

## Files

- `src/schedules/SchedulesPage.tsx`
- `src/schedules/SchedulesPage.test.tsx`

## Interfaces

- `SchedulesPage({onBack})` (part `web-schedules-page`); `onBack` comes from the registry `render(onBack)`.

## Expected outcome

Schedules are fully managed from one page.

## Steps

- Write SchedulesPage.test.tsx; it fails.
- Write SchedulesPage.tsx; it passes.
- `npm run lint` clean.

## Notes

- Mirror the webhook pages' layout (contract `trigger-ui-page-pattern`) so both trigger pages look alike.
