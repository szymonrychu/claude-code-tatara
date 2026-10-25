---
title: web chats menu entry
status: todo
repo: agents-web
value: the Chats page is reachable from the menu between Schedules and Presets
files: [src/matrix/menu.tsx, src/backends/registry.ts, src/backends/registry.test.ts]
verify: "npm ci --no-audit --no-fund && npx vitest run src/backends/registry.test.ts src/App.test.tsx && npm run lint"
depends_on: [web-chats-access-panels]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 689196
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web chats menu entry

## Requirement

Make the Chats page reachable from the menu (design D12; contract `agents-web-backend-registry`). Paths are in code/agents-web.

- `src/matrix/menu.tsx`: `chatsMenu: MenuEntry = {id: 'chats', label: 'Chats', order: 35, backend: 'matrix', render}` rendering `ChatsPage` with `onBack` and the session opener the registry passes (the renamed `openCluster`/`openSession` parameter of `MenuEntry.render` after orchestrator-rename-sessions).
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
