# Discovery brief (context pack)

## Environment (cloud container)
- dockerd runs here; orchestrator DB tests use testcontainers.
- Use mise's node 24: mise x node@24.20.0 -- npm --prefix frontend ... (node 22 first on PATH). Run npm ci in frontend once per worktree.
- Wrapper: tests/test_manager.py::test_shutdown_stops_all and tests/test_container.py::test_example_config_validates_in_image fail only in this container (PID 1 does not reap zombies; Docker Hub 429). CI on main is green.
- agents-helmfile: 5 tests fail here on network policy (harbor.szymonrichert.pl, cloudnative-pg.github.io blocked).
- No cluster access: kind e2e verified by collection only.


## Discovery: claude-code-wrapper (at ca2ddf3)

Paths relative to `code/claude-code-wrapper/`. No LSP tool available; mapped with grep/read plus two scratch probes.

## Shape and rules

- Package `src/claude_code_wrapper/`; public API in `api/` (`app.py`, `auth.py`, `errors.py`, `sessions.py`, `turns.py`, `events.py`, `commands.py`, `peers.py`, `redaction.py`). Tests flat in `tests/test_<module>.py`; fake claude in `tests/fake_claude/`.
- No `AGENTS.md`, `MEMORY.md` or `ROADMAP.md` exist. Rules live in `CLAUDE.md`: test-first, always `uv run`, plain ASCII, tests never use a real claude, "only the fake-claude task edits `tests/conftest.py`", "never write service files into a session workdir". `docs/plans/contracts.json` lists cross-epic contracts.

## Entrypoint and /v1 routing

- `service.py:run_service` builds `SessionManager(service_env=dict(os.environ))` (`service.py:235`), then `create_app` and the internal app, served by uvicorn with `lifespan="off"` (`service.py:140`). Shutdown calls `manager.shutdown()` (`service.py:267`); there is no app lifespan, so any terminal registry must be closed from there.
- `api/app.py:create_app`: `v1 = APIRouter(prefix="/v1", dependencies=[Depends(require_auth)])` then `include_router` per module (`app.py:71-76`). A new module = new `router = APIRouter()` included here. 
- `api/auth.py:require_auth(request: Request)` compares `app.state.auth_token` with hmac. **Probe result: on a WebSocket route under `v1` it fails with `TypeError: require_auth() missing ... 'request'`** (FastAPI 0.151 only injects `Request` for HTTP). Retyping the param to `starlette.requests.HTTPConnection` works for both; an `ApiError` raised then becomes a `WebSocketDenialResponse` (probed).
- Errors: `api/errors.py:ApiError(status, code, message)` and `install_handlers`; envelope `{"error":{"code","message"}}`, redacted. Handlers are HTTP-only; inside an accepted WebSocket, errors must be close codes or JSON control frames.

## Session workdir resolution

- `manager.get(sid)["workdir"]` (`manager.py:352`, `_compose` at `manager.py:1438`) returns the workdir for live and persisted sessions; unknown/ill-formed ids raise `SessionNotFound` (404 via `_read_meta`, `manager.py:1240`, regex `ses_[0-9a-f]{12}`). Live: `_Active.workdir` (`manager.py:217`).
- Workdir may be any absolute path in mounted mode (`workdir.py:prepare_workdir:84`).
- Existing confinement precedent: `workdir.py:safe_write_files:173` (realpath root, `is_relative_to`, `FileWriteError("invalid_path"|"too_large")`).

## PtyProcess and Ring

- `pty_proc.py:PtyProcess(ring_capacity=64KiB)`: `start(argv, cwd, env, rows=50, cols=200, on_output, on_exit)` once; `write(bytes)`, `paste`, `send_prompt`; `close(grace=5.0)` (SIGTERM group, close fd, SIGKILL after grace; idempotent); `alive`, `returncode`, `pid`, `ring`. `setsid` + controlling tty, so job control works.
- Model: pure asyncio, no threads. `loop.add_reader` on the non-blocking master, `READ_SIZE=65536`; writes serialised by one `asyncio.Lock`; exit watched by polling (`EXIT_POLL_SECONDS=0.05`). `on_output` is a single callback, sync or coroutine (coroutines are `ensure_future`d: no backpressure).
- Gaps for a shell: no `resize()` (only module-level `_set_winsize(fd, ...)`, `pty_proc.py:57`, used on the slave at start); one output subscriber only.
- `ring.py:Ring`: thread-locked bytearray of newest `capacity` bytes, `written` counter. Public readers are ANSI-stripped (`text`, `tail`, `contains`); **no raw-bytes accessor**, so replay needs one added. Reusable at 256 KiB.
- Other user: `session.py:_spawn:522`.

## Env

- Claude child env is allow-listed by `session.py:build_env:232` (`BASE_ENV` at `session.py:80`). The shell will instead derive from `manager.service_env`, which holds `CCW_AUTH_TOKEN`, `CCW_PEER_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN` when set; `CCW_HOOK_TOKEN` is per-session, claude env only. Login shell in the image: `/etc/profile.d/mise-shims.sh` re-adds mise shims (`Dockerfile:81`); user `agent`, `/bin/bash`.

## Streaming precedent

- No WebSocket anywhere. SSE: `api/events.py:events` (`StreamingResponse`, subscribe-before-replay, heartbeat via `limits.sse_heartbeat_seconds`). `websockets 17.3` and `uvicorn 0.54` are already locked.

## Config

- `config.py`, pydantic `_Model(extra="forbid")`. Caps live in `LimitsConfig` (`config.py:681`); `Config.limits`. Note `limits.max_file_bytes` already means turn files (262144). Every key needs a README `## Configuration reference` row with the matching default (`tests/test_readme_config.py:98,107`).

## Events

- `events.py:EVENT_TYPES` (`events.py:20`), `append` rejects unknown types. None for terminals or files. Adding one requires a README `## Events (SSE)` H3 (`tests/test_readme_api.py`) and touches the `event-types` contract in `docs/plans/contracts.json`.

## README contract

- H2s: Trust model, Architecture, API reference (`### \`METHOD /v1/...\`` per route, `{id}` for session id), Events (SSE), Hooks, Errors (table `| \`code\` | status | meaning |`), Configuration reference. `tests/test_readme_api.py` enforces routes, event types and error codes scraped from `ApiError(..., "code"` in `api/*.py`; its `_walk` collects only `APIRoute`, so WebSocket routes are not auto-enforced. Trust model phrases are pinned (`test_trust_model_and_callback_contract_documented`).

## Tests

- API tests: stub manager + `TestClient` (`tests/test_api_auth.py`) or `httpx.ASGITransport` (`tests/test_api_events.py:make`); WebSocket tests need `TestClient.websocket_connect`.
- PTY tests: `tests/test_pty_proc.py` `spawn` fixture runs real children via `py(code)` (`sys.executable -I -c`) in `tmp_path`, polls with `wait_until`.
- `make_spec` is a local helper in `tests/test_session_boot.py:93`; `world`, `ccw_service`, `fake_claude_bin` fixtures in `tests/conftest.py:250-310`.

## Release

- `pyproject.toml` version `0.1.0` static; no CHANGELOG; zero git tags or releases. `build.yaml` on main pushes `harbor.szymonrichert.pl/containers/claude-code-wrapper:<shortsha>`; `release.yaml` on `vX.Y.Z` retags that sha. Deployed today by sha: `agents-helmfile/values/agent-orchestrator/common.yaml:7,25` (`:ca2ddf3`).

## Verify (from `mise.toml`)

- `mise run lint` = `uv run ruff check . && uv run ruff format --check .`
- `mise run test` = `uv run pytest` (whole suite, slow); `mise run precommit` = CI pre-commit. No typechecker configured.
- Targeted (76 passed, 13.2s, run here): `uv run pytest tests/test_pty_proc.py tests/test_ring.py tests/test_readme_api.py tests/test_api_auth.py tests/test_workdir.py`; add `tests/test_readme_config.py tests/test_config.py tests/test_api_events.py`.

## Plan inputs

- Reuse: `PtyProcess` (start/write/close/exit callback), `Ring` (capacity 256 KiB), `ApiError` envelope, `manager.get(sid)["workdir"]`, `safe_write_files` confinement pattern, `manager.service_env`.
- Must change: `api/auth.py:require_auth` param to `HTTPConnection` (else any `/v1` WebSocket 500s); add `Ring` raw snapshot; add `PtyProcess.resize(rows, cols)`; fan-out of `on_output` to attached sockets via bounded queues.
- New code: `src/claude_code_wrapper/api/files.py` (routes) + a confinement helper (in `workdir.py` or new `files.py`); `src/claude_code_wrapper/terminals.py` (registry: max 8, reaper 15 min after last detach, env scrub, close-all called from `manager.shutdown` or `run_service`) + `api/terminals.py` (create/list/close HTTP, WebSocket attach); caps in `LimitsConfig` with distinct names; register routers in `api/app.py:71-76`.
- Tests: `tests/test_api_files.py`, `tests/test_terminals.py`, `tests/test_api_terminals.py`, extend `tests/test_pty_proc.py`, `tests/test_ring.py`, and add a README check for WebSocket routes.
- Docs/release: README API H3s, Errors and Configuration rows, Trust model note; first `vX.Y.Z` tag after main builds, then bump the `agents-helmfile` image.
- Unknowns: whether terminals/files work for stopped sessions or close on session destroy; whether a terminal is tied to a live session at all (design call).

## Discovery: agent-orchestrator backend and chart (epics A web-ui, B presets)

Mapped at agent-orchestrator d5a7738 (research.md line numbers, from 3004ed3, are stale). Paths relative to `code/agent-orchestrator/`. No LSP tool available.

## App and routers

- `src/agent_orchestrator/api/app.py:create_app` (23-77): routers `clusters`, `messages`, `streams` (all `APIRouter(prefix="/api/v1")`) at 56-58; SPA mounted at `/` (73-74, `api/spa.py:SpaStaticFiles` 404s `api/*`); `SourceAllowlist` last (76).
- The middleware is `api/allowlist.py:SourceAllowlist`, not `AllowlistMiddleware`. Pure ASGI over `http` and `websocket` scopes; a disallowed WS peer gets `websocket.close` 1008 before accept (45-46). Reads `scope["client"]` only, never headers.
- `uvicorn[standard]` brings `websockets` 17.3 and `wsproto` (uv.lock); `httpx` 0.28.1 is a direct dep. No WS client lib (`httpx-ws`) and no WebSocket route anywhere.
- Errors: `api/errors.py` `ApiError`, `{"error":{code,message}}`; 405 maps to `bad_request`.

## Reaching wrapper pods today

- api never does: README `## Architecture` table says api "never calls wrappers or Kubernetes"; MEMORY D5 says "the api never holds wrapper tokens". Test `tests/test_api_clusters.py:test_api_never_imports_k8s_or_wrapper` (212-231) bans `agent_orchestrator.k8s|wrapper|reconciler` imports in `api/*.py`. Epic A must amend this test and MEMORY, or keep proxy code free of those imports.
- `wrapper/client.py:WrapperClient(base_url, token, http=None)`: httpx, `Authorization: Bearer`, `_url` = `{base}/v1{path}`, errors `WrapperError`/`WrapperUnreachable`. Built in `dispatcher/loop.py:_wrapper` (54-64), `ingester/loop.py:_default_factory` (245).
- Pod URL: `k8s/render.py:pod_url` = `http://<pod>.agent-<slug>.<ns>.svc.<domain>:<wrapper_port>`; stored by the reconciler in `agents.url`, plus `agents.session_id`. The api can read them via `db/agents.py:get_agent`/`list_agents` without importing k8s. `db/views.py:agent_rows` does not select url/session_id.
- Token: `tokens.py:tokens_for(settings, cluster_id).auth` (HMAC of `ORCH_MASTER_KEY`), via `Settings.require_master_key`. Chart already gives every Deployment `ORCH_MASTER_KEY` (`templates/_config.tpl:agent-orchestrator.env` 86-97, used at `deployment.yaml:56,71`).

## Settings

`settings.py:Settings(BaseSettings)`, `env_prefix="ORCH_"`, flat fields 57-124; CSV lists are `CsvList` plus `_split` validator (145); per-field `@field_validator`s. `test_settings.py:test_env_names_documented_in_readme` requires every field as `` `ORCH_X` `` in README `## Configuration` table. `ORCH_WRAPPER_PORT`, `ORCH_CLUSTER_DOMAIN`, `ORCH_MASTER_KEY` "Read by" columns need api added.

## Migrations

`db/migrate.py:run_migrations`: files `NNNN_name.sql` (`_NAME` 4 digits), sorted, each in its own transaction, recorded in `schema_migrations`, session advisory lock; `orch migrate` initContainer. Only `0001_init.sql` exists; next is `0002_*.sql`. Idempotency is by version row only, so seed with `INSERT ... ON CONFLICT DO NOTHING`. `tests/test_migrations.py:41-53` asserts `versions == ["0001"]` and a `TABLES` set; both change.

## Clusters (epic B)

- `db/clusters.py`: `Cluster` dataclass (32-41, needs preset fields), `_from_row`, `_dump`, `create(conn, slug, spec)` (71), `get`, `get_by_slug`, `list_clusters`, `count_active`, `update_spec` (105-121, only caller PATCH), `request_delete`, `set_status`, `purge`. `ClusterDeleting` used only by `update_spec`/PATCH.
- Single writer: clusters written by api; reconciler writes `status`, `observed_generation`, deletes row (README 287-300). A `presets` row needs a README writer entry (api) and `## Data model` row.
- `api/clusters.py`: `_check_spec(spec, settings, stored=None)` (82-90) = `spec.validate_spec` then `spec.fill_resource_defaults` (write-time fill); `create_cluster` POST (131-153, advisory `_CREATE_LOCK`, `max_clusters` 409, `ClusterExists` 409); `patch_cluster` (169-187). `validate_spec(..., stored)` param exists only for PATCH (spec.py:185-206).
- `spec.py`: `validate_slug` (51-55: DNS-1123, max `SLUG_MAX=40`, `orchestrator*` reserved), `ClusterSpec` (97-112, `replicas` default 1). Generated slug must fit 40 and dodge the reserved prefix.
- `api/schemas.py`: `CreateCluster` (14-18, `extra="forbid"`, `spec` defaulted), `PatchCluster` (21-24), `ClusterView` (37-46).
- PATCH removal touches `tests/test_api_clusters.py` 88-97, 110, 353-367, 452-457, 460-482; `tests/test_clusters_repo.py` 58, 72; README `### PATCH`; `frontend/src/api/client.ts` patchCluster. After removal `PATCH /clusters/{id}` returns 405 (GET/DELETE share the path); verify with SPA mount too. README API intro says "`/api/v1` is additive only ... never removed"; retiring PATCH contradicts it.

## OpenAPI and schema.d.ts

- `uv run python -m agent_orchestrator.api.openapi > openapi.json` (`api/openapi.py:export`).
- `cd frontend && npm run gen:api` (openapi-typescript); CI `npm run check:api`.
- `tests/test_readme_api.py`: `test_openapi_json_matches_app`, `test_frontend_schema_matches_openapi` (needs `frontend/node_modules`), `test_every_route_documented`/`test_no_stale_route_in_readme` (README `### \`METHOD /api/v1...\`` headings, regex GET|POST|PATCH|PUT|DELETE only, `APIRoute` only). WebSocket routes are invisible to OpenAPI and this test; document them by hand.

## README API structure

`## API` (375): intro (base path, error shape, versioning, allowlist, error codes list), one `### \`METHOD path\`` per route with body/response/errors prose, then `### Events` table. `## Security` (177) and `### Ingress` (152) hold ingress guidance; no `proxy-read-timeout` text exists yet.

## Chart

- `values.yaml`: `env: {}` is the only settings channel (any `ORCH_*` key into ConfigMap, `templates/configmap.yaml:4-8,23-25`). `ingress.annotations`, `denySourceRanges`, `allowSourceRanges` (63-77) rendered by `templates/ingress.yaml`.
- Tests: `tests/test_chart_*.py` via `tests/helm_render.py` (real helm).

## Tests and e2e

- `tests/conftest.py`: testcontainers `postgres:18-alpine` session container, migrated template DB, per-test `dsn`, `empty_dsn`, `pool`. Docker required; unavailable in this sandbox (DB tests cannot run here).
- API tests: `httpx.ASGITransport(app, client=PEER)` (`test_api_clusters.py:client_for`); no WS test client yet. `tests/fakes/fake_wrapper.py:FakeWrapper` is uvicorn on a real socket (WS capable), kept honest by `test_fake_wrapper_contract.py` against the real image (`-m integration`).
- e2e: `scripts/e2e.sh` (kind, chart with `e2e/values-kind.yaml`, `ORCH_ALLOWED_CIDRS=127.0.0.0/8`, port-forward 18080), `tests/e2e/test_e2e_kind.py` fixtures `api`, `cluster` (POST raw spec). Agent image `e2e/agent-test.Dockerfile` pins wrapper `BASE_IMAGE ...:ca2ddf3`/`WRAPPER_SHA`; pyproject dev dep pins the same SHA. Epic A needs both bumped to the wrapper release with the new APIs.

## Verify commands (mise.toml)

- `mise run lint` (`uv run ruff check . && uv run ruff format --check .`) - ran: "All checks passed!", "97 files already formatted".
- `mise run test` (`uv run pytest`, excludes integration/e2e); targeted: `uv run pytest tests/test_readme_api.py tests/test_settings.py -q` - ran: 30 passed.
- `mise run test:chart`, `mise run lint:chart`, `mise run test:integration`, `mise run test:e2e`; frontend `npm run lint && npm test && npm run build && npm run check:api`.
- No mypy: not in deps, config or CI.

## Unknowns

- Origin policy for clients sending no Origin (headless, e2e): not decidable from code.
- Whether the WS relay may use the `websockets` transitive dep or must add an explicit dep.

## Plan inputs

- A: new `api/workspace.py` (or similar) router registered in `create_app`; resolve agent via `db/agents`, token via `tokens_for`; amend `test_api_never_imports_k8s_or_wrapper` (or avoid `wrapper` import) and MEMORY D5, README Architecture row.
- A: `ORCH_ALLOWED_ORIGINS` field in `Settings` + README Configuration row + `e2e/values-kind.yaml`; WS check in or beside `SourceAllowlist`.
- A: hand-written README sections for WS routes; extend `FakeWrapper`; bump wrapper SHA in pyproject, `uv.lock`, `e2e/agent-test.Dockerfile`.
- A: README `### Ingress` timeouts (`nginx.ingress.kubernetes.io/proxy-read-timeout`/`proxy-send-timeout` via `ingress.annotations`); chart test optional.
- B: `0002_presets.sql`; `db/presets.py`; `Cluster` gains `preset_id`/`preset_name`; `CreateCluster` exactly one of `spec`/`preset_id`; slug generator within 40 chars, not `orchestrator*`.
- B: delete `patch_cluster`, `PatchCluster`, `update_spec`, `ClusterDeleting`, `validate_spec` `stored` param, listed tests; add 405 test; fix README versioning sentence; update `test_migrations` versions/TABLES.
- Both: regen `openapi.json` then `npm run gen:api`; docker needed for DB tests.

## Frontend discovery (agent-orchestrator/frontend)

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

## Reuse map: cluster tabs and presets

Paths: W = code/claude-code-wrapper/src/claude_code_wrapper, O = code/agent-orchestrator/src/agent_orchestrator, F = code/agent-orchestrator/frontend/src. LSP was unavailable and jscpd not installed; near-duplicates come from grep and reading.

## Existing parts

- PTY: `W/pty_proc.py:PtyProcess` (start(argv, cwd, env, rows, cols, on_output, on_exit), write, close). No public resize: `_set_winsize` (:57) is only called in `start`.
- Ring buffer: `W/ring.py:Ring(capacity)`, passed through `PtyProcess(ring_capacity)`. Only `text()`/`tail()`, ANSI-stripped; no raw-bytes accessor for replay.
- Shell env: `W/session.py:BASE_ENV` (:80), `passthrough_names` (:195): build a scrubbed env with no CCW_* / CLAUDE_*.
- Path confinement (write side only): `W/workdir.py:safe_write_files` (:173-190, realpath + `is_relative_to`); also `W/manager.py:961`, `W/bootstrap/instructions.py:50`. No read-side or list helper.
- Wrapper auth/errors: `W/api/auth.py:require_auth` (typed to `Request`, so not usable on a WebSocket route), `W/api/errors.py:ApiError`.
- Wrapper caps: `W/config.py:LimitsConfig` (:681, has `max_file_bytes`), `SessionsConfig`.
- Wrapper SSE: `W/api/events.py` (`_frame`, heartbeat), model for pings.
- WebSocket: none in either repo's src or tests. `websockets` arrives transitively via `uvicorn[standard]`; not declared in the orchestrator pyproject. httpx has no WebSocket client.
- Token derivation `O/tokens.py:tokens_for`; pod URL `O/k8s/render.py:pod_url`; `agents.url`, `agents.session_id`, `pod_name` exist (`O/db/agents.py:Agent`).
- Wrapper HTTP client `O/wrapper/client.py:WrapperClient` (`_request`, `_error_parts`, `_raise_for_error`), no file/terminal methods. Shared httpx pool at `O/dispatcher/loop.py:Dispatcher._wrapper`.
- Source allowlist `O/api/allowlist.py:SourceAllowlist`: already closes disallowed WebSocket peers with 1008, handles IPv4-mapped; no Origin check.
- Settings `O/settings.py:Settings` (`CsvList`, `_csv`, `_split`, `_check_cidrs`, `allowed_networks`, `max_replicas`): template for `ORCH_ALLOWED_ORIGINS` and caps. Caps reach the UI via `O/api/clusters.py:meta` and `schemas.MetaCaps`.
- API plumbing: `O/api/errors.py:ApiError`/`not_found`, `O/api/app.py:create_app`, `O/api/streams.py:resume_cursor`/`stream_events`.
- Spec: `O/spec.py:validate_slug` (DNS-1123, `SLUG_MAX` 40, reserved names), `validate_spec`, `fill_resource_defaults`, `ClusterSpec`; wrapped by private `O/api/clusters.py:_check_spec`.
- Slug sanitising `O/bench/runner.py:arm_slug`; no random-suffix helper.
- DB: `O/db/clusters.py:create`/`update_spec`/`_dump`/`ClusterExists`. Migrations `O/db/migrate.py:run_migrations`, `O/db/migrations/0001_init.sql` (only one).
- Chart: `agent-orchestrator.env` shared by all components; a new `ORCH_*` setting reaches the api via values `env:` with no template change.
- Helmfile: `agents-helmfile/values/agent-orchestrator/common.yaml:37` already sets `proxy-read-timeout`/`proxy-send-timeout` 3600.
- Frontend: `F/layout/ConfirmDialog.tsx`, `F/clusters/DiscardClusterDialog.tsx` (typed confirm); `F/clusters/ClusterForm.tsx` + `clusterSpecForm.ts` (`blankValues`, `valuesFromSpec`, `validate`, `toSpec`); `F/api/client.ts` (`request`, `ApiError`, `eventStreamUrl`); `F/api/stream.ts:openStream` (EventSource only); `F/ribbon/useClusters.ts` (`sortedClusters`, `sortedAgents`, `select`); `F/chat/useClusterChat.ts` (SSE hook with epoch guard); `F/layout/useLayout.ts`, `Shell.tsx`, `ribbon/stateMark.tsx`, `ContextGauge.tsx`, `ClusterRow.tsx` (Menu), `AgentRow.tsx`; `F/layout/designRules.ts` (no colour literals, effects, glyph Unicode). No localStorage use anywhere. `@mui/icons-material` absent; IconButtons use ASCII glyphs.
- Test fixtures: `tests/fakes/fake_wrapper.py:FakeWrapper` (no file/terminal/WebSocket routes), `tests/fakes/real_wrapper.py`, `tests/test_fake_wrapper_contract.py`; `tests/factories.py:insert_cluster`/`insert_agent`; `tests/test_api_clusters.py:client_for` (httpx ASGITransport, no WebSocket). Wrapper: `tests/test_api_auth.py` (TestClient + StubManager), `tests/conftest.py:World`. `tests/e2e/test_e2e_kind.py`; `agents-helmfile/scripts/smoke.sh` + `tests/test_smoke_script.py`.

## Shared parts needing one owner

1. Wrapper path-confinement helper (read, list, cwd): wrapper file API task; terminal task uses it for the shell cwd.
2. Wrapper session-to-workdir resolver and new caps in `LimitsConfig`: wrapper file API task.
3. Wrapper WebSocket bearer-auth dependency: wrapper terminal task.
4. `PtyProcess.resize` and `Ring` raw-bytes read: wrapper terminal task.
5. Orchestrator agent resolver (cluster/agent to url, session_id, token) and shared httpx client on `app.state`: orchestrator proxy task.
6. Origin allowlist setting and check: orchestrator proxy task.
7. FakeWrapper file/terminal/WebSocket routes plus contract-test update: orchestrator proxy task; e2e uses them.
8. OpenAPI, `schema.d.ts` regen, README route sections: sequential across both epics' backend tasks; `tests/test_readme_api.py` enforces the README.
9. `_check_spec` public and shared by preset save and cluster create: presets routes task.
10. Name to DNS-1123 slugify (from `arm_slug` into `spec.py`) plus random suffix: presets cluster-create task.
11. Frontend storage wrapper (try/catch localStorage): tabs workspace task.
12. ClusterForm / `patchCluster` edit path: tabs top-bar task removes Edit entry points; presets PresetForm task removes the code.
13. Hamburger menu and top bar: tabs top-bar task; presets settings page only adds its entry.

## Near-duplicates

- WrapperClient factories: `O/dispatcher/loop.py:54-66`, `O/ingester/loop.py:245-250`, `O/cli.py:167`, `O/reconciler/loop.py:248,492`, `O/dispatcher/verify.py:46`.
- realpath + `is_relative_to` confinement: `W/workdir.py:178-190`, `W/manager.py:963-965`, `W/bootstrap/instructions.py:50-55`.
- Slug rules: `O/spec.py:16,51`, `F/clusters/clusterSpecForm.ts:SLUG`/`MAX_SLUG`, `O/bench/runner.py:32`.
- Env-key rules: `O/spec.py:_ENV_KEY_RE` vs `F/clusters/clusterSpecForm.ts:ENV_NAME`/`RESERVED_KEY`.
- `useClusters.ts` and `useClusterChat.ts` repeat stream-open and cancelled-guard code.

## Plan inputs

reuse
- PtyProcess - W/pty_proc.py:PtyProcess - wrapper terminal task
- Ring - W/ring.py:Ring - wrapper terminal task
- BASE_ENV, passthrough_names - W/session.py:BASE_ENV - wrapper terminal task
- safe_write_files (pattern) - W/workdir.py:safe_write_files - wrapper file API task
- LimitsConfig - W/config.py:LimitsConfig - wrapper file and terminal tasks
- require_auth, ApiError - W/api/auth.py:require_auth - wrapper file and terminal tasks
- tokens_for - O/tokens.py:tokens_for - orchestrator proxy task
- pod_url, Agent.url - O/k8s/render.py:pod_url - orchestrator proxy task
- WrapperClient - O/wrapper/client.py:WrapperClient - orchestrator proxy task
- SourceAllowlist - O/api/allowlist.py:SourceAllowlist - orchestrator proxy task
- Settings CsvList pattern - O/settings.py:Settings - orchestrator proxy and chart tasks
- validate_spec, fill_resource_defaults, validate_slug - O/spec.py - presets routes and cluster-create tasks
- run_migrations - O/db/migrate.py:run_migrations - presets migration task
- openStream - F/api/stream.ts:openStream - filesystem panel task
- useClusters, sortedAgents - F/ribbon/useClusters.ts - top bar and workspace tasks
- ChatView - F/chat/ChatView.tsx - workspace task
- ConfirmDialog - F/layout/ConfirmDialog.tsx - top bar task
- clusterSpecForm helpers - F/clusters/clusterSpecForm.ts:blankValues - PresetForm task
- FakeWrapper - tests/fakes/fake_wrapper.py - orchestrator proxy and e2e tasks

do-not-build
- WebSocket timeouts in deployed helmfile values: already 3600 (agents-helmfile/values/agent-orchestrator/common.yaml:37); chart README note only.
- Chart wiring for new ORCH_* settings: shared env helper; docs only.
- A separate PTY or ring: extend PtyProcess and Ring (resize, raw read).
- A new token scheme: tokens_for.
- A WebSocket peer allowlist: SourceAllowlist covers websocket scope; add Origin only.

fix-as-ac
- require_auth typed to Request (W/api/auth.py:21): WebSocket without a valid bearer is rejected, tested with TestClient.websocket_connect.
- `_check_spec` private (O/api/clusters.py:82): preset save and cluster create call one public validator.
- httpx ASGITransport cannot test WebSocket (O/tests/test_api_clusters.py:28): relay tests use TestClient sockets plus an API-only e2e.
- websockets undeclared in the orchestrator pyproject: declare it.
- PATCH retirement leftovers (O/api/clusters.py:170, db/clusters.update_spec, F/api/client.ts:patchCluster): 405 retirement test and symbols gone.
- Default preset seed idempotent: re-running does not overwrite an edited default.

ideas
- adopted: SSE heartbeat cadence from W/api/events.py for the 20 s terminal ping.
- adopted: arm_slug sanitising for preset-name slugs.
- rejected: inotify for tree refresh (README Q10).
- open: frontend storage.ts wrapper must be built.
