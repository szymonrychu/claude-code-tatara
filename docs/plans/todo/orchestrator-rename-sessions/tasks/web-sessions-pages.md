---
title: web sessions pages
status: todo
repo: agents-web
value: the Sessions settings page and its dialogs say session
files: [src/clusters/, src/sessions/, src/backends/registry.ts, src/backends/registry.test.ts, src/App.tsx, src/App.test.tsx, src/nomenclature.test.ts]
verify: "npx tsc -b && npx vitest run src/sessions src/backends src/App.test.tsx src/nomenclature.test.ts && npm run lint"
depends_on: [web-api-layer-sessions]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web sessions pages

## Requirement

Rename the sessions settings page and its dialogs (design D2, D12; user decision: cluster is renamed session throughout, with the web UI fixed to match). Paths are in code/agents-web.

- `git mv src/clusters src/sessions`: `SessionsPage` (title "Sessions", button "New session", empty state "No sessions yet"), `NewSessionDialog` (title and aria-label "New session"), `DiscardSessionDialog` (body: "Everything is deleted: the agents, the workspace PVC and its files, and the session's whole chat history ..."), `InitScriptsDialog` ("No run recorded for this session.", "Saved. Applies to the next session"), `sessionSpecForm.ts`; each `*.test.tsx` renamed with its component and asserting the new texts.
- `src/backends/registry.ts`: menu entry id `sessions`, label "Sessions", order 10, `openSession`; `src/backends/registry.test.ts`.
- `src/App.tsx`, `src/App.test.tsx`: the settings route to the sessions page, "No sessions yet"; test names that name the unit say session.
- New `src/nomenclature.test.ts` (D12): `git ls-files` over `src/sessions`, `src/backends`, `src/App.tsx` and `src/App.test.tsx` has no line matching `/cluster/i`; web-workspace-sessions and web-docs-names widen the guarded list.
- Tests first: the renamed page and dialog tests fail on the old texts before the rename.

## Acceptance conditions

- AC1: the sessions page shows Sessions, New session and No sessions yet [evidence: test:src/sessions/SessionsPage.test.tsx::lists sessions]
- AC2: the menu entry is sessions / Sessions [evidence: test:src/backends/registry.test.ts::sessions entry]
- AC3: the old directory is gone from git [evidence: command:test -z "$(git ls-files src/clusters)"]
- AC4: the guarded paths name the unit session only [evidence: command:npx vitest run src/nomenclature.test.ts]
- AC5: the UI type-checks, the touched tests and lint pass [evidence: command:npx tsc -b && npx vitest run src/sessions src/backends src/App.test.tsx && npm run lint]

## Files

- `src/clusters/`
- `src/sessions/`
- `src/backends/registry.ts`
- `src/backends/registry.test.ts`
- `src/App.tsx`
- `src/App.test.tsx`
- `src/nomenclature.test.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
