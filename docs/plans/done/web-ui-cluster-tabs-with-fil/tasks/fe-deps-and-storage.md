---
title: fe deps and storage
status: done
repo: agent-orchestrator
value: "the frontend has the panel, tree, terminal and icon libraries and crash-proof UI state storage"
files: [frontend/package.json, frontend/package-lock.json, frontend/vite.config.ts, frontend/src/api/client.ts, frontend/src/layout/storage.ts, frontend/src/layout/storage.test.ts]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/storage.test.ts src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: []
model: ""
review: ""
verified_head: fa1456d8c69b6a9b89be5f97bd0d317299d0f758
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 5
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# fe deps and storage

## Requirement

Lay the frontend foundation for the workspace (design D7; user Q13), test-first where behaviour exists.

- Dependencies in `frontend/package.json` with the lock updated (`npm install`, commit `package-lock.json`): `react-resizable-panels` `^4.14.8`, `@xterm/xterm` `^6.0.0`, `@xterm/addon-fit` `^0.11.0`, `@mui/x-tree-view` `^9.16.0`, `@mui/icons-material` `~9.5.0`. `npm ci` stays clean (no peer conflicts with React 19.3 and MUI 9.5).
- `frontend/vite.config.ts`: the dev proxy for `/api` also proxies WebSockets (`ws: true`).
- `frontend/src/api/client.ts`: export the existing `request` and `query` helpers (no behaviour change) so new API modules reuse them.
- New `frontend/src/layout/storage.ts`: `loadJson<T>(key: string, fallback: T, valid?: (v: unknown) => v is T): T` and `saveJson(key: string, value: unknown): void`. Neither ever throws: a missing `localStorage`, a throwing getter or setter (private mode, quota), invalid JSON or a value failing `valid` all yield the fallback or a silent no-op. Keys are namespaced `orch:`.

## Acceptance conditions

- AC1: loadJson returns stored values and the fallback for missing, invalid or rejected values [evidence: test:frontend/src/layout/storage.test.ts::loadJson_round_trip_and_fallbacks]
- AC2: loadJson and saveJson never throw when localStorage is absent or throws [evidence: test:frontend/src/layout/storage.test.ts::storage_never_throws]
- AC3: the new dependencies install cleanly and the app builds [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend run build]
- AC4: the Vite dev proxy forwards WebSockets [evidence: command:grep -q 'ws: true' frontend/vite.config.ts]
- AC5: storage test, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/storage.test.ts src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

## Files

- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/vite.config.ts`
- `frontend/src/api/client.ts`
- `frontend/src/layout/storage.ts`
- `frontend/src/layout/storage.test.ts`

## Interfaces

- `frontend/src/layout/storage.ts`: `loadJson`, `saveJson` (owns part `fe-storage`, consumed by fe-panel-workspace).
- `frontend/package.json` dependency set (owns part `fe-deps`, consumed by fe-top-bar, fe-panel-workspace, fe-filesystem-panel, fe-terminal-socket, fe-terminal-panel).
- `frontend/src/api/client.ts`: `request`, `query` now exported.

## Expected outcome

Every later frontend task can import the panel, tree, terminal and icon libraries, call `request`, and persist UI state safely.

## Steps

- Write `frontend/src/layout/storage.test.ts` (node environment, stub `globalThis.localStorage` with a map and with throwing methods; test titles exactly `loadJson_round_trip_and_fallbacks` and `storage_never_throws`); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/storage.test.ts`: fails (module missing).
- Implement `storage.ts`; rerun: passes.
- Add the dependencies (`mise x node@24.20.0 -- npm --prefix frontend install <pkgs>`), the proxy flag and the exports; run the verify command: passes.

## Notes

- PATH node is 22; use `mise x node@24.20.0 --` for every npm call (jsdom 30 wants node 24).
- The build already warns about a chunk over 500 kB; that warning is non-fatal and not in scope.
- No colour literals anywhere outside `theme.ts` (designRules).
