---
title: web schedules menu entry
status: todo
repo: agents-web
value: Schedules appears in the hamburger menu below Webhooks when the schedule backend is configured
files: [src/App.tsx, src/App.test.tsx]
verify: "npx vitest run src/App.test.tsx && npm run lint"
depends_on: [web-schedules-page]
owns: [web-schedules-menu]
uses: [web-schedules-page, web-menu-entries, web-backends-config]
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

# web schedules menu entry

## Requirement

Register the Schedules entry (design D12; approval A4, gate Q7) through the frontend-decoupling menu mechanism (contract `web-menu-entries`, successor of `orch-settings-menu`): label `Schedules`, position directly below the webhook entry, giving Clusters, Webhooks, Schedules, Presets; it opens `SchedulesPage`. The entry is present only when `config.json` lists the `schedules` backend (`web-backends-config`); without the webhook entry it sits directly above Presets.

## Acceptance conditions

- AC1: with the schedules backend configured the menu shows Clusters, Webhooks, Schedules, Presets in order [evidence: command:npx vitest run src/App.test.tsx -t 'schedules menu order']
- AC2: without the backend there is no Schedules entry [evidence: command:npx vitest run src/App.test.tsx -t 'schedules hidden']
- AC3: the entry opens the schedules page [evidence: command:npx vitest run src/App.test.tsx -t 'opens schedules']

## Files

- `src/App.tsx`
- `src/App.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
