# Frontend discovery (agent-orchestrator/frontend)

Mapped 2026-10-23 at agent-orchestrator `d5a7738` (cluster-form-defaults-and-ga already merged; research.md cites `3004ed3`). Paths relative to `code/agent-orchestrator/frontend/src/`. Small (about 3900 lines), read directly; no LSP tool available.

## Shape and entrypoints

- `main.tsx`: `createRoot` > `StrictMode` > `ThemeProvider(theme)` > `CssBaseline` > `App`. `index.css` pins `#root` to `100dvh`, `overflow: hidden`, flex column.
- **No router.** No react-router, no `location`/`history` use. `App.tsx:App` calls `useClusters()` and renders `Shell` with `aside={(close) => <Ribbon .../>}` and children `ChatView` for `state.clusters[state.selectedId]`, else "Select a cluster". `api/spa.py:SpaStaticFiles` falls back to `index.html` for non-`/api` paths, so client routes would work.
- Generated: `api/schema.d.ts` (`npm run gen:api` from `../openapi.json`); never hand-edit.

## Components to replace or move (Epic A)

- `layout/Shell.tsx:Shell({title, aside, children})`: phone = `AppBar` + "Menu" `Button` + temporary `Drawer` (`data-testid="ribbon-drawer"`); tablet/desktop = permanent `aside` (`data-testid="ribbon-aside"`, `ASIDE_WIDTH`) + `main` (`p: 2`, `overflow: auto`).
- `layout/useLayout.ts:useLayout(): 'phone'|'tablet'|'desktop'` (sm 600, lg 1200 via `useMediaQuery`).
- `ribbon/Ribbon.tsx:Ribbon({clusters, selectedId, onSelect, error})`: New cluster button, error alert, "No clusters yet", `ClusterRow` list, and owns the three dialogs: `ClusterForm mode="create"` (onSaved selects the new id), `ClusterForm mode="edit"`, `DiscardClusterDialog`.
- `ribbon/ClusterRow.tsx:ClusterRow({entry, selected, onSelect, onEdit, onDiscard})`: `StateMark`, slug, `StatusItem` hook-failed and ready/replicas, `ContextGauge(value=summary.context_pct_max, autoCompactPct)`, +/- expand, "..." `Menu` with Edit and Discard; expanded shows `AgentRow`s.
- `ribbon/AgentRow.tsx:AgentRow({agent, autoCompactPct})`, `formatAge`, private `useNow`.
- `ribbon/stateMark.tsx:StateMark`, `agentMarkState`; `ribbon/ContextGauge.tsx:ContextGauge({value, autoCompactPct, size?, label?})`.
- `ribbon/useClusters.ts`: `useReducer` store, `ClustersState{clusters, selectedId, loaded, error}`, `clustersReducer`, `actionFromEvent`, `sortedClusters` (by slug), `sortedAgents`; `useClusters()` returns `{state, clusters, select}`. `keepSelection` nulls `selectedId` when the cluster disappears; nothing auto-selects. Fed by the status SSE `/api/v1/stream`.
- `chat/ChatView.tsx:ChatView({cluster, agents, maxItems?})`: root is `height: 100%` flex column; header (h5 slug, state caption, `AgentFilter`), `ChatLog`, `QueueStrip`, `Composer`. `chat/AgentFilter.tsx:AgentFilter({agents, selected, onToggle})` chips. Moving agent rows into its header means ChatView is not literally unchanged.
- `chat/useClusterChat.ts`: opens its own `openStream(eventStreamUrl(id))` with `tool_call`, `tool_result` among `STREAM_EVENTS`; the stream is private to the hook. In `chatModel.ts:EventRow`, tool input is `data.tool_input ?? data.input`, name `data.name ?? data.tool_name`, so a Write/Edit path is `data.tool_input.file_path`. The filesystem panel needs a second subscription or a lifted stream.

## designRules.ts (`layout/designRules.ts`)

`SOURCES` = Vite `import.meta.glob(['../**/*.ts','../**/*.tsx', excluding tests], {query:'?raw', eager})`, i.e. every non-test src file; node_modules and CSS are not scanned. `designViolations` bans colour literals outside `theme.ts`, shadows/blur/gradients, `color="secondary"`, decorative Unicode (dashes, smart quotes, ellipsis, arrows, box drawing, emoji), fontWeight other than 400/500, off-grid spacing (0.75/1.25/1.5/2.5), `title=` on `Button`/`IconButton`, filled `Alert`. Test `designRules.test.ts` "source files follow the design rules" fails on any violation. Consequence: an xterm `ITheme` colour map must live in `theme.ts`; SVG icon components are fine.

## Epic B surface

- `clusters/clusterSpecForm.ts`: `FormValues` (slug ... image), `blankValues(meta)` (from `meta.defaults`), `valuesFromSpec(slug, spec)`, `validate(v, mode: 'create'|'edit', meta)` (slug and pvcSize rules only in create), `toSpec`, `envKeyError`, `hookUrlError`, `anyMcpError`, `MAX_SLUG = 40`.
- `clusters/ClusterForm.tsx:ClusterForm({open, mode, cluster?, onClose, onSaved})`; `submit` calls `createCluster({slug, spec})` or `patchCluster(cluster.id, {spec})` (line 73); slug and PVC disabled in edit.
- `clusters/DiscardClusterDialog.tsx:DiscardClusterDialog({open, cluster, onClose, onDiscarded})`, `hookTarget`.
- `api/client.ts`: types are aliases of `components['schemas'][...]` from `./schema` (`ClusterView`, `CreateCluster`, `PatchCluster`, `Meta`, ...); generic `request<T>(method, path, body)` against `BASE='/api/v1'`, throws `ApiError(status, code, message)` from `{error:{code,message}}`; per-route consts (`patchCluster` at lines 75-76).
- `api/stream.ts:openStream(url, {onEvent, eventNames, afterId, eventSource?})`: EventSource wrapper, last-id resume, backoff 1-30 s. There is no WebSocket helper anywhere.
- Tests to retire/rewrite: `ClusterForm.test.tsx` "edit keeps a model...", "edit with a null model...", "edit patches spec", "Ribbon wiring: ribbon opens create, edit and discard"; `ribbon/Ribbon.test.tsx` (7 tests, including phone drawer and desktop aside test ids); `App.test.tsx` expects "No clusters yet".

## Toolchain

- `package.json`: react/react-dom `~19.3.1`, `@mui/material ~9.5.0` (installed 9.5.0, `@mui/system` 9.5.0), emotion 11, `react-virtuoso ~4.18.19`; dev: vite `~8.3.5`, vitest `~5.0.5`, jsdom `^30.1.3`, testing-library react 16, typescript `~5.9.0`, eslint 10, openapi-typescript `~7.13.0`.
- Tests: Vitest, `environment: 'node'` (vite.config.ts), jsdom opted in per file with `// @vitest-environment jsdom`; no setupFiles; each test stubs `window.matchMedia`, mocks `../api/client` and `../api/stream` with `vi.mock`, and mocks heavy DOM libs (`react-virtuoso` in ChatLog.test). No ResizeObserver, WebSocket or localStorage stubs exist yet.
- Build into Python: `Dockerfile` stage `node:24-bookworm-slim` runs `npm ci` and `npm run build` (dist), copied to `/app/static`, `ORCH_STATIC_DIR=/app/static`; `api/app.py:73-74` mounts `SpaStaticFiles` at `/`. Vite dev proxy `'/api': 'http://localhost:8000'` has no `ws: true`.
- Registry (npm view, 2026-10-23): react-resizable-panels 4.14.8 (peer react ^18||^19), @xterm/xterm 6.0.0, @xterm/addon-fit 0.11.0, @mui/x-tree-view 9.16.0 (peer @mui/material and @mui/system ^7.3||^9), @mui/icons-material 9.5.0 (peer @mui/material ^9.5.0). All compatible with MUI 9.5.
- `npm ci` here: `added 305 packages, and audited 306 packages in 8s` / `found 0 vulnerabilities`, with EBADENGINE warnings (jsdom 30 wants node ^22.22.2 or ^24.15; PATH node is `/opt/node22` v22.22.0, tests still pass). Workbench `.mise.toml` pins node 24.20.0 (`/root/.local/share/mise/installs/node/24.20.0/bin`).

## Verify commands (CI `.github/workflows/ci.yaml` job `frontend`, working dir `frontend`)

```
npm ci
npm run lint        # eslint src --max-warnings 0
npm test            # vitest run
npm run build       # tsc -b && vite build
npm run check:api   # regenerate schema to TMPDIR and diff
```
Baseline run here (node 24.20.0): lint exit 0; `Test Files 13 passed (13)`, `Tests 93 passed (93)`; build `built in 1.12s` (warning: 610.68 kB chunk over 500 kB, non-fatal); check:api exit 0. No mise task for the frontend. Python side: `mise run test` includes `tests/test_readme_api.py::test_frontend_schema_matches_openapi`, which needs `frontend/node_modules/.bin/openapi-typescript` (CI job `test` runs `npm ci` first).

## Unknowns

- How react-resizable-panels 4 and xterm 6 behave under jsdom (no ResizeObserver, no canvas); likely need `vi.mock` like react-virtuoso. Settled by a spike test.

## Plan inputs

- New deps: `react-resizable-panels@^4.14.8`, `@xterm/xterm@^6.0.0`, `@xterm/addon-fit@^0.11.0`, `@mui/x-tree-view@^9.16.0`, `@mui/icons-material@~9.5.0`; commit the updated `package-lock.json`.
- Replace: `App.tsx`, `layout/Shell.tsx`, `ribbon/Ribbon.tsx`, `ribbon/ClusterRow.tsx`; move `AgentRow` into the chat panel header; keep `useClusters` (`selectedId` = active tab) and `StateMark`, `ContextGauge`, `DiscardClusterDialog`.
- Retire with tests: `Ribbon.test.tsx`, ribbon test ids, the Edit menu item, `ClusterForm` edit tests (Epic B also `patchCluster`, `PatchCluster` alias, `mode`).
- New seams: a WebSocket client module (none exists), a file API client (after schema regen), an event subscription for the filesystem panel (stream is private to `useClusterChat`), a localStorage layout store keyed by cluster id, xterm colours in `theme.ts`.
- Verify (node 24 on PATH): `npm run lint && npm test && npm run build && npm run check:api` in `frontend/`; `mise run test` after OpenAPI changes.
