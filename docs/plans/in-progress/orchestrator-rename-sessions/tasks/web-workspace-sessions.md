---
title: web workspace sessions
status: in-progress
repo: agents-web
value: "the chat, top bar, menu, files, terminal and preset form say session"
files: [src/chat/, src/ribbon/, src/layout/, src/files/, src/terminal/, src/presets/, src/nomenclature.test.ts]
verify: "npx tsc -b && npx vitest run && npm run lint"
depends_on: [web-sessions-pages]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 14
expected_tokens: 1883475
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web workspace sessions

## Requirement

Rename the session workspace UI: chat, ribbon, top bar, menu, files, terminal and presets (design D2, D12; user decision: cluster is renamed session throughout, with the web UI fixed to match). Paths are in code/agents-web.

- `src/chat/`: `useClusterChat.ts` to `useSessionChat.ts`; Composer placeholder "Message the session"; ScaleControl tooltip "Static session: scaling is off"; AgentsStrip, ChatView, QueueStrip, ChatLog props and identifiers.
- `src/ribbon/`: `useClusters.ts` to `useSessions.ts` and its state (`sessions`, `session`).
- `src/layout/`: TopBar button "New session" and props; SessionsMenu empty state "No sessions yet" and props; Workspace `data-session` attribute; panel layout and storage keys that name the unit (saved layouts under the old key are dropped once, no migration, D2 no-compat); ConfirmDialog test texts.
- `src/files/`, `src/terminal/`: props, identifiers, comments (`sessionId`).
- `src/presets/`: PresetForm help texts "More than 1 makes the session a hive" and "Runs once when a session starts, in the shared workdir; agents can read and edit it; edits apply to the next session"; PresetsPage doc comment "the stored SessionSpec templates".
- Every test in these directories follows the rename, test names included.
- `src/nomenclature.test.ts`: guard all of `src/` except `src/webhooks/` and `src/api/webhooks-schema.d.ts` (web-webhooks-session-fields adds them).

## Acceptance conditions

- AC1: the composer invites a message to the session [evidence: test:src/chat/Composer.test.tsx::placeholder names the session]
- AC2: the top bar offers New session and the menu says No sessions yet [evidence: test:src/layout/TopBar.test.tsx::new session button]
- AC3: preset help texts say session [evidence: test:src/presets/PresetForm.test.tsx::help texts name the session]
- AC4: src outside the webhooks UI names the unit session only [evidence: command:npx vitest run src/nomenclature.test.ts]
- AC5: the UI type-checks, its tests and lint pass [evidence: command:npx tsc -b && npx vitest run && npm run lint]

## Files

- `src/chat/`
- `src/ribbon/`
- `src/layout/`
- `src/files/`
- `src/terminal/`
- `src/presets/`
- `src/nomenclature.test.ts`

## Interfaces

- `useSessions()` (ribbon state) and `useSessionChat()` hooks; `data-session` on the workspace root.

## Expected outcome

Every chat, top bar, menu, files, terminal and preset text says session; src outside the webhooks UI passes the guard.

## Steps

- Red: change the expected texts in the touched tests and widen `src/nomenclature.test.ts`; `npx vitest run` fails.
- Green: rename hooks, props, texts, storage keys and comments; the verify passes.

## Notes

- Test titles used as AC refs: "placeholder names the session" (Composer.test.tsx), "new session button" (TopBar.test.tsx), "help texts name the session" (PresetForm.test.tsx).
- Saved layouts under old storage keys are dropped once (no migration, no fallback).
