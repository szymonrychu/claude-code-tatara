---
title: web schedule runs list
status: todo
repo: agents-web
value: "a user sees each schedule's recent runs, their status and a link to the session"
files: [src/schedules/ScheduleRuns.tsx, src/schedules/ScheduleRuns.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/schedules/ScheduleRuns.test.tsx && npm run lint"
depends_on: [web-schedules-api-client]
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

# web schedule runs list

## Requirement

Add `ScheduleRuns` (design D12; approval A4): the last 20 runs of one schedule (`listScheduleRuns`), newest first, each with fire time in the schedule's zone, trigger (scheduled or manual), `RunStatusChip` from the trigger UI kit (contract `trigger-ui-page-pattern`), the reason when present, and a link to the session in the orchestrator view when `session_id` is set. Refreshes with `usePoll` every 10 s while mounted and on `refreshKey` change.

## Acceptance conditions

- AC1: runs render newest first with status, trigger and reason [evidence: command:npx vitest run src/schedules/ScheduleRuns.test.tsx -t 'renders']
- AC2: a run with a session links to that session [evidence: command:npx vitest run src/schedules/ScheduleRuns.test.tsx -t 'session link']
- AC3: the list refreshes on its interval and on refreshKey [evidence: command:npx vitest run src/schedules/ScheduleRuns.test.tsx -t 'refresh']

## Files

- `src/schedules/ScheduleRuns.tsx`
- `src/schedules/ScheduleRuns.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
