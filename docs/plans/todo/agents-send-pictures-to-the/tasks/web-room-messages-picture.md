---
title: web room messages picture
status: todo
repo: agents-web
value: "the Chats page lists a sent picture as picture: <name>"
files: [openapi/matrix.json, openapi/matrix.source, src/api/matrix-schema.d.ts, src/matrix/RoomMessages.tsx, src/matrix/RoomMessages.test.tsx]
verify: "npx vitest run src/matrix && npm run check:api && npm run lint"
depends_on: [mxc-room-messages-msgtype]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web room messages picture

## Requirement

README Goal G3, verbatim: "the session web chat shows the sent picture inside the tool-call box from the same-origin session download route; message text still never renders images; the Chats page shows "picture: <name>"."

Design D8, verbatim: "Chats page: MessageView grows `msgtype` (from outbound.content); RoomMessages shows "picture: <name>" for m.image. No bytes served by the connector, no mxc proxy. User Q3."

Open question Q3 (planned on its recommended answer): "The Chats page shows a "picture: <name>" line, not the image? [recommended: yes]"

Scope (agents-web):
- `openapi/matrix.json` synced (`npm run sync:api -- matrix`) from the connector commit that carries `MessageView.msgtype` (mxc-room-messages-msgtype): connector `main` once merged, else the connector epic-branch commit kept reachable by a merge commit (my call, the matrix epic's precedent 23f0424); `openapi/matrix.source` names it; `src/api/matrix-schema.d.ts` regenerated.
- `src/matrix/RoomMessages.tsx`: an outbound row with `msgtype` `m.image` shows `picture: <body>` in the Body cell; every other row as today; no `<img>`.
- `src/matrix/RoomMessages.test.tsx` (new test file).

## Acceptance conditions

- ac1: an outbound message with msgtype m.image shows "picture: <name>" in the Body cell, and text rows and inbound rows show their body as before [evidence: command:npx vitest run src/matrix/RoomMessages.test.tsx]
- ac2: the matrix OpenAPI copy and its types agree, and the source names the connector commit carrying msgtype [evidence: command:npm run check:api && grep -q 'msgtype' openapi/matrix.json && grep -qE '^agents-matrix-connector [0-9a-f]{40}$' openapi/matrix.source]
- ac3: RoomMessages renders no img [evidence: command:test "$(grep -c '<img' src/matrix/RoomMessages.tsx)" = 0]
- ac4: the matrix tests, API check and lint pass [evidence: command:npx vitest run src/matrix && npm run check:api && npm run lint]

## Files

- `openapi/matrix.json`
- `openapi/matrix.source`
- `src/api/matrix-schema.d.ts`
- `src/matrix/RoomMessages.tsx`
- `src/matrix/RoomMessages.test.tsx`

## Interfaces

- `MessageView.msgtype: string | null` (connector UI API, `src/api/matrix-schema.d.ts`, re-exported by `src/matrix/api.ts`).

## Expected outcome

The Chats page lists a picture the agent sent as "picture: <name>" instead of a bare file name.

## Steps

- Red: `src/matrix/RoomMessages.test.tsx` (mock `listRoomMessages` as `ChatsPage.test.tsx` does); run `npx vitest run src/matrix/RoomMessages.test.tsx`: fails.
- Green: sync the matrix API from the connector commit, regenerate the types, the Body cell; run the task's verify: passes. Quote the summary line.

## Notes

- `npm run sync:api -- matrix [--from <checkout>]` reads the sibling `../agents-matrix-connector`; check out the pinned commit there first.
- No bytes and no mxc URL reach the browser (non-goal: image bytes on the Chats page).
- (my call, builder-check Q1) The connector tasks merge to connector `main` first; this task starts after that and pins the connector `main` sha, so the epic-branch fallback in Scope is not used.
