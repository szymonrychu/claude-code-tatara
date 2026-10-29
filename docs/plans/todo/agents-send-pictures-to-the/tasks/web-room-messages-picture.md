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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
