---
title: web room initiate toggle
status: todo
repo: agents-web
value: "the user switches 'Agents may start chats' on or off per room in the web UI"
files: [openapi/matrix.json, openapi/matrix.source, src/api/matrix-schema.d.ts, src/matrix/RoomDrawer.tsx, src/matrix/ChatsPage.test.tsx]
verify: "npx vitest run src/matrix && npm run check:api && npm run lint"
depends_on: [mxc-room-initiate-flag]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 941421
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web room initiate toggle

## Requirement

README Goal, verbatim: "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

Design D15, verbatim: "The room drawer gets an "Agents may start chats" switch bound to `agents_may_initiate`, saved with the preset and trigger in the one PUT (gate question Q4). The vendored `openapi/matrix.json` and generated `src/api/matrix-schema.d.ts` follow the connector's committed `openapi.json`."

Open question Q4 (pending gate), verbatim: "Add an 'agents may start chats' toggle to the agents-web room settings in this epic (my call, pending gate)?" recommended "yes".

Constraint (lead, verbatim): "agents-web toggle lands after markdown-rendering-in-chat and file-editor-with-tabs-and-hi (shared agents-web files)".

Scope (agents-web): `npm run sync:api -- matrix` from the agents-matrix-connector `main` that carries mxc-room-initiate-flag (updates `openapi/matrix.json`, `openapi/matrix.source`, `src/api/matrix-schema.d.ts`); `src/matrix/RoomDrawer.tsx` gets the switch (label "Agents may start chats", initial value from the room detail, saved in the same `setRoomSettings` call). `src/matrix/ChatsPage.test.tsx` test 'saves room settings' is no longer accurate (named): it expects the PUT body `{preset_id, trigger}` only; the body now always carries `agents_may_initiate`, so its two `toHaveBeenCalledWith` expectations gain the field (false here).

## Acceptance conditions

- ac1: the room drawer shows an "Agents may start chats" switch reflecting agents_may_initiate, and Save sends it with the preset and trigger in one setRoomSettings call [evidence: command:npx vitest run src/matrix/ChatsPage.test.tsx -t "agents may start chats"]
- ac2: saving the preset and trigger sends agents_may_initiate as loaded, so an untouched switch never changes the flag (updated) [evidence: command:npx vitest run src/matrix/ChatsPage.test.tsx -t "saves room settings"]
- ac3: the vendored matrix OpenAPI document and the generated types match, and matrix.source names the connector commit they came from [evidence: command:npm run check:api && grep -q '^agents-matrix-connector [0-9a-f]\{40\}$' openapi/matrix.source && grep -q agents_may_initiate openapi/matrix.json]
- ac4: the matrix UI tests and lint pass [evidence: command:npx vitest run src/matrix && npm run lint]

## Files

- `openapi/matrix.json`
- `openapi/matrix.source`
- `src/api/matrix-schema.d.ts`
- `src/matrix/RoomDrawer.tsx`
- `src/matrix/ChatsPage.test.tsx`

## Interfaces

- `RoomSettingsIn` (generated) gains `agents_may_initiate?: boolean | null`; `RoomView` gains `agents_may_initiate: boolean`.
- `RoomDrawer`: state `mayInitiate`, loaded from `RoomDetail.agents_may_initiate`, sent as `agents_may_initiate` in `setRoomSettings(roomId, {preset_id, trigger, agents_may_initiate})`.

## Expected outcome

The user turns "Agents may start chats" on or off per room in the web UI.

## Steps

- Sync: `npm run sync:api -- matrix` (reads the sibling agents-matrix-connector checkout at its `main`; confirm `main` carries the flag first).
- Red: add the "agents may start chats" test, update 'saves room settings'; run `npx vitest run src/matrix/ChatsPage.test.tsx`: they fail.
- Green: the switch in `RoomDrawer.tsx`; run the task's verify: passes. Quote the summary line with counts.

## Notes

- Held until markdown-rendering-in-chat and file-editor-with-tabs-and-hi are done (README blockers).
- Use the MUI `Switch` with `FormControlLabel` as other drawers do; the label text is the accessible name the test queries.
- The connector keeps the stored flag when the field is omitted (mxc-room-initiate-flag), but the UI always sends it, so what the user sees is what is saved.
