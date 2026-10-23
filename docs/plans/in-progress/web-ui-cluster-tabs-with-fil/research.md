# Research: web ui cluster tabs with filesystem chat and terminal panels

Researched 2026-10-23 against agent-orchestrator 3004ed3 and claude-code-wrapper ca2ddf3 (the submodule pins). Paths below are relative to `code/<component>/`.

## 1. Which UI has the left ribbon

- The agent-orchestrator frontend (`frontend/`, React 19.3, MUI 9.5, Vite 8, Vitest 5, react-virtuoso 4.18; `frontend/package.json`). The wrapper has no web UI: its public surface is `/v1` HTTP plus SSE (wrapper README `## API reference`, `## Events (SSE)`).
- `frontend/src/layout/Shell.tsx:15-77`: tablet and desktop render a permanent left `aside` of width `clamp(240px, 24vw, 340px)` beside `main`; phone renders a top bar with a temporary `Drawer`.
- `frontend/src/App.tsx:10-33`: the aside is `Ribbon`, the main pane is `ChatView` for the selected cluster.
- `frontend/src/ribbon/Ribbon.tsx:18-44`: New cluster button, one `ClusterRow` per cluster, the create, edit and discard dialogs.
- `frontend/src/ribbon/ClusterRow.tsx:23-56`: state mark, slug, ready/replicas, `ContextGauge`, expand toggle, actions menu; expanded rows show `AgentRow` (`AgentRow.tsx:31-50`: ordinal, pod, state, free since, own gauge).
- `frontend/src/ribbon/useClusters.ts`: a hand-rolled store, REST load plus `/api/v1/stream` deltas, holding `selectedId`; this maps one to one onto an active tab.
- `frontend/src/chat/ChatView.tsx:22-50`: header, agent filter, `ChatLog`, `QueueStrip`, `Composer`; it is self-contained and can move into a panel unchanged.
- `frontend/src/layout/designRules.ts`: a test-enforced style guard (no colour literals outside theme.ts, no shadows or gradients, no decorative Unicode, no `title=` on buttons). SVG icons are not banned; the current UI uses text buttons (`+`, `-`, `...`) and has no icon package.

## 2. What the backend offers today

Orchestrator `/api/v1` (`src/agent_orchestrator/api/`):

- Clusters and agents: `clusters.py:83-191` (meta, list, create, get, patch, delete, agents).
- Messages and commands: `messages.py:61-176` (send, list, cancel, retry, interrupt, compact, restart, checks).
- Streams: `streams.py:71` paged cluster events, `streams.py:140` cluster event SSE (the chat), `streams.py:243` the global status SSE (the ribbon). The chat already subscribes to `tool_call` and `tool_result` (`chat/useClusterChat.ts:16-17`), so the UI sees every Write and Edit with its `file_path`.
- Access control: `api/allowlist.py:35-49`, a direct-peer CIDR allowlist that already handles WebSocket scopes (closes with 1008). There is no authentication; README `## Security` documents LAN-only exposure and the pod-to-ingress boundary.
- The api process can reach wrappers with their bearer token: the chart passes `ORCH_MASTER_KEY` to every component (`chart/agent-orchestrator/templates/_config.tpl:90-96`) and `tokens.py:33` derives the per-cluster token. Today only the dispatcher, ingester and reconciler call wrappers.

Wrapper `/v1` (`code/claude-code-wrapper`, README lines 157-700): sessions, turns, commands, interrupt, probe, transcript, history, events SSE, config, prompts, peers. No file listing, no file read, no terminal, no WebSocket route anywhere (`grep -rn websocket src` is empty in both repos).

Storage: every agent of a cluster mounts the same RWX PVC at `/workdir` (`k8s/render.py:39-41`, subPath `workdir`) and works in `/workdir/<spec.workdir>` (`render.py:35-36`); sessions are per pod (`render.py:162-165`). So any ready agent can serve the cluster's file tree.

### Missing pieces

| Missing | Where | Notes |
|---|---|---|
| directory listing and file read over the session workdir | wrapper `/v1/sessions/{id}/files` | resolve, then refuse paths outside the workdir (symlinks included); entry and byte caps |
| PTY shell over WebSocket | wrapper `/v1/sessions/{id}/terminals` | reuse `PtyProcess` and its ring (`src/claude_code_wrapper/pty_proc.py:74`); FastAPI WebSockets need a WS library, which `uvicorn[standard]` already brings (`websockets`) |
| proxies | orchestrator `/api/v1/clusters/{id}/files`, `/terminals`, WebSocket relay | the api picks a ready agent and relays with the derived token; a WS client in the api (`websockets` 17.3 or `httpx-ws` 0.9.0) |
| Origin check on WS upgrade | orchestrator api | new `ORCH_ALLOWED_ORIGINS` |

### Security implications

- The UI is unauthenticated and protected only by source CIDR (README `## Security`). Anyone on the LAN who can send a chat prompt can already make an agent run arbitrary commands, so a shell adds no new capability in principle, but it removes the model as a filter and makes it interactive and instant.
- Cross-site WebSocket hijacking: browsers do not apply CORS to WebSocket upgrades, so a page from any origin open in a LAN browser can open `ws://orchestrator/...`. The server must validate the `Origin` header against an allowlist (OWASP WebSocket Security Cheat Sheet, https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html). A cross-origin `fetch` with an `application/json` body needs a CORS preflight that the api never grants; a WebSocket upgrade has no preflight. The cheat sheet: "Validate the Origin header on every handshake. Always use an explicit allowlist of trusted origins."
- Shell environment: the agent pod env carries `CLAUDE_CODE_OAUTH_TOKEN`, `CCW_AUTH_TOKEN` and `CCW_PEER_TOKEN` (`render.py:137-143`). Scrubbing them from the shell env is defence in depth only; the wrapper README `### Peer trust model` already states the agent uid can read them from `/proc/<pid>/environ`.
- Path confinement: the wrapper trust model allows any absolute workdir for mounted mode (README `## Trust model`); the file API must confine reads to the session workdir after `realpath`, refuse device files and cap sizes.
- Pods can reach the ingress (README `## Security`); keep `ingress.denySourceRanges` set to node IPs so agent pods cannot open shells on their siblings through it.
- ingress-nginx: "Support for websockets is provided by NGINX out of the box", but `proxy-read-timeout` and `proxy-send-timeout` default to 60 seconds; the docs suggest raising them above 3600 (https://kubernetes.github.io/ingress-nginx/user-guide/miscellaneous/). App-level pings every 20 s keep the session alive regardless.

## 3. Libraries (checked against the npm and PyPI registries on 2026-10-23)

| Need | Pick | Version | License | Fit |
|---|---|---|---|---|
| resizable panels | `react-resizable-panels` | 4.14.8 (2026-10-20) | MIT | peer react ^18 or ^19. v4 API: `Group` (`orientation`, `onLayoutChanged`, `groupRef`), `Panel` (`collapsible`, `collapsedSize`, `minSize`, `panelRef` with `collapse()`, `expand()`, `isCollapsed()`, `resize()`), `Separator`. Sizes: numbers are pixels, unit-less strings are percent. Source: https://github.com/bvaughn/react-resizable-panels README |
| terminal | `@xterm/xterm` | 6.0.0 (2025-12-22) | MIT | v6 breaking changes: canvas renderer addon removed (use DOM or WebGL), viewport and scrollbar reworked, `windowsMode` and `fastScrollModifier` removed (https://github.com/xtermjs/xterm.js/releases/tag/6.0.0) |
| terminal sizing | `@xterm/addon-fit` | 0.11.0 | MIT | call `fit()` from the Panel `onResize` |
| terminal transport | own protocol over `WebSocket` | - | - | `@xterm/addon-attach` 0.12.0 pipes raw bytes only and has no resize channel, so a small binary-data plus JSON-control protocol is simpler |
| tree view | `@mui/x-tree-view` `SimpleTreeView` / `RichTreeView` | 9.16.0 (2026-10-20) | MIT | peer `@mui/material` ^7.3 or ^9, matches the repo's MUI 9.5. Expansion, selection and label editing are Community; lazy loading, virtualization and drag reordering are Pro (`@mui/x-tree-view-pro`, commercial; https://mui.com/x/react-tree-view/). Lazy children are therefore loaded by hand on expansion |
| tree alternative | `react-arborist` | 4.0.1 | MIT | virtualized, but needs `react-dnd` peers and brings its own styling outside MUI |
| icons | `@mui/icons-material` | 9.5.0 | MIT | peer `@mui/material` ^9.5.0, exact match |
| tabs | MUI `Tabs` (`variant="scrollable"`) | in `@mui/material` 9.5 | MIT | no new dependency |
| WS client in the orchestrator api | `websockets` | 17.3 | BSD | already in the lock through `uvicorn[standard]`; `httpx-ws` 0.9.0 is the alternative |

Recommendation: react-resizable-panels plus MUI Tabs plus xterm.js 6 plus MIT `SimpleTreeView` with hand-rolled lazy loading. Every pick is MIT, React 19 compatible and MUI 9 compatible.

## 4. Live tree refresh

inotify fires only for changes made through the local kernel client; network filesystems such as Ceph have no server-side hook for it, so a watcher in one pod does not see writes from another (LWN, "Change notifications for network filesystems", 2022, https://lwn.net/Articles/896055/; medium confidence, no CephFS-specific doc found). The cluster event stream already carries every `tool_call` with `file_path` for Write, Edit and NotebookEdit (wrapper README `### tool_call`), which is a better invalidation signal; Bash side effects are covered by re-fetching expanded directories on each Bash `tool_result` plus a manual refresh.

## 5. Options considered for the terminal host

| Option | For | Against |
|---|---|---|
| A. wrapper terminal API, proxied by the api (recommended) | the workdir and tools are already in the pod, bearer auth and token derivation exist, no RBAC change | shells share the agent pod's resources and env |
| B. a per-cluster workspace pod mounting the PVC | isolates human shells from agent secrets and CPU | a new image and Service, reconciler work, a second PVC consumer |
| C. Kubernetes `pods/exec` | no wrapper change | the Role deliberately has no `pods/exec` (README `### RBAC`), and the api has no Kubernetes client by design |
