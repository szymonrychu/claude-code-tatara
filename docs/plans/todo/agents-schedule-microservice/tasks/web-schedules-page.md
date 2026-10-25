---
title: web schedules page
status: todo
repo: agents-web
value: "a user manages every schedule from one page: enable, disable, run now, edit, delete"
files: [src/schedules/SchedulesPage.tsx, src/schedules/SchedulesPage.test.tsx]
verify: "npx vitest run src/schedules/SchedulesPage.test.tsx && npm run lint"
depends_on: [web-schedule-form, web-schedule-runs-list]
owns: [web-schedules-page]
uses: [web-schedules-client, web-schedule-form, web-schedule-runs, trigger-ui-page-pattern]
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
