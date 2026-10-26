---
title: web chats menu entry
status: done
repo: agents-web
value: the Chats page is reachable from the menu between Schedules and Presets
files: [src/matrix/menu.tsx, src/backends/registry.ts, src/backends/registry.test.ts]
verify: "npm ci --no-audit --no-fund && npx vitest run src/backends/registry.test.ts src/App.test.tsx && npm run lint"
depends_on: [web-chats-access-panels]
model: sonnet
review: ""
verified_head: 162770e3207614d19913e7c6426cb40b9b5390db
points: 1
expected_minutes: 5
expected_tokens: 678580
points_actual: 1
actual_minutes: 2
actual_tokens: 194601
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 136995, review 57606"
---

# web chats menu entry

## Requirement

Make the Chats page reachable from the menu (design D12; contract `agents-web-backend-registry`). Paths are in code/agents-web.

- `src/matrix/menu.tsx`: `chatsMenu: MenuEntry = {id: 'chats', label: 'Chats', order: 35, backend: 'matrix', render}` rendering `ChatsPage` with `onBack` and `openSession`, the session opener `MenuEntry.render` passes after orchestrator-rename-sessions task web-sessions-pages.
- `src/backends/registry.ts`: `BACKEND_MENUS.matrix = [chatsMenu]`; the reserved-slots comment gains `35 Chats (agents-matrix-connector)`.
- `src/backends/registry.test.ts`: with the matrix backend configured the entry is listed between Schedules (30) and Presets (40); without it, it is absent.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: the Chats entry appears at order 35 only when the matrix backend is configured [evidence: command:npx vitest run src/backends/registry.test.ts -t "lists Chats only with the matrix backend"]
- AC2: the app tests and lint pass [evidence: command:npx vitest run src/backends/registry.test.ts src/App.test.tsx && npm run lint]

## Files

- `src/matrix/menu.tsx`
- `src/backends/registry.ts`
- `src/backends/registry.test.ts`

## Interfaces

- `BACKEND_MENUS.matrix` (contract `agents-web-backend-registry`, slot 35).

## Expected outcome

With `config.json` listing `{id: matrix, label: Chats, basePath: /matrix/api/v1}`, the menu shows Chats.

## Steps

- Red: add the registry test case. Fails: no entry.
- Green: write `menu.tsx` and register it. Run the verify.

## Notes

- Same shape as agents-webhook-microservice task web-webhook-menu-entry.

- 2026-10-26 done
