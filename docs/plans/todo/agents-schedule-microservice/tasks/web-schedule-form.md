---
title: web schedule form
status: todo
repo: agents-web
value: a user creates or edits a schedule and sees its next fire times before saving
files: [src/schedules/ScheduleForm.tsx, src/schedules/ScheduleForm.test.tsx]
verify: "npx vitest run src/schedules/ScheduleForm.test.tsx && npm run lint"
depends_on: [web-schedules-api-client]
owns: [web-schedule-form]
uses: [web-schedules-client, trigger-ui-page-pattern, orch-presets-api]
model: ""
estimate: 5
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

# web schedule form

## Requirement

Add `ScheduleForm` (design D4, D7, D12; approvals A2, A4), built on the trigger mapping page pattern agents-webhook-microservice puts in agents-web (contract `trigger-ui-page-pattern`: preset picker, form layout, error display).

- Fields: name, cron (5 fields, with a one-line syntax hint), timezone (select over `Intl.supportedValuesOf('timeZone')`, default `Europe/Warsaw`), preset (picker over the orchestrator's `GET /api/v1/presets`), prompt (textarea, hint naming `{schedule_name}` and `{fired_at}`), enabled.
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
