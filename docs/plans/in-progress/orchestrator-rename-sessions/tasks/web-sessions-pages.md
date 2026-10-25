---
title: web sessions pages
status: in-progress
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


Orchestrator ruling 2026-10-25 (review of this task): src/App.tsx and src/App.test.tsx keep their cluster identifiers until web-workspace-sessions renames useClusters, TopBar and the cluster props they import; they compile only together. This task guards src/sessions and src/backends only; the App.tsx and App.test.tsx renames and their guard move to web-workspace-sessions.

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

- Menu entry `{id: 'sessions', label: 'Sessions', order: 10, backend: 'orchestrator'}` (supersedes `web-settings-menu-order`'s Clusters entry for agents-schedule-microservice, which inserts between Sessions and Presets).

## Expected outcome

Settings > Sessions lists sessions with New session and discard; every text says session; `src/clusters` is gone from git.

## Steps

- Red: rename the test files with their components (`git mv`), change their expected texts, write `src/nomenclature.test.ts` over the guarded paths; `npx vitest run src/sessions src/backends src/App.test.tsx src/nomenclature.test.ts` fails.
- Green: `git mv src/clusters src/sessions`, rename components and texts, registry, App; the verify passes.

## Notes

- Test titles used as AC refs: "lists sessions" in SessionsPage.test.tsx, "sessions entry" in registry.test.ts.

- 2026-10-25 amended: App.tsx/App.test.tsx renames move to web-workspace-sessions (compile dependency)
