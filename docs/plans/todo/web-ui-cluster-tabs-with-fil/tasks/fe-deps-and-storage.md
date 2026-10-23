---
title: fe deps and storage
status: todo
repo: agent-orchestrator
value: "the frontend has the panel, tree, terminal and icon libraries and crash-proof UI state storage"
files: [frontend/package.json, frontend/package-lock.json, frontend/vite.config.ts, frontend/src/api/client.ts, frontend/src/layout/storage.ts, frontend/src/layout/storage.test.ts]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/storage.test.ts src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: []
owns: [fe-deps, fe-storage]
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
