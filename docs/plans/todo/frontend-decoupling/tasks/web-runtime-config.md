---
title: web runtime config
status: todo
repo: agents-web
value: "one UI bundle runs anywhere; config.json says where each backend is"
files: [public/config.json, src/config/backends.ts, src/config/backends.test.ts, src/main.tsx, src/api/client.ts, src/api/terminals.ts, src/api/client.test.ts, vite.config.ts]
verify: "npm ci --no-audit --no-fund && npx vitest run src/config/backends.test.ts src/api/client.test.ts src/terminal/terminalSocket.test.ts && npm run lint"
depends_on: []
owns: [backends-config]
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

# web runtime config

## Requirement

The UI reads its backends from a runtime `config.json` and every orchestrator URL follows the configured base path (design D3). Paths are in code/agents-web.

- `src/config/backends.ts`:
  - types `Backend {id, label, basePath}` and `RuntimeConfig {backends: Backend[]}`;
  - `parseConfig(json: unknown): RuntimeConfig` throws `ConfigError` with a message naming the field when: `backends` is not an array; an `id` does not match `^[a-z][a-z0-9-]*$` or repeats; a `label` is empty; a `basePath` does not start with `/`, ends with `/`, or contains `//`, `://`, `?` or `#`; no backend has id `orchestrator`. Unknown keys are ignored.
  - `loadConfig(fetchFn = fetch)`: GET `/config.json` with `cache: 'no-store'`, rejects a non-2xx answer with a `ConfigError` naming the status, parses with `parseConfig`, and makes the result current.
  - `backendBase(id)` returns the current base path of a configured backend and throws `ConfigError` for an unconfigured one; `isConfigured(id)` returns a boolean.
- `src/api/client.ts`: the orchestrator base comes from `backendBase('orchestrator')` at call time; `request`, `eventStreamUrl` and `statusStreamUrl` stay relative. Until a config is loaded (unit tests) the base is `/api/v1`.
- `src/api/terminals.ts:terminalSocketUrl`: `ws(s)://${location.host}${orchestrator base}/agents/.../attach`, still same origin.
- `src/main.tsx`: awaits `loadConfig()` before rendering `App`; on a `ConfigError` it renders a plain page with the message and makes no API call.
- `public/config.json`: `{"backends": [{"id": "orchestrator", "label": "Orchestrator", "basePath": "/api/v1"}]}` (dev server and image default; the chart replaces it).
- `vite.config.ts`: the dev server proxies the first path segment of each backend in `public/config.json` (with `ws: true`) to `AGENTS_WEB_PROXY_<ID>` (id upper-cased, `-` to `_`), default `http://localhost:8000` for `orchestrator`.
- Existing tests that assert relative `/api/v1/...` URLs keep passing unchanged; `src/api/client.test.ts` adds one case with `basePath` `/orch/api/v1` proving request, stream and socket URLs follow it.

## Acceptance conditions

- AC1: parseConfig accepts a valid config and rejects each invalid case naming the field; loadConfig rejects a non-2xx answer [evidence: command:npx vitest run src/config/backends.test.ts]
- AC2: orchestrator request, stream and socket URLs follow the configured base path and stay relative [evidence: command:npx vitest run src/api/client.test.ts src/terminal/terminalSocket.test.ts src/chat/ChatLog.test.tsx src/files/FilesPanel.test.tsx]
- AC3: no absolute backend URL in non-test source [evidence: command:! grep -rEn "[\"'\`]https?://" src --include='*.ts' --include='*.tsx' --exclude='*.test.ts' --exclude='*.test.tsx' --exclude=schema.d.ts]
- AC4: the bundle builds and lints [evidence: command:npm run build && npm run lint]
- AC5: main.tsx renders App only after a valid config and a plain error page otherwise [evidence: judgement:reviewer reads src/main.tsx against the requirement]

## Files

- `public/config.json`
- `src/config/backends.ts`
- `src/config/backends.test.ts`
- `src/main.tsx`
- `src/api/client.ts`
- `src/api/terminals.ts`
- `src/api/client.test.ts`
- `vite.config.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
