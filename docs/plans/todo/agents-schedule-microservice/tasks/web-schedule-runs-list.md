---
title: web schedule runs list
status: todo
repo: agents-web
value: "a user sees each schedule's recent runs, their status and a link to the cluster"
files: [src/schedules/ScheduleRuns.tsx, src/schedules/ScheduleRuns.test.tsx]
verify: "npx vitest run src/schedules/ScheduleRuns.test.tsx && npm run lint"
depends_on: [web-schedules-api-client]
owns: [web-schedule-runs]
uses: [web-schedules-client, trigger-ui-page-pattern]
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

# web schedule runs list

## Requirement

Add `ScheduleRuns` (design D12; approval A4): the last 20 runs of one schedule (`listScheduleRuns`), newest first, each with fire time in the schedule's zone, trigger (scheduled or manual), a status chip (new, in-progress, handled, failed, ignored, the webhook page's chip component from `trigger-ui-page-pattern`), the reason when present, and a link to the cluster in the orchestrator UI when `cluster_id` is set. Refreshes every 10 s while mounted and on `refreshKey` change.

## Acceptance conditions

- AC1: runs render newest first with status, trigger and reason [evidence: command:npx vitest run src/schedules/ScheduleRuns.test.tsx -t 'renders']
- AC2: a run with a cluster links to that cluster [evidence: command:npx vitest run src/schedules/ScheduleRuns.test.tsx -t 'cluster link']
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

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
