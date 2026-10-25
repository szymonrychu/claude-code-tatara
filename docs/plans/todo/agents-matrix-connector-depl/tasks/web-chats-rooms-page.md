---
title: web chats rooms page
status: todo
repo: agents-web
value: "an operator sees every discovered chat, its access and recent messages, and allows or denies it"
files: [src/matrix/ChatsPage.tsx, src/matrix/RoomsTable.tsx, src/matrix/RoomDrawer.tsx, src/matrix/RoomMessages.tsx, src/matrix/ChatsPage.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/matrix/ChatsPage.test.tsx && npm run lint"
depends_on: [web-matrix-api-client]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 14
expected_tokens: 1860143
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web chats rooms page

## Requirement

The Chats page: rooms table, room drawer and recent messages (design D12). Paths are in code/agents-web.

- `src/matrix/ChatsPage.tsx`: `ChatsPage({onBack, onOpenSession})` with a header showing the bot user id and sync health from `getMeta()` (a warning when `sync.healthy` is false) and a Rooms section; polls rooms every 5 s with `usePoll` (trigger UI kit).
- `src/matrix/RoomsTable.tsx`: columns name, kind (DM, Group, Matrix, Infrastructure), flags (message request, encrypted), members, access chip (allowed, denied, default with the reason), preset name, effective trigger, session slug (clicking calls `onOpenSession(sessionId)`), last activity, queued; a kind filter and an access filter; a row click opens the drawer.
- `src/matrix/RoomDrawer.tsx`: members (display name, Matrix id, Facebook id, access chip); preset (`PresetSelect`, with "Default preset" as the empty choice) and trigger (Default, All messages, Only when mentioned) saved through `setRoomSettings` with `FormError` on 422; Allow room and Deny room buttons (`addRule` with kind `room`), disabled for infrastructure and encrypted rooms, each after a `ConfirmDialog`; when a room rule exists, a Remove rule action instead.
- `src/matrix/RoomMessages.tsx`: the room's recent messages (`listRoomMessages`, polled every 5 s while the drawer is open): direction, time, sender name, body (or "not stored" when the body is null), status via `RunStatusChip` and reason; Load older through `beforeId`.
- `src/matrix/ChatsPage.test.tsx`: the table renders rooms with their access and session; filters work; the drawer saves preset and trigger and shows a 422 message; Allow and Deny create the right rule after confirming and are disabled for encrypted and infrastructure rooms; messages render including "not stored".

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: the rooms table shows kind, flags, access, preset, trigger, session and queued, and filters by kind and access [evidence: command:npx vitest run src/matrix/ChatsPage.test.tsx -t "lists rooms with access and session"]
- AC2: the drawer saves the preset and trigger and shows a 422 error [evidence: command:npx vitest run src/matrix/ChatsPage.test.tsx -t "saves room settings"]
- AC3: Allow room and Deny room create the room rule after a confirm and are disabled for encrypted and infrastructure rooms [evidence: command:npx vitest run src/matrix/ChatsPage.test.tsx -t "allows and denies a room"]
- AC4: recent messages show both directions, status and reason, and "not stored" for a null body [evidence: command:npx vitest run src/matrix/ChatsPage.test.tsx -t "shows recent messages"]
- AC5: the header warns when sync is unhealthy [evidence: command:npx vitest run src/matrix/ChatsPage.test.tsx -t "warns on unhealthy sync"]
- AC6: lint passes [evidence: command:npm run lint]

## Files

- `src/matrix/ChatsPage.tsx`
- `src/matrix/RoomsTable.tsx`
- `src/matrix/RoomDrawer.tsx`
- `src/matrix/RoomMessages.tsx`
- `src/matrix/ChatsPage.test.tsx`

## Interfaces

- `src/matrix/ChatsPage.tsx`: `ChatsPage({onBack, onOpenSession})`, extended by web-chats-access-panels and rendered by web-chats-menu-entry.
- Uses `src/triggers/index.ts` (`usePoll`, `PresetSelect`, `RunStatusChip`, `FormError`; contract `trigger-ui-page-pattern`) and `src/layout/ConfirmDialog.tsx`.

## Expected outcome

An operator sees every discovered chat, opens one, sets its preset and allows it.

## Steps

- Red: `src/matrix/ChatsPage.test.tsx` with the five cases (mock `src/matrix/api.ts`). Fails: no components.
- Green: write the four components. Run the verify.

## Notes

- Follow `src/webhooks/WebhooksPage.tsx` and `EventsTable.tsx` for layout and polling; MUI components as elsewhere.
- `RunStatusChip` statuses are new, in-progress, handled, ignored, failed, which match the inbound statuses.
