# web ui cluster tabs with filesystem chat and terminal panels design

## Summary

The agent-orchestrator web UI drops the left cluster ribbon for a top tab bar (one tab per cluster) with a hamburger menu, and each cluster tab becomes a three-panel workspace: filesystem tree, chat (the existing ChatView with an agents strip), and a multi-tab terminal. Two new backend surfaces carry it: the claude-code-wrapper gains a session-scoped file API (list, read) and a terminal API (HTTP lifecycle plus a WebSocket PTY), and the orchestrator api proxies both through one new module, guarded by a mandatory Origin allowlist. Every capability is a documented public API with an API-only end-to-end test (headless parity). The epic ends with the image and chart pins in agents-helmfile; apply and smoke are run by the user.

## Intent and why

The user wants one screen per cluster that shows what the agents changed on disk and lets them run commands beside the chat, and a navigation that scales past a handful of clusters better than a side ribbon (user request 2026-10-23, README Description). Today the UI has no view of the shared workdir and no shell; seeing a file or running `git status` means asking an agent to do it.

## Goals

- The ribbon aside (`frontend/src/layout/Shell.tsx` aside, `frontend/src/ribbon/Ribbon.tsx`, `ClusterRow.tsx`) is gone from `git ls-files`; a top tab bar shows one tab per cluster with state mark, slug and context gauge; New cluster and Discard are reachable from the bar; no Edit entry point remains in the UI.
- A hamburger button at the top left opens a drawer: every cluster (session) listed from the top, a settings section pinned to the bottom that renders the categories it is given (none in this epic).
- A cluster tab shows filesystem, chat and terminal panels split by draggable separators; minimize, maximize and restore follow the rules in D7; the layout persists per cluster in the browser; the phone layout shows one panel at a time with a three-way switch.
- The chat panel is ChatView with its agent filter chips replaced by an agents strip (pod, state, free since, own gauge, filter toggle).
- The terminal panel holds several shell tabs, each on a chosen agent pod (first ready agent preselected), over a WebSocket PTY rendered with xterm.js 6; shells survive tab switches and reloads and replay their scrollback on reattach.
- The filesystem panel shows the cluster workdir as a lazy tree (dotfiles and `.git` included, 2000 entries per page with a "more" row), refreshed from the event stream and by a manual refresh, with a read-only preview.
- Wrapper: `GET /v1/sessions/{id}/files`, `GET /v1/sessions/{id}/files/content`, `POST|GET /v1/sessions/{id}/terminals`, `DELETE /v1/sessions/{id}/terminals/{terminal_id}`, `WS /v1/sessions/{id}/terminals/{terminal_id}/attach`, each documented in the wrapper README and covered by an API-only e2e test on the real service.
- Orchestrator: `GET /api/v1/clusters/{cluster_id}/files`, `GET /api/v1/clusters/{cluster_id}/files/content`, `GET /api/v1/clusters/{cluster_id}/terminals`, `POST /api/v1/agents/{agent_id}/terminals`, `DELETE /api/v1/agents/{agent_id}/terminals/{terminal_id}`, `WS /api/v1/agents/{agent_id}/terminals/{terminal_id}/attach`, documented in the README (the WebSocket route by hand), in OpenAPI and `schema.d.ts`, with API-only tests against FakeWrapper and a kind e2e test.
- agents-helmfile pins the orchestrator chart and image and the wrapper image of this epic and sets `ORCH_ALLOWED_ORIGINS`.

## Non-goals

- No authentication or user accounts; the UI stays unauthenticated and LAN-only.
- No file editing, upload, rename or delete; no inotify.
- No keyboard attached to the Claude TUI PTY; terminals are separate shells.
- No chat or dispatch behaviour change.
- No Kubernetes `pods/exec` RBAC and no workspace pod.
- No removal of `PATCH /api/v1/clusters/{cluster_id}`, `patchCluster` or the ClusterForm edit mode: the cluster-presets epic removes that code. This epic removes only the Edit entry points from the UI.
- No Presets settings category (cluster-presets adds it to this epic's menu).
- No wrapper version tag or GitHub release; images are deployed by short sha.
- Running `helmfile apply`, `mise run smoke` or the kind e2e in this container: the user runs apply and smoke after the epic; the kind e2e runs in the orchestrator PR CI.

## Anti-goals

- A WebSocket route reachable from an arbitrary web page in a LAN browser (cross-site WebSocket hijacking).
- A file read that escapes the session workdir through `..`, an absolute path or a symlink.
- A slow terminal client that stalls the PTY reader or the wrapper event loop.
- The api gaining broad wrapper access: only the one proxy module may use the wrapper client and tokens.
- A regression in ChatView, dispatch or the existing `/api/v1` routes and tests.
- Shells or file reads that keep running after their session is destroyed or the service stops.

## Constraints

- Python only except the TypeScript frontend; services talk only through the queue or HTTP (WebSocket counts as HTTP upgrade).
- Test-first in every repo. Wrapper rules (`code/claude-code-wrapper/CLAUDE.md`): `uv run` always, plain ASCII, tests never use a real claude, only the fake-claude task edits `tests/conftest.py`, never write service files into a session workdir.
- Wrapper `tests/test_readme_api.py` scrapes routes and `ApiError` codes; every new error code needs an Errors table row and every new `LimitsConfig` key a Configuration reference row (`tests/test_readme_config.py`). Its `_walk` sees only `APIRoute`, so the WebSocket route needs its own README check.
- Orchestrator `tests/test_readme_api.py` requires a README `### \`METHOD /api/v1...\`` heading per HTTP route and `openapi.json` plus `frontend/src/api/schema.d.ts` regenerated (`uv run python -m agent_orchestrator.api.openapi > openapi.json`, then `npm run gen:api`). WebSocket routes are absent from OpenAPI; document them by hand under a `### \`WS /api/v1/...\`` heading, which the README route regex (GET|POST|PATCH|PUT|DELETE) ignores.
- `frontend/src/layout/designRules.ts`: no colour literals outside `theme.ts` (the xterm colour map lives there), no decorative Unicode, no `title=` on buttons, fontWeight 400/500 only.
- Verify commands in this container: orchestrator `uv run pytest -q -p no:cacheprovider <files>` plus the lint (testcontainers, dockerd running); task verifies spell the lint as `uv run ruff check . && uv run ruff format --check .` (what `mise run lint` runs in the Python repos), because the plan validator counts `mise run lint` as a whole suite; frontend `mise x node@24.20.0 -- npm --prefix frontend ci` first, then `run lint`, `test -- <file>`, `run build`, `run check:api`; wrapper targeted test files plus `mise run lint` (the full wrapper suite takes 13 minutes and `tests/test_manager.py::test_shutdown_stops_all` fails only in this container because PID 1 does not reap zombies; it is never a verify target).
- No cluster access here: helmfile apply, smoke and kind e2e cannot run; the kind test is verified by collection (`-m e2e --collect-only`) and runs in the PR CI `e2e` job.
- Merge order: the wrapper PR merges before `wrapper-sha-pin` runs; both product PRs merge before `deploy-pin` runs (D9).

## Decisions

### D1: Wrapper file API shape and confinement
`GET /v1/sessions/{id}/files?path=<rel>&offset=<n>` lists one directory and `GET /v1/sessions/{id}/files/content?path=<rel>` reads one file, for any session whose workdir exists on disk (live or persisted). `path` is relative to the session workdir (empty means the root). One helper in a new `src/claude_code_wrapper/files.py` resolves every path with `realpath` and refuses anything outside the realpath of the workdir (`invalid_path`, 400), so `..`, absolute paths and escaping symlinks fail; entries are listed with type `dir`, `file`, `symlink` or `other` and a symlink is followed only when its target stays inside. Listing: directories first, then names, `limits.files_max_entries` (2000) per page with `next_offset` when more remain; response carries the absolute `root` so clients map event `file_path` values onto the tree. Content: `kind` `text` (UTF-8, no NUL in the first 8 KiB, at most `limits.file_preview_max_bytes` 1 MiB, content inline), `binary` (size and guessed mime only) or `too_large` (size only); FIFOs, sockets and devices are refused with `not_a_file` and never opened. Alternatives: a recursive tree endpoint (rejected: unbounded on `node_modules`), reading through the orchestrator PVC (rejected: the api has no mount and must not get one). (my call)

### D2: Terminal WebSocket protocol
Binary frames carry PTY bytes in both directions; text frames carry JSON control: client `{"type":"resize","cols":C,"rows":R}` and `{"type":"ping"}`, server `{"type":"pong"}` and `{"type":"exit","code":N}` (then close 1000). On attach the server first sends the scrollback ring (256 KiB) as binary frames, then live output. Several clients may attach to one terminal: each gets a bounded queue fed by one PTY reader; a client whose queue overflows is closed with 1013 instead of blocking the PTY. Frames over `limits.terminal_max_frame_bytes` (64 KiB) close with 1009. The browser pings every 20 s to keep ingress-nginx from idling the connection. Alternative: `@xterm/addon-attach` raw bytes (rejected: no resize channel). (my call)

### D3: Terminal lifecycle and identity
A terminal belongs to the wrapper process and is created under a session, which gives it its cwd (the session workdir, confined by the D1 helper) and its lifetime: it closes when its session is destroyed and at service shutdown (`SessionManager.shutdown`). No new SSE event types are added (the `event-types` contract is untouched). Terminal ids are `term_<12 hex>`. (my call)

### D4: Orchestrator proxy routes and error mapping
Files are cluster-scoped (`/api/v1/clusters/{cluster_id}/files`, `/files/content`, optional `agent_id`, default the first ready agent by ordinal, since every agent mounts the same RWX workdir). Terminals are agent-scoped like the existing agent commands (`POST /api/v1/agents/{agent_id}/terminals`, `DELETE /api/v1/agents/{agent_id}/terminals/{terminal_id}`, `WS .../attach`), with a cluster-wide `GET /api/v1/clusters/{cluster_id}/terminals` that fans out to every ready agent and reports unreachable ones in `unavailable_agents`. The proxy resolves `agents.url` and `agents.session_id` from the database (no Kubernetes import) and the token with `tokens_for(settings, cluster_id).auth`. Wrapper 4xx answers pass through with their status and code; a transport failure is 502 `wrapper_unreachable`, a wrapper 5xx is 502 `wrapper_error`, no ready agent or an agent without a session is 409 `agent_not_ready`, an unset `ORCH_MASTER_KEY` is 503 `unavailable` on these routes only. (my call)

### D5: Origin rule
A pure ASGI check in `api/origin.py` applies to every WebSocket upgrade, and a dependency from the same module applies to `POST` and `DELETE` on the terminal routes. A request without an `Origin` header passes (non-browser clients; browsers always send Origin on WebSocket upgrades and on cross-origin POST/DELETE); an `Origin` of `null` or one not in `ORCH_ALLOWED_ORIGINS` is refused: WebSocket close 1008 before accept, HTTP 403 `forbidden_origin`. An empty `ORCH_ALLOWED_ORIGINS` refuses every Origin-bearing upgrade (fail closed). Comparison is exact on scheme, host and port after lower-casing. It runs alongside the existing `SourceAllowlist`, which keeps checking the direct peer. (my call)

### D6: WebSocket client in the orchestrator api
The relay uses `websockets` (17.3, already in `uv.lock` through `uvicorn[standard]`), now declared as a direct dependency. Alternative `httpx-ws` 0.9.0 (rejected: one more dependency for the same job). (my call)

### D7: Panel layout rules and persistence
`react-resizable-panels` 4 `Group` with three collapsible `Panel`s and two `Separator`s, default 25/45/30. Minimize collapses a panel to a narrow vertical strip with its name and a restore button; at most two panels are minimized (the last expanded panel has no minimize control); maximize collapses the other two; double-click on a separator restores 25/45/30. Layout and collapsed set persist per cluster id in localStorage through `frontend/src/layout/storage.ts`, whose reads and writes never throw. Layout is browser-only presentation state with no API; headless parity covers capabilities, not layout. (my call)

### D8: Filesystem refresh plumbing
The filesystem panel opens its own event stream subscription (`openStream` on the cluster events URL with `tool_call` and `tool_result`) instead of lifting the private stream out of `useClusterChat`, so ChatView stays untouched. A `tool_call` of Write, Edit or NotebookEdit re-fetches the parent directory of `tool_input.file_path` (mapped through the listing `root`) when that directory is loaded; a `tool_result` of Bash re-fetches every expanded directory, debounced to one pass per second. (my call)

### D9: Pins, merge order and deploy
Merge order: wrapper PR, then `wrapper-sha-pin` pins the orchestrator `claude-code-wrapper` dev dependency, `uv.lock`, `e2e/agent-test.Dockerfile` (`BASE_IMAGE`, `WRAPPER_SHA`) and README `## Images` to the wrapper main merge commit (the precedent of `container-images-ci`); the orchestrator PR merges after its CI e2e passes; `deploy-pin` then pins agents-helmfile to both main merge sha7 values (precedent `deploy-pin-d5a7738`) and sets `ORCH_ALLOWED_ORIGINS: https://agents.szymonrichert.pl`. The orchestrator supplies the sha values with `ticket.py amend` when it reaches each pin task; a pin task whose merge does not exist yet reports `blocked` with the orchestrator as `whoCanClear`. Apply and smoke are run by the user after the epic. (my call)

### D10: Tab selection default
When no tab is selected and clusters exist, the first cluster by slug is selected; a discarded or vanished selected cluster falls back the same way. (my call)

### D11: Shell process
The shell is `/bin/bash -l` (falling back to `/bin/sh -l` when bash is absent) with `TERM=xterm-256color`, started under `PtyProcess` in the session workdir with the service environment minus the scrubbed secrets. Terminals are capped per wrapper process (`limits.terminals_max` 8), which is per pod. (my call)

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| research-code-internal | ran (discovery/reuse.md, shared-parts map) | reuse `PtyProcess`, `Ring`, `safe_write_files` pattern, `tokens_for`, `SourceAllowlist`, `openStream`, `useClusters`, `ChatView`, `FakeWrapper` (discovery/reuse.md Plan inputs) | a second PTY or ring; a new token scheme |
| research-docs | ran (research.md section 3, npm and PyPI registries 2026-10-23) | react-resizable-panels 4.14.8 v4 API (`Group`, `Panel`, `Separator`, https://github.com/bvaughn/react-resizable-panels); `@xterm/xterm` 6.0.0 without canvas renderer (https://github.com/xtermjs/xterm.js/releases/tag/6.0.0); `@mui/x-tree-view` 9.16.0 MIT `SimpleTreeView` with hand-rolled lazy loading (https://mui.com/x/react-tree-view/); `@mui/icons-material` 9.5.0; ingress-nginx WebSocket timeouts (https://kubernetes.github.io/ingress-nginx/user-guide/miscellaneous/) | `react-arborist` (react-dnd peers, styling outside MUI); `@xterm/addon-attach` (no resize channel) |
| research-code-external | ran (research.md sections 2 and 5) | OWASP WebSocket cheat sheet: validate Origin on every handshake with an explicit allowlist (https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html) | workspace pod (option B) and `pods/exec` (option C), research.md section 5 |
| research-papers | skipped: UI and infra plumbing, no algorithmic core | none | none |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| discovery/reuse.md reuse | PtyProcess - W/pty_proc.py:PtyProcess | pty-resize-and-raw-ring, terminal-registry |
| discovery/reuse.md reuse | Ring - W/ring.py:Ring | pty-resize-and-raw-ring, terminal-registry |
| discovery/reuse.md reuse | BASE_ENV, passthrough_names - W/session.py:BASE_ENV | terminal-registry (scrub list; the shell derives from `manager.service_env`) |
| discovery/reuse.md reuse | safe_write_files pattern - W/workdir.py:safe_write_files | wrapper-file-api |
| discovery/reuse.md reuse | LimitsConfig - W/config.py:LimitsConfig | wrapper-file-api, terminal-registry |
| discovery/reuse.md reuse | require_auth, ApiError - W/api/auth.py:require_auth | wrapper-file-api, terminal-websocket-api |
| discovery/reuse.md reuse | tokens_for - O/tokens.py:tokens_for | wrapper-proxy-seam |
| discovery/reuse.md reuse | pod_url, Agent.url - O/k8s/render.py:pod_url | wrapper-proxy-seam (reads the stored `agents.url`, never imports k8s) |
| discovery/reuse.md reuse | WrapperClient - O/wrapper/client.py:WrapperClient | wrapper-proxy-seam |
| discovery/reuse.md reuse | SourceAllowlist - O/api/allowlist.py:SourceAllowlist | origin-allowlist (kept; Origin check added beside it) |
| discovery/reuse.md reuse | Settings CsvList pattern - O/settings.py:Settings | origin-allowlist |
| discovery/reuse.md reuse | validate_spec, fill_resource_defaults, validate_slug - O/spec.py | rejected: presets epic only |
| discovery/reuse.md reuse | run_migrations - O/db/migrate.py | rejected: presets epic only, no migration here |
| discovery/reuse.md reuse | openStream - F/api/stream.ts:openStream | fe-filesystem-panel |
| discovery/reuse.md reuse | useClusters, sortedAgents - F/ribbon/useClusters.ts | fe-top-bar, fe-retire-ribbon, fe-agents-strip, fe-terminal-panel |
| discovery/reuse.md reuse | ChatView - F/chat/ChatView.tsx | fe-panel-workspace, fe-agents-strip |
| discovery/reuse.md reuse | ConfirmDialog - F/layout/ConfirmDialog.tsx | fe-retire-ribbon (via DiscardClusterDialog) |
| discovery/reuse.md reuse | clusterSpecForm helpers - F/clusters/clusterSpecForm.ts | rejected: presets epic only |
| discovery/reuse.md reuse | FakeWrapper - tests/fakes/fake_wrapper.py | file-proxy-routes, terminal-proxy-routes, terminal-ws-relay |
| discovery/reuse.md do-not-build | WebSocket timeouts in deployed helmfile values (already 3600) | origin-allowlist (chart README note only), deploy-pin (no timeout change) |
| discovery/reuse.md do-not-build | chart wiring for new ORCH_* settings | origin-allowlist (README only; values `env:` carries it) |
| discovery/reuse.md do-not-build | a separate PTY or ring | pty-resize-and-raw-ring |
| discovery/reuse.md do-not-build | a new token scheme | wrapper-proxy-seam |
| discovery/reuse.md do-not-build | a WebSocket peer allowlist | origin-allowlist |
| discovery/reuse.md fix-as-ac | require_auth typed to Request (W/api/auth.py:21) | terminal-websocket-api |
| discovery/reuse.md fix-as-ac | `_check_spec` private | rejected: presets epic only |
| discovery/reuse.md fix-as-ac | httpx ASGITransport cannot test WebSocket | terminal-ws-relay, kind-e2e-workspace |
| discovery/reuse.md fix-as-ac | websockets undeclared in the orchestrator pyproject | terminal-ws-relay |
| discovery/reuse.md fix-as-ac | PATCH retirement leftovers | rejected: presets epic removes PATCH; this epic removes only the Edit entry points (fe-retire-ribbon) |
| discovery/reuse.md fix-as-ac | default preset seed idempotent | rejected: presets epic only |
| discovery/reuse.md ideas | adopted: SSE heartbeat cadence for the 20 s terminal ping | fe-terminal-socket |
| discovery/reuse.md ideas | adopted: arm_slug sanitising for preset-name slugs | rejected: presets epic only |
| discovery/reuse.md ideas | rejected: inotify for tree refresh | fe-filesystem-panel (event-stream refresh, D8) |
| discovery/reuse.md ideas | open: frontend storage.ts wrapper must be built | fe-deps-and-storage |
| discovery/wrapper.md | require_auth fails on WebSocket routes; retype to HTTPConnection | terminal-websocket-api |
| discovery/wrapper.md | Ring has no raw accessor; PtyProcess has no resize | pty-resize-and-raw-ring |
| discovery/wrapper.md | no app lifespan; close terminals from manager shutdown | terminal-registry |
| discovery/wrapper.md | README WebSocket routes not auto-enforced | terminal-websocket-api |
| discovery/orchestrator-backend.md | test_api_never_imports_k8s_or_wrapper and MEMORY D5 | wrapper-proxy-seam |
| discovery/orchestrator-backend.md | ORCH_ALLOWED_ORIGINS plus e2e values | origin-allowlist |
| discovery/orchestrator-backend.md | wrapper SHA in pyproject, uv.lock, agent-test.Dockerfile | wrapper-sha-pin |
| discovery/orchestrator-backend.md | README `### Ingress` timeouts | origin-allowlist |
| discovery/frontend.md | new deps and package-lock | fe-deps-and-storage |
| discovery/frontend.md | retire Ribbon.test.tsx, ribbon test ids, Edit item, Ribbon wiring test | fe-retire-ribbon |
| discovery/frontend.md | Vite dev proxy lacks `ws: true` | fe-deps-and-storage |
| discovery/frontend.md | xterm colours in theme.ts | fe-terminal-panel |
| discovery/frontend.md | jsdom lacks ResizeObserver, canvas, WebSocket | fe-panel-workspace, fe-terminal-socket, fe-terminal-panel (mock in tests) |
| research.md section 4 | inotify blind to other CephFS clients | fe-filesystem-panel |
| research.md section 2 | scrub CLAUDE_CODE_OAUTH_TOKEN, CCW_* from the shell | terminal-registry |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 Wrapper file API shape and confinement | wrapper-file-api, wrapper-workspace-e2e |
| D2 Terminal WebSocket protocol | pty-resize-and-raw-ring, terminal-websocket-api, terminal-ws-relay, fe-terminal-socket |
| D3 Terminal lifecycle and identity | terminal-registry, terminal-websocket-api |
| D4 Orchestrator proxy routes and error mapping | wrapper-proxy-seam, file-proxy-routes, terminal-proxy-routes |
| D5 Origin rule | origin-allowlist, terminal-proxy-routes, terminal-ws-relay |
| D6 WebSocket client in the orchestrator api | terminal-ws-relay |
| D7 Panel layout rules and persistence | fe-deps-and-storage, fe-panel-workspace |
| D8 Filesystem refresh plumbing | fe-filesystem-panel |
| D9 Pins, merge order and deploy | wrapper-sha-pin, kind-e2e-workspace, deploy-pin |
| D10 Tab selection default | fe-retire-ribbon |
| D11 Shell process | terminal-registry |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `pty-resize` | pty-resize-and-raw-ring | terminal-registry | `code/claude-code-wrapper/src/claude_code_wrapper/pty_proc.py` |
| `ring-raw-snapshot` | pty-resize-and-raw-ring | terminal-registry | `code/claude-code-wrapper/src/claude_code_wrapper/ring.py` |
| `wrapper-path-confinement` | wrapper-file-api | terminal-registry | `code/claude-code-wrapper/src/claude_code_wrapper/files.py` |
| `wrapper-files-api` | wrapper-file-api | file-proxy-routes, wrapper-workspace-e2e | `code/claude-code-wrapper/README.md` |
| `terminal-registry` | terminal-registry | terminal-websocket-api | `code/claude-code-wrapper/src/claude_code_wrapper/terminals.py` |
| `wrapper-terminals-api` | terminal-websocket-api | terminal-proxy-routes, terminal-ws-relay, wrapper-workspace-e2e | `code/claude-code-wrapper/README.md` |
| `origin-allowlist` | origin-allowlist | terminal-proxy-routes, terminal-ws-relay | `code/agent-orchestrator/src/agent_orchestrator/api/origin.py` |
| `workspace-proxy-module` | wrapper-proxy-seam | file-proxy-routes, terminal-proxy-routes, terminal-ws-relay | `code/agent-orchestrator/src/agent_orchestrator/api/workspace.py` |
| `orch-files-api` | file-proxy-routes | fe-filesystem-panel, kind-e2e-workspace | `code/agent-orchestrator/README.md` |
| `orch-terminals-api` | terminal-proxy-routes | fe-terminal-socket, kind-e2e-workspace | `code/agent-orchestrator/README.md` |
| `fake-wrapper-terminals` | terminal-proxy-routes | terminal-ws-relay | `code/agent-orchestrator/tests/fakes/fake_wrapper.py` |
| `orch-terminal-ws` | terminal-ws-relay | fe-terminal-socket, kind-e2e-workspace | `code/agent-orchestrator/README.md` |
| `wrapper-main-pin` | wrapper-sha-pin | kind-e2e-workspace | `code/agent-orchestrator/pyproject.toml` |
| `fe-deps` | fe-deps-and-storage | fe-top-bar, fe-panel-workspace, fe-filesystem-panel, fe-terminal-socket, fe-terminal-panel | `code/agent-orchestrator/frontend/package.json` |
| `fe-storage` | fe-deps-and-storage | fe-panel-workspace | `code/agent-orchestrator/frontend/src/layout/storage.ts` |
| `fe-sessions-menu` | fe-top-bar | fe-retire-ribbon | `code/agent-orchestrator/frontend/src/layout/SessionsMenu.tsx` |
| `fe-workspace-slots` | fe-panel-workspace | fe-filesystem-panel, fe-terminal-panel | `code/agent-orchestrator/frontend/src/layout/Workspace.tsx` |
| `fe-terminal-socket` | fe-terminal-socket | fe-terminal-panel | `code/agent-orchestrator/frontend/src/terminal/terminalSocket.ts` |

Cross-epic contracts in `docs/plans/contracts.json`: `wrapper-files-api`, `wrapper-terminals-api` (consumer agent-orchestrator), `orch-allowed-origins` (consumer agents-helmfile) and `orch-settings-menu` (consumer cluster-presets: its Presets category is one entry in the `settingsCategories` prop of `SessionsMenu`; it also removes PATCH and the ClusterForm edit code this epic leaves in place).

## Review focus

- Path confinement in `files.py`: symlink escapes, `..`, absolute paths, FIFOs and devices (never opened), size caps enforced before reading the whole file.
- Terminal fan-out and reaper in `terminals.py`: no unbounded queue, no PTY stall from a slow client, the reaper never kills an attached shell, every shell closed on session destroy and shutdown, the env scrub.
- `require_auth` on WebSocket: an unauthenticated upgrade is denied before accept.
- Origin rule: WebSocket upgrades from unlisted origins never reach the relay; `null` refused; absent Origin allowed only as D5 says.
- The import whitelist: exactly one api module (`api/workspace.py`) may import `agent_orchestrator.wrapper` and use tokens.
- The relay: both directions closed when either side closes, close codes propagated, no task leak per connection.
- Frontend: retirement tests assert on `git ls-files`; no Edit entry point anywhere; ChatView behaviour unchanged apart from the agents strip.

## Left to the builder

- Internal module layout inside the named files (helper names, dataclasses), as long as the routes, fields, error codes and config keys named in the tasks hold.
- Exact visual sizes of the minimized strip and tab labels within designRules.
- Whether `layout/Shell.tsx` is rewritten or deleted, as long as no aside remains and the phone top bar works.
- The reconnect backoff curve of the terminal socket within 1 to 30 s.
- Mocking strategy for `react-resizable-panels`, `@xterm/xterm` and `@mui/x-tree-view` under jsdom.

## Assumptions and unknowns

- `react-resizable-panels` 4 and `@xterm/xterm` 6 need mocks under jsdom (no ResizeObserver, no canvas): confirmed by the first frontend task that imports them; tests mock them like `react-virtuoso`.
- Starlette `TestClient` runs the app on its own loop, which conflicts with the async psycopg pool fixture: the relay test serves the api with uvicorn on a loopback port in the test loop and connects with the `websockets` client (probe in terminal-ws-relay).
- The wrapper image keeps `/bin/bash` and `/etc/profile.d/mise-shims.sh` (wrapper Dockerfile:81): checked by the wrapper e2e test, which runs a login shell.
- Harbor publishes `claude-code-wrapper:<sha7>` and chart `0.1.0-main.<sha7>` on each main merge: checked by the pin tasks before pinning (`helm show chart` or registry digest where credentials allow; otherwise the user's apply surfaces it).

## Open questions
- Q1: Is a "session" in the request one orchestrator cluster, with every cluster shown as a tab (no closing, scrollable bar, ordered by slug)? [recommended: yes, a tab per cluster, same set the ribbon lists today]
- Q2: Where do the per-agent rows (pod, state, free since, own gauge) go once the ribbon is gone? [recommended: a compact agents strip in the chat panel header, merged with the agent filter chips]
- Q3: Where does a terminal run? [recommended: a shell in a chosen agent pod, served by the wrapper and proxied by the orchestrator api; not a separate workspace pod, not Kubernetes pods/exec]
- Q4: Does "terminal allows for scheduling multiple tabs" mean several concurrent terminal tabs, rather than queued or scheduled commands? [recommended: yes, several concurrent shells as tabs, each with its own pod choice]

## Irreversible operations in scope

- Deleting `frontend/src/ribbon/Ribbon.tsx`, `ClusterRow.tsx`, `Ribbon.test.tsx`, `AgentRow.tsx` and `frontend/src/chat/AgentFilter.tsx`: git history keeps them; pinned by retirement tests.
- Live shells on agent pods: an interactive shell can change the shared workdir like any agent; covered by the user's Q7 answer (LAN-only, Origin allowlist).
- Deploy (helmfile apply) is run by the user after the epic, not by this plan.
