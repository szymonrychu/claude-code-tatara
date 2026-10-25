---
title: web schedule runs list
status: todo
repo: agents-web
value: "a user sees each schedule's recent runs, their status and a link to the cluster"
files: [src/schedules/ScheduleRuns.tsx, src/schedules/ScheduleRuns.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/schedules/ScheduleRuns.test.tsx && npm run lint"
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

- `ScheduleRuns({scheduleId, timezone, refreshKey})` (part `web-schedule-runs`).

## Expected outcome

Run history and cluster links are visible per schedule.

## Steps

- Write ScheduleRuns.test.tsx; it fails.
- Write ScheduleRuns.tsx; it passes.
- `npm run lint` clean.

## Notes

- The cluster link uses the cluster view route agents-web already has for the orchestrator.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule
