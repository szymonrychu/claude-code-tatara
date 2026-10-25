---
title: web schedule form
status: todo
repo: agents-web
value: a user creates or edits a schedule and sees its next fire times before saving
files: [src/schedules/ScheduleForm.tsx, src/schedules/ScheduleForm.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/schedules/ScheduleForm.test.tsx && npm run lint"
depends_on: [web-schedules-api-client]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web schedule form

## Requirement

Add `ScheduleForm` (design D4, D7, D12; approvals A2, A4) on the trigger UI kit agents-webhook-microservice puts in agents-web (contract `trigger-ui-page-pattern`, `src/triggers/index.ts`: `PresetSelect`, `RunStatusChip`, `usePoll`).

- Fields: name, cron (5 fields, with a one-line syntax hint), timezone (select over `Intl.supportedValuesOf('timeZone')`, default `Europe/Warsaw`), preset (`PresetSelect` over the orchestrator's `GET /api/v1/presets`), prompt (textarea, hint naming `{schedule_name}` and `{fired_at}`), enabled.
- Live preview: on cron or timezone change (debounced 300 ms) calls `previewSchedule` and lists the next 3 fire times in the chosen zone; a 422 shows the server's reason under the cron or timezone field.
- Save calls create or update; server errors (422 codes, 409 name conflict) appear on the matching field; success calls `onSaved(schedule)`.

## Acceptance conditions

- AC1: the form shows the next 3 fire times for a valid cron and the reason for an invalid one [evidence: command:npx vitest run src/schedules/ScheduleForm.test.tsx -t 'preview']
- AC2: timezone defaults to Europe/Warsaw and presets come from the orchestrator [evidence: command:npx vitest run src/schedules/ScheduleForm.test.tsx -t 'defaults']
- AC3: server validation errors land on their fields [evidence: command:npx vitest run src/schedules/ScheduleForm.test.tsx -t 'errors']
- AC4: save creates or updates and reports the saved schedule [evidence: command:npx vitest run src/schedules/ScheduleForm.test.tsx -t 'save']

## Files

- `src/schedules/ScheduleForm.tsx`
- `src/schedules/ScheduleForm.test.tsx`

## Interfaces

- `ScheduleForm({schedule?: ScheduleView, onSaved, onCancel})` (part `web-schedule-form`).

## Expected outcome

Schedules are created and edited in the UI with a preview of when they fire.

## Steps

- Write ScheduleForm.test.tsx; `npx vitest run src/schedules/ScheduleForm.test.tsx` fails.
- Write ScheduleForm.tsx; the test passes.
- `npm run lint` clean.

## Notes

- Reuse `PresetSelect` from the kit; do not write another preset picker.
