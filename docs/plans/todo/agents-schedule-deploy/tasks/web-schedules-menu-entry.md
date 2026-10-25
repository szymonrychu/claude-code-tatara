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

- `src/schedules/menu.ts:schedulesMenu`, `BACKEND_MENUS.schedules` in `src/backends/registry.ts` (part `web-schedules-menu`).

## Expected outcome

The schedules UI lives in the hamburger menu.

## Steps

- Add the three tests to src/backends/registry.test.ts; they fail.
- Register the entry; they pass.
- `npm run lint` clean.

## Notes

- `SchedulesPage` accepts `onBack` per the registry's `render(onBack)`.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule
