---
title: web schedules menu entry
status: todo
repo: agents-web
value: Schedules appears in the hamburger menu below Webhooks when the schedule backend is configured
files: [src/schedules/menu.ts, src/backends/registry.ts, src/backends/registry.test.ts]
verify: "npm ci --no-audit --no-fund && npx vitest run src/backends/registry.test.ts src/App.test.tsx && npm run lint"
depends_on: [web-schedules-page]
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

# web schedules menu entry

## Requirement

Register the Schedules entry (design D12; approval A4, gate Q7) in the frontend-decoupling backend registry (contract `agents-web-backend-registry`, `src/backends/registry.ts`; order rule `web-settings-menu-order` of configuration-improvements): `src/schedules/menu.ts` exports `schedulesMenu: MenuEntry = {id: 'schedules', label: 'Schedules', order: 30, backend: 'schedules', render: (onBack) => createElement(SchedulesPage, {onBack})}` (a `.ts` file, so no JSX), and `src/backends/registry.ts` sets `BACKEND_MENUS.schedules = [schedulesMenu]` (the agents-webhook web-webhook-menu-entry shape). `src/App.test.tsx` stays green. Order 30 is the slot the registry reserves for Schedules, between Webhooks (20) and Presets (40), giving Sessions, Webhooks, Schedules, Presets (gate Q7). The entry appears only when `config.json` lists the `schedules` backend.

## Acceptance conditions

- AC1: with the schedules backend configured, Schedules sorts after Webhooks and before Presets [evidence: command:npx vitest run src/backends/registry.test.ts -t 'schedules order']
- AC2: without the schedules backend there is no Schedules entry [evidence: command:npx vitest run src/backends/registry.test.ts -t 'schedules hidden']
- AC3: the entry renders the schedules page [evidence: command:npx vitest run src/backends/registry.test.ts -t 'schedules render']

## Files

- `src/schedules/menu.ts`
- `src/backends/registry.ts`
- `src/backends/registry.test.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
