# web ui cluster tabs with filesystem chat and terminal panels implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: fe deps and storage

- Status: done
- Files: `frontend/package.json`, `frontend/package-lock.json`, `frontend/vite.config.ts`, `frontend/src/api/client.ts`, `frontend/src/layout/storage.ts`, `frontend/src/layout/storage.test.ts`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/storage.test.ts src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build`
- Verified head: fa1456d8c69b6a9b89be5f97bd0d317299d0f758

#### Requirement

Lay the frontend foundation for the workspace (design D7; user Q13), test-first where behaviour exists.

- Dependencies in `frontend/package.json` with the lock updated (`npm install`, commit `package-lock.json`): `react-resizable-panels` `^4.14.8`, `@xterm/xterm` `^6.0.0`, `@xterm/addon-fit` `^0.11.0`, `@mui/x-tree-view` `^9.16.0`, `@mui/icons-material` `~9.5.0`. `npm ci` stays clean (no peer conflicts with React 19.3 and MUI 9.5).
- `frontend/vite.config.ts`: the dev proxy for `/api` also proxies WebSockets (`ws: true`).
- `frontend/src/api/client.ts`: export the existing `request` and `query` helpers (no behaviour change) so new API modules reuse them.
- New `frontend/src/layout/storage.ts`: `loadJson<T>(key: string, fallback: T, valid?: (v: unknown) => v is T): T` and `saveJson(key: string, value: unknown): void`. Neither ever throws: a missing `localStorage`, a throwing getter or setter (private mode, quota), invalid JSON or a value failing `valid` all yield the fallback or a silent no-op. Keys are namespaced `orch:`.

#### Acceptance conditions

- AC1: loadJson returns stored values and the fallback for missing, invalid or rejected values [evidence: test:frontend/src/layout/storage.test.ts::loadJson_round_trip_and_fallbacks]
- AC2: loadJson and saveJson never throw when localStorage is absent or throws [evidence: test:frontend/src/layout/storage.test.ts::storage_never_throws]
- AC3: the new dependencies install cleanly and the app builds [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend run build]
- AC4: the Vite dev proxy forwards WebSockets [evidence: command:grep -q 'ws: true' frontend/vite.config.ts]
- AC5: storage test, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/storage.test.ts src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

#### Files

- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/vite.config.ts`
- `frontend/src/api/client.ts`
- `frontend/src/layout/storage.ts`
- `frontend/src/layout/storage.test.ts`

#### Interfaces

- `frontend/src/layout/storage.ts`: `loadJson`, `saveJson` (owns part `fe-storage`, consumed by fe-panel-workspace).
- `frontend/package.json` dependency set (owns part `fe-deps`, consumed by fe-top-bar, fe-panel-workspace, fe-filesystem-panel, fe-terminal-socket, fe-terminal-panel).
- `frontend/src/api/client.ts`: `request`, `query` now exported.

#### Expected outcome

Every later frontend task can import the panel, tree, terminal and icon libraries, call `request`, and persist UI state safely.

#### Steps

- Write `frontend/src/layout/storage.test.ts` (node environment, stub `globalThis.localStorage` with a map and with throwing methods; test titles exactly `loadJson_round_trip_and_fallbacks` and `storage_never_throws`); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/storage.test.ts`: fails (module missing).
- Implement `storage.ts`; rerun: passes.
- Add the dependencies (`mise x node@24.20.0 -- npm --prefix frontend install <pkgs>`), the proxy flag and the exports; run the verify command: passes.

#### Notes

- PATH node is 22; use `mise x node@24.20.0 --` for every npm call (jsdom 30 wants node 24).
- The build already warns about a chunk over 500 kB; that warning is non-fatal and not in scope.
- No colour literals anywhere outside `theme.ts` (designRules).

### S2: origin allowlist

- Status: done
- Files: `src/agent_orchestrator/settings.py`, `src/agent_orchestrator/api/origin.py`, `src/agent_orchestrator/api/app.py`, `README.md`, `chart/agent-orchestrator/README.md`, `e2e/values-kind.yaml`, `tests/test_origin.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_origin.py tests/test_settings.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 2a8ce4f66056f06eadc3e460137d6d2abe5f9282

#### Requirement

Add the mandatory Origin allowlist to the orchestrator api (design D5, user Q7), test-first.

- `Settings.allowed_origins` (`ORCH_ALLOWED_ORIGINS`), a comma-separated `CsvList` of origins (`scheme://host[:port]`, lower-cased, no path, no trailing slash; an invalid entry fails settings validation with the field name), default empty.
- New `src/agent_orchestrator/api/origin.py`:
  - a pure ASGI middleware added in `api/app.py` that, for every `websocket` scope, reads the `Origin` header: absent passes; `null` or not in `allowed_origins` is refused with `websocket.close` code 1008 before accept. An empty list refuses every Origin-bearing upgrade. It runs together with the existing `SourceAllowlist`, which is unchanged.
  - a FastAPI dependency `require_allowed_origin` that applies the same rule to an HTTP request and raises `ApiError` 403 `forbidden_origin`; the terminal routes (task terminal-proxy-routes) attach it to their POST and DELETE.
- `e2e/values-kind.yaml` sets `ORCH_ALLOWED_ORIGINS` to `http://127.0.0.1:18080,http://localhost:18080` (the e2e port-forward).
- README (`code/agent-orchestrator/README.md`): a `## Configuration` row for `ORCH_ALLOWED_ORIGINS` (default empty, read by api); in `## Security` the Origin rule (why: browsers apply no CORS to WebSocket upgrades), including that deployments serving the UI must list the UI origin; in `### Ingress` that WebSocket routes need `nginx.ingress.kubernetes.io/proxy-read-timeout` and `proxy-send-timeout` raised (3600, as agents-helmfile already sets) through `ingress.annotations`, and that the UI pings every 20 s; `forbidden_origin` (403) added to the API error code list.

#### Acceptance conditions

- AC1: ORCH_ALLOWED_ORIGINS parses a CSV of origins, normalises case and rejects a value with a path [evidence: test:tests/test_origin.py::test_settings_parse_and_validate]
- AC2: a WebSocket upgrade with an unlisted or null Origin is closed with 1008 before accept, a listed Origin and a missing Origin pass [evidence: test:tests/test_origin.py::test_websocket_origin_rule]
- AC3: an empty allowlist refuses every Origin-bearing upgrade [evidence: test:tests/test_origin.py::test_empty_list_fails_closed]
- AC4: require_allowed_origin answers 403 forbidden_origin for an unlisted Origin on HTTP and passes a missing one [evidence: test:tests/test_origin.py::test_http_dependency]
- AC5: the setting is documented in the README Configuration table [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_settings.py]
- AC6: README Security and Ingress describe the Origin rule and the WebSocket timeouts [evidence: doc-section:README.md#Ingress]
- AC7: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_origin.py tests/test_settings.py && uv run ruff check . && uv run ruff format --check .]
- AC8: the orchestrator README and the chart README document ORCH_ALLOWED_ORIGINS with http://localhost:5173 as the dev example [evidence: test:tests/test_origin.py::test_readmes_document_dev_origin]

#### Files

- `src/agent_orchestrator/settings.py`
- `src/agent_orchestrator/api/origin.py`
- `src/agent_orchestrator/api/app.py`
- `README.md`
- `chart/agent-orchestrator/README.md`
- `e2e/values-kind.yaml`
- `tests/test_origin.py`

#### Interfaces

- `agent_orchestrator.settings.Settings.allowed_origins` (`ORCH_ALLOWED_ORIGINS`; cross-epic contract `orch-allowed-origins`, consumed by agents-helmfile task deploy-pin).
- `agent_orchestrator.api.origin.OriginAllowlist` (ASGI) and `require_allowed_origin` (dependency) (owns part `origin-allowlist`, consumed by terminal-proxy-routes and terminal-ws-relay).

#### Expected outcome

A browser page from another origin can no longer open any WebSocket on the api; headless clients that send no Origin keep working.

#### Steps

- Write `tests/test_origin.py`: settings parsing, and the middleware exercised directly as ASGI (call it with a fake `websocket` scope and receive/send queues, assert the `websocket.close` 1008 message and that the inner app was not called), plus a tiny FastAPI app for the dependency via `httpx.ASGITransport`; run `uv run pytest -q -p no:cacheprovider tests/test_origin.py`: fails (ImportError).
- Implement the setting, `api/origin.py`, add the middleware in `create_app`; rerun: passes.
- README rows and sections; `uv run pytest -q -p no:cacheprovider tests/test_settings.py`: passes.
- `uv run ruff check . && uv run ruff format --check .`: clean.

#### Notes

- Pattern: `api/allowlist.py:SourceAllowlist` (pure ASGI over `http` and `websocket`, closes 1008 before accept) and the `CsvList` plus `_split` validator in `settings.py`.
- do-not-build: no chart template change (values `env:` already reaches every component's ConfigMap) and no new peer allowlist.
- No route in the app is a WebSocket yet; the middleware test needs no real WebSocket route.
- Builder check ruling 10: Accepted that only configured origins work; the orchestrator README and chart README document ORCH_ALLOWED_ORIGINS with http://localhost:5173 as the dev example; the helmfile sets only the ingress origin. The chart README is chart/agent-orchestrator/README.md (create it if absent; it is now in files).

- 2026-10-23 amended: builder check rulings 10 add acceptance conditions AC8-AC8

### S3: pty resize and raw ring

- Status: done
- Files: `src/claude_code_wrapper/pty_proc.py`, `src/claude_code_wrapper/ring.py`, `tests/test_pty_proc.py`, `tests/test_ring.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_pty_proc.py tests/test_ring.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 2f6788d78832faeb574ecf5ab729b512f78b612a

#### Requirement

Give the wrapper's PTY layer the two primitives an interactive shell needs, without changing how Claude sessions use it.

- `PtyProcess.resize(rows: int, cols: int) -> None` in `src/claude_code_wrapper/pty_proc.py` sets the window size of the running child's PTY (TIOCSWINSZ on the master, which delivers SIGWINCH to the foreground process group). Rows and cols must be 1..1000, else `ValueError`. Calling it before `start()` or after `close()` raises `RuntimeError`; it never blocks the event loop.
- `Ring.raw() -> bytes` in `src/claude_code_wrapper/ring.py` returns the newest bytes exactly as appended (no ANSI stripping, no decoding), at most `capacity` bytes, taken under the ring lock. `text()`, `tail()`, `contains()` and `written` behave as before.
- Existing callers (`session.py:_spawn`) are untouched; the existing tests in `tests/test_pty_proc.py` and `tests/test_ring.py` keep passing.

#### Acceptance conditions

- AC1: resize changes the child's window size as seen by the child (`stty size` or `os.get_terminal_size` in a `py(...)` child prints the new rows and cols) [evidence: test:tests/test_pty_proc.py::test_resize_reaches_child]
- AC2: resize rejects out-of-range sizes and calls before start or after close [evidence: test:tests/test_pty_proc.py::test_resize_rejects_bad_sizes_and_states]
- AC3: Ring.raw returns the newest raw bytes, escapes included, capped at capacity [evidence: test:tests/test_ring.py::test_raw_keeps_escapes_and_caps]
- AC4: the targeted PTY and ring suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_pty_proc.py tests/test_ring.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/pty_proc.py`
- `src/claude_code_wrapper/ring.py`
- `tests/test_pty_proc.py`
- `tests/test_ring.py`

#### Interfaces

- `claude_code_wrapper.pty_proc.PtyProcess.resize(self, rows: int, cols: int) -> None` (new, owns part `pty-resize`).
- `claude_code_wrapper.ring.Ring.raw(self) -> bytes` (new, owns part `ring-raw-snapshot`).
- Consumed by task terminal-registry (scrollback replay and resize control frames).

#### Expected outcome

A shell started under `PtyProcess` can be resized while it runs, and its last N bytes of raw output can be replayed byte for byte.

#### Steps

- Write `test_resize_reaches_child` and `test_resize_rejects_bad_sizes_and_states` in `tests/test_pty_proc.py` (use the existing `spawn` fixture and `py(...)` helper; the child loops printing `os.get_terminal_size(0)` on SIGWINCH or on a stdin line) and `test_raw_keeps_escapes_and_caps` in `tests/test_ring.py`; run `uv run pytest -q -p no:cacheprovider tests/test_pty_proc.py tests/test_ring.py`: the three new tests fail with AttributeError.
- Implement `resize` (reuse `_set_winsize` on the master fd) and `raw`; rerun: all pass.
- `uv run ruff check . && uv run ruff format --check .`: "All checks passed!".

#### Notes

- Pure asyncio, no threads; `resize` is a synchronous ioctl and must check `self._fd` (or equivalent) is open.
- Do not touch `tests/conftest.py` (wrapper rule: only the fake-claude task edits it).
- `tests/test_manager.py::test_shutdown_stops_all` fails only in this container (PID 1 does not reap zombies; CI on main is green); it is not part of this task's verify.

### S4: wrapper file api

- Status: done
- Files: `src/claude_code_wrapper/files.py`, `src/claude_code_wrapper/api/files.py`, `src/claude_code_wrapper/api/app.py`, `src/claude_code_wrapper/config.py`, `README.md`, `tests/test_api_files.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_api_files.py tests/test_readme_api.py tests/test_readme_config.py tests/test_config.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: f63dee9c6a431d93f31b3cba025e9b98518ae24f

#### Requirement

Add a session-scoped, read-only file API to the wrapper (design D1), test-first.

Routes (under the existing `/v1` router, bearer auth as every `/v1` route), in a new `src/claude_code_wrapper/api/files.py` registered in `api/app.py`:

- `GET /v1/sessions/{id}/files?path=<rel>&offset=<n>`: lists one directory of the session workdir. `path` is relative to the workdir, default empty (the workdir itself); `offset` default 0. Response 200 `{"session_id", "root": <absolute realpath of the workdir>, "path": <normalised relative path, "" for root>, "entries": [{"name", "type": "dir"|"file"|"symlink"|"other", "size": int|null, "mtime": ISO-8601 str}], "next_offset": int|null}`. Everything is listed, dotfiles and `.git` included. Order: directories first, then everything else, each by name (byte order). At most `limits.files_max_entries` entries per response; `next_offset` is the offset of the next page or null.
- `GET /v1/sessions/{id}/files/content?path=<rel>`: reads one file. Response 200 `{"session_id", "path", "size", "mtime", "mime": str|null (from `mimetypes.guess_type`), "kind": "text"|"binary"|"too_large", "content": str|null}`. `kind` is `too_large` when size exceeds `limits.file_preview_max_bytes` (content null, the file is not read past the check); `binary` when the first 8 KiB contain a NUL byte or the bytes are not valid UTF-8 (content null); else `text` with the decoded content.

Confinement, in a new `src/claude_code_wrapper/files.py` (one helper, owns part `wrapper-path-confinement`, reused by the terminal task for the shell cwd): `resolve_in_workdir(workdir: str, rel: str) -> Path` rejects absolute `rel`, NUL bytes, and any path whose `realpath` is not inside the `realpath` of the workdir (so `..` and escaping symlinks fail). A symlink entry is listed as `symlink` and is followed by the content route only when its resolved target stays inside the workdir.

Errors (the existing `ApiError` envelope): `invalid_path` 400 (escape, absolute, NUL), `not_found` 404 for an unknown session (existing `SessionNotFound` path) and for a missing path, `not_a_directory` 400 when listing a file, `not_a_file` 400 when reading a directory, FIFO, socket or device. The content route opens only after the realpath confinement check, with `os.open(path, O_RDONLY | O_NOFOLLOW | O_NONBLOCK)`, then `os.fstat` on the descriptor and refuses anything that is not a regular file (closing the descriptor unread); it never stats and then opens by path, so a path swapped to a FIFO, device or symlink between check and open cannot hang or leak, and size and the bounded read come from the same descriptor. The session workdir comes from `manager.get(id)["workdir"]`, so live and persisted sessions both work; a session whose workdir no longer exists answers `not_found`.

Config: `LimitsConfig.files_max_entries` (default 2000, ge=1) and `LimitsConfig.file_preview_max_bytes` (default 1048576, ge=1); the existing `max_file_bytes` keeps its meaning (turn files).

README (`code/claude-code-wrapper/README.md`): one `### \`GET /v1/sessions/{id}/files\`` and one `### \`GET /v1/sessions/{id}/files/content\`` section under `## API reference` (parameters, response fields, errors), rows for the new error codes in `## Errors`, rows for the two config keys with their defaults in `## Configuration reference`, and `## Trust model` sentences that the file API reads only inside the session workdir after symlink resolution, and that file content (and, in the terminal task, terminal frames) is not passed through the secret redactor: redaction would corrupt files and PTY streams, and the shell already runs as the agent uid, so anything the agent can read a client can read.

#### Acceptance conditions

- AC1: listing the root returns dirs first, dotfiles and .git included, with root, types, sizes and mtimes [evidence: test:tests/test_api_files.py::test_list_root_dirs_first_includes_dotfiles]
- AC2: listing pages at files_max_entries with next_offset [evidence: test:tests/test_api_files.py::test_list_pages_with_next_offset]
- AC3: `..`, absolute paths, NUL bytes and a symlink pointing outside the workdir are refused with invalid_path and nothing outside is read [evidence: test:tests/test_api_files.py::test_escapes_refused]
- AC4: content returns text, binary (NUL or invalid UTF-8) and too_large kinds per the 1 MiB cap [evidence: test:tests/test_api_files.py::test_content_kinds]
- AC5: a FIFO is refused with not_a_file without blocking or reading (opened O_NONBLOCK, then refused by fstat), and directory vs file mismatches answer not_a_directory and not_a_file [evidence: test:tests/test_api_files.py::test_fifo_and_type_mismatch_refused]
- AC6: a request without the bearer token is 401, an unknown session or path is 404 [evidence: test:tests/test_api_files.py::test_auth_and_not_found]
- AC7: README documents both routes, the error codes and the config keys, enforced by the README tests [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_readme_api.py tests/test_readme_config.py tests/test_config.py]
- AC8: the confinement helper exists and is the only path resolver of the file routes [evidence: symbol:src/claude_code_wrapper/files.py::resolve_in_workdir]
- AC9: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_api_files.py tests/test_readme_api.py tests/test_readme_config.py tests/test_config.py && uv run ruff check . && uv run ruff format --check .]
- AC10: the content route opens with O_RDONLY|O_NOFOLLOW|O_NONBLOCK after confinement and checks fstat on the descriptor; a path swapped to a FIFO, symlink or device between the confinement check and the open is refused and nothing is read [evidence: test:tests/test_api_files.py::test_content_open_nofollow_and_fstat]
- AC11: README Trust model states that file content and terminal frames are not passed through the secret redactor and why [evidence: doc-section:README.md#Trust model]

#### Files

- `src/claude_code_wrapper/files.py`
- `src/claude_code_wrapper/api/files.py`
- `src/claude_code_wrapper/api/app.py`
- `src/claude_code_wrapper/config.py`
- `README.md`
- `tests/test_api_files.py`

#### Interfaces

- `claude_code_wrapper.files.resolve_in_workdir(workdir: str, rel: str) -> pathlib.Path` (owns part `wrapper-path-confinement`), plus listing and reading helpers in the same module.
- Routes `GET /v1/sessions/{id}/files` and `GET /v1/sessions/{id}/files/content` (owns part `wrapper-files-api`, cross-repo contract `wrapper-files-api`, consumed by agent-orchestrator task file-proxy-routes): field names above are the contract.
- `LimitsConfig.files_max_entries`, `LimitsConfig.file_preview_max_bytes`.

#### Expected outcome

`curl -H 'Authorization: Bearer ...' http://pod:8080/v1/sessions/<id>/files` lists the workdir; `.../files/content?path=README.md` returns its text; nothing outside the workdir is ever readable.

#### Steps

- Write `tests/test_api_files.py` with a stub manager (pattern of `tests/test_api_auth.py`: `TestClient` plus a stub whose `get(sid)` returns `{"workdir": str(tmp_path / "wd")}`), covering AC1-AC6; run `uv run pytest -q -p no:cacheprovider tests/test_api_files.py`: fails (404 routes).
- Implement `files.py`, `api/files.py`, register the router in `api/app.py`, add the config keys; rerun: passes.
- Update the README sections; run `uv run pytest -q -p no:cacheprovider tests/test_readme_api.py tests/test_readme_config.py tests/test_config.py`: passes.
- `uv run ruff check . && uv run ruff format --check .`: clean.

#### Notes

- Confinement precedent: `workdir.py:safe_write_files` (realpath root, `is_relative_to`). Do not move or change it; the new helper is read-side.
- Read with a bounded read (`size` from `os.fstat` on the opened descriptor; never `read()` an unbounded file; never stat then open by path); do the blocking filesystem work in `asyncio.to_thread` so a slow CephFS stat does not stall the loop.
- `mtime` as UTC ISO-8601 with milliseconds, like other wrapper timestamps.
- Wrapper rules: plain ASCII, `uv run` always, never write service files into a session workdir (tests create their own fixture files in `tmp_path`).
- `tests/test_manager.py::test_shutdown_stops_all` fails only in this container (PID 1 does not reap zombies); not a verify target.

- 2026-10-23 amended: interrogate rulings 9 (open with O_NOFOLLOW|O_NONBLOCK and fstat, no stat-then-open) and 12 (README Trust model states no redaction of file content and terminal frames)

### S5: fe top bar

- Status: done
- Files: `frontend/src/layout/TopBar.tsx`, `frontend/src/layout/SessionsMenu.tsx`, `frontend/src/layout/TopBar.test.tsx`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/TopBar.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build`
- Verified head: 997f078e838f0a9a51d8124d0c10ee202e7b87e9

#### Requirement

Build the top bar and the hamburger sessions menu as standalone components (user Q1, Q14, Q15), test-first; wiring into App is task fe-retire-ribbon.

- New `frontend/src/layout/TopBar.tsx`: `TopBar({clusters, selectedId, onSelect, onNew, onDiscard, settingsCategories})`. Left to right: a hamburger `IconButton` (MUI `MenuIcon`, `aria-label="Open menu"`), a MUI `Tabs` `variant="scrollable"` with one tab per cluster in `sortedClusters` order (label: `StateMark`, slug, `ContextGauge` with the cluster's `context_pct_max` and auto-compact tick), the active tab = `selectedId`, then a "New cluster" button. Each tab has an actions button (`aria-label="Cluster actions"`) opening a `Menu` whose only item is "Discard" (calls `onDiscard(cluster)`); there is no Edit item. Tabs cannot be closed.
- New `frontend/src/layout/SessionsMenu.tsx`: `SessionsMenu({open, onClose, clusters, selectedId, onSelect, settingsCategories})`, a temporary MUI `Drawer` anchored left: a "Sessions" list from the top, one item per cluster (state mark and slug, the selected one marked), choosing one calls `onSelect(id)` and closes; a "Settings" section pinned to the bottom that renders one item per entry of `settingsCategories: {id, label, onOpen}[]` and the text "No settings yet" when the list is empty (this epic passes an empty list; the cluster-presets epic adds Presets).
- Both pass `designRules` (no colour literals, no decorative Unicode, no `title=` on buttons); icons come from `@mui/icons-material`.

#### Acceptance conditions

- AC1: one tab per cluster in slug order with state mark, slug and gauge, the selected one active, and selecting a tab calls onSelect [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/TopBar.test.tsx -t tabs_one_per_cluster_in_slug_order]
- AC2: the tab actions menu offers Discard only, no Edit [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/TopBar.test.tsx -t tab_actions_offer_discard_only]
- AC3: New cluster calls onNew [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/TopBar.test.tsx -t new_cluster_button]
- AC4: the hamburger opens the drawer listing sessions from the top, and choosing one selects it and closes the drawer [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/TopBar.test.tsx -t hamburger_lists_sessions_and_selects]
- AC5: the settings section sits at the bottom, renders given categories and shows the empty state when none [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/TopBar.test.tsx -t settings_section_bottom_with_empty_state]
- AC6: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/TopBar.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

#### Files

- `frontend/src/layout/TopBar.tsx`
- `frontend/src/layout/SessionsMenu.tsx`
- `frontend/src/layout/TopBar.test.tsx`

#### Interfaces

- `TopBar` props as above; `SessionsMenu` props including `settingsCategories: {id: string, label: string, onOpen: () => void}[]` (owns part `fe-sessions-menu`, consumed by fe-retire-ribbon; cross-epic contract `orch-settings-menu`, consumed by cluster-presets).
- Uses `StateMark` (`ribbon/stateMark.tsx`), `ContextGauge` (`ribbon/ContextGauge.tsx`), `sortedClusters` and `ClusterEntry` (`ribbon/useClusters.ts`), part `fe-deps` (icons).

#### Expected outcome

A tested top bar and drawer ready to replace the ribbon, with the settings area the presets epic will fill.

#### Steps

- Write `frontend/src/layout/TopBar.test.tsx` (`// @vitest-environment jsdom`, stub `window.matchMedia` like the other tests; titles exactly as in the AC refs); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/TopBar.test.tsx`: fails.
- Implement `TopBar.tsx` and `SessionsMenu.tsx`; rerun: passes; run the verify command.

#### Notes

- `StateMark`, `ContextGauge` and `useClusters.ts` stay where they are (under `ribbon/`); moving them is not in scope.
- The cluster-presets epic will add a Presets entry through `settingsCategories` and remove the ClusterForm edit code; keep that prop generic.

### S6: terminal registry

- Status: done
- Files: `src/claude_code_wrapper/terminals.py`, `src/claude_code_wrapper/config.py`, `src/claude_code_wrapper/manager.py`, `README.md`, `tests/test_terminals.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_terminals.py tests/test_readme_config.py tests/test_config.py tests/test_manager.py --deselect tests/test_manager.py::test_shutdown_stops_all && uv run ruff check . && uv run ruff format --check .`
- Verified head: 5f8f1e22b82b0927bb77e14433fc688c402d92d2

#### Requirement

Add the wrapper's terminal registry (design D2, D3, D11; user Q4, Q5, Q6): the in-process owner of interactive shells, test-first, with no HTTP surface yet.

New `src/claude_code_wrapper/terminals.py` with a `TerminalRegistry` held by the `SessionManager` (for example `manager.terminals`):

- `create(session_id, rows=24, cols=80) -> TerminalInfo` starts a shell under `PtyProcess(ring_capacity=limits.terminal_scrollback_bytes)`: argv `/bin/bash -l` (or `/bin/sh -l` when `/bin/bash` is absent), cwd the session workdir resolved through `files.resolve_in_workdir(workdir, "")`, env = the env `manager._child_env(ctx)` builds for the Claude process (BASE_ENV plus the passthrough set including `spec.env`, plus `TERM=xterm-256color`), minus every `ClaudeEnv` name of kind `secret` (`claude_env.py:30`, which includes `ANTHROPIC_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN`) and `CCW_AUTH_TOKEN`, `CCW_PEER_TOKEN`, `CCW_HOOK_TOKEN`; never the whole `manager.service_env`. Ids are `term_<12 lowercase hex>`. `TerminalInfo` carries `terminal_id`, `session_id`, `created_at`, `alive`, `exit_code`, `attached` (client count), `rows`, `cols`.
- Cap: at most `limits.terminals_max` (default 8) live terminals per wrapper process (one pod); one more raises a `TerminalLimit` error. `create` reserves its slot synchronously (count check and registration in one step, no await between) before awaiting `PtyProcess.start`, and releases the slot if the start fails, so concurrent creates never exceed the cap.
- `list(session_id) -> list[TerminalInfo]`, `get(session_id, terminal_id)` (unknown raises `TerminalNotFound`), `close(session_id, terminal_id)` (idempotent, uses `PtyProcess.close`): it unregisters the terminal synchronously before awaiting the close, so an attach racing the reaper gets `TerminalNotFound` (404) or the exit marker, never a hang. Closing kills every process in the shell's session (session id equals the shell pid, found by scanning `/proc/<pid>/stat`), not only its process group, so a `nohup` or `setsid`-less background job does not survive the close.
- `attach(session_id, terminal_id) -> Attachment`: registers a subscriber and returns the scrollback snapshot (`Ring.raw()`) taken in the same synchronous step as the subscription, so no byte is lost or duplicated between replay and live output. Each subscriber has a bounded queue (bytes plus an exit marker); when a subscriber's queue overflows it is marked overflowed and dropped (the API task closes it with 1013) while the PTY reader and the other subscribers carry on. `Attachment.detach()` removes it. Input: `write(bytes)`; `resize(rows, cols)` uses `PtyProcess.resize`.
- Exit: when the shell exits every subscriber receives the exit marker with the exit code; the terminal stays listed with `alive: false` until closed or reaped.
- Reaper: a terminal with no attached client for `limits.terminal_idle_reap_seconds` (default 900) is closed and removed; an attached terminal is never reaped; an exited terminal with no client is removed at the next reaper tick (builder check ruling 2).
- Session destroy closes the session's terminals (every process of each shell's session); `SessionManager.shutdown()` closes every terminal (bounded by the existing shutdown budget) and stops the reaper.

Config (`LimitsConfig`, each with a `## Configuration reference` row and its default in the wrapper README): `terminals_max` 8 (ge=0, 0 disables terminals), `terminal_scrollback_bytes` 262144 (ge=1), `terminal_idle_reap_seconds` 900 (gt=0), `terminal_max_frame_bytes` 65536 (ge=1, read by the API task).

#### Acceptance conditions

- AC1: a created shell runs in the session workdir and echoes typed input back through a subscriber [evidence: test:tests/test_terminals.py::test_create_runs_shell_in_workdir]
- AC2: with every scrubbed name seeded (sentinel values) into both the service env and the Claude env (every ClaudeEnv secret-kind name, CCW_AUTH_TOKEN, CCW_PEER_TOKEN, CCW_HOOK_TOKEN), the shell prints none of the names or values and has TERM=xterm-256color; a seeded non-secret passthrough name is still present [evidence: test:tests/test_terminals.py::test_env_scrubbed]
- AC3: the ninth live terminal is refused with TerminalLimit [evidence: test:tests/test_terminals.py::test_cap_per_process]
- AC4: attach returns the scrollback snapshot and then only newer bytes, with no gap or duplicate [evidence: test:tests/test_terminals.py::test_attach_replays_then_streams]
- AC5: an overflowing subscriber is dropped while the other subscriber keeps receiving output [evidence: test:tests/test_terminals.py::test_slow_subscriber_dropped_not_blocking]
- AC6: shell exit delivers the exit code to subscribers and marks the terminal not alive [evidence: test:tests/test_terminals.py::test_exit_reported]
- AC7: the reaper closes a detached terminal after the idle delay and never an attached one [evidence: test:tests/test_terminals.py::test_reaper_respects_attachment]
- AC8: close, session destroy and manager shutdown each close the terminals and kill a nohup'd background job the shell started (every process in the shell's session is gone) [evidence: test:tests/test_terminals.py::test_closed_on_destroy_and_shutdown]
- AC9: the config keys are documented with their defaults [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_readme_config.py tests/test_config.py]
- AC10: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_terminals.py tests/test_readme_config.py tests/test_config.py tests/test_manager.py --deselect tests/test_manager.py::test_shutdown_stops_all && uv run ruff check . && uv run ruff format --check .]
- AC11: attaching to an exited terminal returns the scrollback and then the exit marker [evidence: test:tests/test_terminals.py::test_attach_exited_replays_then_exit]
- AC12: the idle clock starts at creation for a never-attached terminal and at the last detach otherwise [evidence: test:tests/test_terminals.py::test_idle_clock_creation_and_detach]
- AC13: terminals_max counts exited terminals and an exited terminal with no client is reaped at the next reaper tick [evidence: test:tests/test_terminals.py::test_cap_counts_exited_and_reaps_exited]
- AC14: rows or cols outside 1..1000 on create raise InvalidSize [evidence: test:tests/test_terminals.py::test_invalid_size_rejected]
- AC15: the shell env equals the env manager._child_env(ctx) builds for Claude (BASE_ENV plus the passthrough set including spec.env) minus every ClaudeEnv secret-kind name and CCW_AUTH_TOKEN, CCW_PEER_TOKEN, CCW_HOOK_TOKEN, and is not the whole service env [evidence: test:tests/test_terminals.py::test_env_matches_claude_process_env]
- AC16: create or attach on a known but not active session raises SessionNotActive and stopping a session closes its shells [evidence: test:tests/test_terminals.py::test_session_not_active_and_closed_on_stop]
- AC17: concurrent creates (more tasks than the cap, started together) never leave more than terminals_max registered terminals and a failed start releases its slot [evidence: test:tests/test_terminals.py::test_concurrent_creates_never_exceed_cap]
- AC18: an attach racing a reap or close gets TerminalNotFound or the exit marker and never hangs [evidence: test:tests/test_terminals.py::test_attach_during_reap_never_hangs]

#### Files

- `src/claude_code_wrapper/terminals.py`
- `src/claude_code_wrapper/config.py`
- `src/claude_code_wrapper/manager.py`
- `README.md`
- `tests/test_terminals.py`

#### Interfaces

- `claude_code_wrapper.terminals.TerminalRegistry` with `create`, `list`, `get`, `close`, `attach`, `close_all`; `TerminalInfo`, `Attachment` (`queue`, `detach()`, `write()`, `resize()`), errors `TerminalLimit`, `TerminalNotFound` (owns part `terminal-registry`, consumed by terminal-websocket-api).
- Uses `PtyProcess.resize` and `Ring.raw` (parts `pty-resize`, `ring-raw-snapshot`) and `files.resolve_in_workdir` (part `wrapper-path-confinement`).
- `LimitsConfig.terminals_max`, `terminal_scrollback_bytes`, `terminal_idle_reap_seconds`, `terminal_max_frame_bytes`.

#### Expected outcome

The manager can start, fan out, resize, reap and close login shells in a session workdir, with secrets scrubbed and a hard per-pod cap, ready for the HTTP and WebSocket layer.

#### Steps

- Write `tests/test_terminals.py` (AC1-AC8). Build a `SessionManager` with a stub or the `world` fixture only if needed; a registry constructed with a fake `workdir_of(session_id)` callable and an explicit `service_env` keeps it fast. Use a tiny reap delay in tests. Run `uv run pytest -q -p no:cacheprovider tests/test_terminals.py`: fails (ImportError).
- Implement `terminals.py`, the config keys and the manager wiring (destroy and shutdown); rerun: passes.
- Add the README config rows; run `uv run pytest -q -p no:cacheprovider tests/test_readme_config.py tests/test_config.py`: passes.
- `uv run ruff check . && uv run ruff format --check .`: clean.

#### Notes

- Concurrency is the risk: `PtyProcess` has one `on_output` callback, called on the loop; fan out from it with `queue.put_nowait` per subscriber and treat `QueueFull` as overflow. Never await inside the callback.
- Snapshot and subscribe in the same synchronous block (no await between) so replay and live output join exactly.
- `CCW_HOOK_TOKEN` is per session and is set by `_child_env`; it is scrubbed with the other tokens (defence in depth, user Q6; the same uid can still read `/proc`, which the trust model accepts).
- The shell is a login shell so `/etc/profile.d/mise-shims.sh` puts the mise tools on PATH in the image (Dockerfile:81).
- Tests run real children: use `/bin/sh` (present everywhere) and short `wait_until` bounds.
- `tests/test_manager.py::test_shutdown_stops_all` fails only in this container (PID 1 does not reap zombies; CI on main is green); the verify command includes `tests/test_manager.py` (this task touches the manager destroy, stop and shutdown paths) with that one test deselected. Do not edit `tests/conftest.py`.
- Builder check ruling 1: Attaching to an exited shell replays the scrollback, sends the exit control frame, then closes 1000. The panel reopens tabs on mount only for alive shells from listTerminals.
- Builder check ruling 2: The idle clock starts at creation for a never-attached terminal, else at the last detach. terminals_max counts every registered terminal, alive or exited; an exited terminal with no attached client is reaped at the next reaper tick.
- Builder check ruling 3: Rows or cols outside 1..1000 on create answer 422 with code invalid_size (wrapper, passed through by the orchestrator); a resize control frame out of range or malformed is ignored and logged, the socket stays open.
- Builder check ruling 4 (widened by interrogate ruling 1): The shell env is the env `manager._child_env(ctx)` builds for Claude (BASE_ENV plus the passthrough set, which includes spec.env, plus TERM) minus every ClaudeEnv name of kind secret (claude_env.py:30) and CCW_AUTH_TOKEN, CCW_PEER_TOKEN, CCW_HOOK_TOKEN; not the whole service env.
- Builder check ruling 5: Terminals exist only for an active session; create or attach on a known but not active session answers 409 session_not_active; 404 only for an unknown session. Stopping or destroying a session closes its shells.

- 2026-10-23 amended: builder check rulings 1,2,3,4,5 add acceptance conditions AC11-AC16

- 2026-10-23 amended: interrogate rulings 1 (shell env is the Claude env minus all secret-kind and CCW_* names; exited terminal reaped at next tick), 2 (scrub test seeds every scrubbed name), 6 (cap reservation and synchronous unregister), 11 (kill whole shell session), 13 (verify adds test_manager.py with test_shutdown_stops_all deselected)

### S7: wrapper proxy seam

- Status: done
- Files: `src/agent_orchestrator/api/workspace.py`, `src/agent_orchestrator/api/app.py`, `src/agent_orchestrator/wrapper/client.py`, `tests/test_workspace_proxy.py`, `tests/test_wrapper_client.py`, `tests/test_api_clusters.py`, `README.md`, `MEMORY.md`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_workspace_proxy.py tests/test_wrapper_client.py tests/test_api_clusters.py tests/test_settings.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 093a155e09ab1248b87d755d1828432fc82b89e9

#### Requirement

Open the narrow seam through which the orchestrator api may call wrapper pods (user decision N1, design D4), test-first, before any proxy route exists.

- New `src/agent_orchestrator/api/workspace.py`, the only api module allowed to import `agent_orchestrator.wrapper` or use `agent_orchestrator.tokens`. It provides:
  - `resolve_agent(conn, settings, *, cluster_id=None, agent_id=None) -> WrapperTarget` (a frozen dataclass: `agent_id`, `cluster_id`, `pod_name`, `url`, `session_id`, and `token` declared `field(repr=False)` so it never shows in a repr, traceback or log line): with `agent_id` it loads that agent (404 `not_found` when unknown, or when `cluster_id` is given and differs); with only `cluster_id` it picks the first agent by ordinal that is ready (has `url` and `session_id` and a live status); none ready is 409 `agent_not_ready`; unknown cluster 404. The token is `tokens_for(settings, cluster_id).auth`; an unset master key raises 503 `unavailable`. Data comes from `db/agents.py` and `db/clusters.py`; no Kubernetes import.
  - a shared `httpx.AsyncClient` created lazily on first use (a `get_client(app)` helper, stored on `app.state`; no lifespan needed, so tests that never run the lifespan and drive the app through `httpx.ASGITransport` work), closed in the lifespan shutdown when it was created, and a helper that sends a request to the wrapper through `WrapperClient` and maps the outcome: wrapper 2xx returned as JSON; wrapper 4xx re-raised as `ApiError` with the wrapper's status and code; wrapper 5xx 502 `wrapper_error`; transport failure 502 `wrapper_unreachable`.
- `WrapperClient` (`src/agent_orchestrator/wrapper/client.py`) gains one generic method used by the helper, for example `request_json(method, path, *, params=None, json=None) -> tuple[int, Any]`, with its own test in `tests/test_wrapper_client.py`; existing methods are unchanged.
- `tests/test_api_clusters.py::test_api_never_imports_k8s_or_wrapper` whitelists exactly `api/workspace.py` for `agent_orchestrator.wrapper` (still banned: `agent_orchestrator.k8s` and `agent_orchestrator.reconciler` everywhere, and `agent_orchestrator.wrapper` in every other api module); a second assertion fails if any other api module imports `agent_orchestrator.tokens`.
- README `## Architecture`: the api row says the api calls wrappers only for the file and terminal proxies in `api/workspace.py`, never Kubernetes; `## Configuration`: `ORCH_MASTER_KEY` and `ORCH_MASTER_KEY_FILE` "Read by" lists include the api for the proxies; error codes `agent_not_ready` (409), `wrapper_error` (502), `wrapper_unreachable` (502), `unavailable` (503) in the API intro list.
- `MEMORY.md`: a dated entry (2026-10-23) amending D5: the api now calls wrapper pods with derived tokens, only through `api/workspace.py`, for the file and terminal proxies (user decision N1), because the wrapper is the only process with the workdir mounted and a PTY, and Kubernetes `pods/exec` is excluded.
- Token hygiene: the derived token is sent only as the `Authorization` header by `WrapperClient` (never in a URL, query string, response body, error detail or log message); a `caplog` test at DEBUG over the helper (file path and terminal path requests, success and every error mapping) finds the token in no log record and no response (interrogate ruling 7).
- Terminal id check: this module defines, once, `TERMINAL_ID_RE = re.compile(r"^term_[0-9a-f]{12}$")` (the wrapper registry's id format) and `validate_terminal_id(value) -> str`, which raises `ApiError` 422 `invalid_request` for anything else; the terminal HTTP routes and the WebSocket relay call it before any upstream request so the derived bearer can never reach another upstream path through a crafted id such as `..` (interrogate ruling 4).

#### Acceptance conditions

- AC1: resolve_agent picks the first ready agent by ordinal, honours an explicit agent_id, and answers not_found, agent_not_ready and unavailable as specified [evidence: test:tests/test_workspace_proxy.py::test_resolve_agent_rules]
- AC2: the forwarding helper maps wrapper 2xx, 4xx, 5xx and transport failure to the specified results [evidence: test:tests/test_workspace_proxy.py::test_forward_error_mapping]
- AC3: the shared httpx client is created lazily on first use, reused, and closed in the lifespan shutdown [evidence: test:tests/test_workspace_proxy.py::test_shared_client_lifecycle]
- AC4: WrapperClient.request_json sends the bearer and returns status and body [evidence: test:tests/test_wrapper_client.py::test_request_json_passthrough]
- AC5: only api/workspace.py may import agent_orchestrator.wrapper or agent_orchestrator.tokens [evidence: test:tests/test_api_clusters.py::test_api_never_imports_k8s_or_wrapper]
- AC6: MEMORY.md records the D5 amendment with date and why, and README Architecture names the proxy module [evidence: judgement:MEMORY.md and README.md Architecture]
- AC7: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_workspace_proxy.py tests/test_wrapper_client.py tests/test_api_clusters.py tests/test_settings.py && uv run ruff check . && uv run ruff format --check .]
- AC8: an app driven through httpx.ASGITransport without running the lifespan can use the proxy helper (the client is created on demand) [evidence: test:tests/test_workspace_proxy.py::test_client_works_without_lifespan]
- AC9: WrapperTarget.token is excluded from repr and a DEBUG caplog over file and terminal proxy requests, success and error paths, finds the token in no log record and no response [evidence: test:tests/test_workspace_proxy.py::test_token_never_in_logs_or_responses]
- AC10: validate_terminal_id accepts term_<12 lowercase hex> and answers 422 invalid_request for .., term_zz, uppercase, overlong, empty and path-like ids [evidence: test:tests/test_workspace_proxy.py::test_terminal_id_validator]

#### Files

- `src/agent_orchestrator/api/workspace.py`
- `src/agent_orchestrator/api/app.py`
- `src/agent_orchestrator/wrapper/client.py`
- `tests/test_workspace_proxy.py`
- `tests/test_wrapper_client.py`
- `tests/test_api_clusters.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

- `agent_orchestrator.api.workspace.resolve_agent`, `WrapperTarget`, the forwarding helper and the lifespan-managed client on `app.state` (owns part `workspace-proxy-module`, consumed by file-proxy-routes, terminal-proxy-routes, terminal-ws-relay).
- `agent_orchestrator.wrapper.client.WrapperClient.request_json`.

#### Expected outcome

The api has one audited module that can reach a cluster's wrapper pods with the derived token; every other api module stays wrapper-free, and the docs say so.

#### Steps

- Write `tests/test_workspace_proxy.py` (DB fixtures `pool`/`dsn`, `tests/factories.py:insert_cluster`/`insert_agent`, `FakeWrapper` for the forwarding cases), `test_request_json_passthrough` in `tests/test_wrapper_client.py`, and tighten `test_api_never_imports_k8s_or_wrapper`; run `uv run pytest -q -p no:cacheprovider tests/test_workspace_proxy.py tests/test_wrapper_client.py tests/test_api_clusters.py`: new tests fail.
- Implement `api/workspace.py`, the lifespan client in `api/app.py`, `request_json`; rerun: passes.
- README and MEMORY edits; `uv run pytest -q -p no:cacheprovider tests/test_settings.py`: passes.
- `uv run ruff check . && uv run ruff format --check .`: clean.

#### Notes

- `db/views.py:agent_rows` does not select `url`/`session_id`; use `db/agents.py:get_agent`/`list_agents` (`Agent.url`, `Agent.session_id`, `pod_name`, `ordinal`).
- Readiness: use the same notion of a usable agent the dispatcher uses (has a session and is not in a dead or discarding state); name the exact rule in the docstring.
- `WrapperClient` errors are `WrapperError`/`WrapperUnreachable` (`wrapper/client.py`); reuse its `_error_parts` for the wrapper code.
- DB tests use testcontainers (dockerd is running in this container).

- 2026-10-23 amended: interrogate rulings 4 (terminal id format pinned in one place), 7 (token hygiene: repr=False, header only, caplog test), 8 (shared httpx client created lazily so lifespan-less ASGITransport tests work)

### S8: fe retire ribbon

- Status: done
- Files: `frontend/src/App.tsx`, `frontend/src/App.test.tsx`, `frontend/src/layout/Shell.tsx`, `frontend/src/ribbon/Ribbon.tsx`, `frontend/src/ribbon/ClusterRow.tsx`, `frontend/src/ribbon/Ribbon.test.tsx`, `frontend/src/clusters/ClusterForm.test.tsx`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/App.test.tsx src/clusters/ClusterForm.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build`
- Verified head: c58e22096af1d5588687a3032307037e81b20fee

#### Requirement

Replace the left ribbon with the top bar in the app and retire the ribbon (user Q1, Q15; design D10), with retirement tests.

- `frontend/src/App.tsx` renders `TopBar` (task fe-top-bar) above the main area on every layout (phone, tablet, desktop); the hamburger opens `SessionsMenu` with an empty `settingsCategories`. App hosts the dialogs the ribbon owned: New cluster opens `ClusterForm mode="create"` (on save the new cluster's tab is selected); tab Discard opens `DiscardClusterDialog`. The main area renders `ChatView` for the selected cluster (the workspace panels arrive in fe-panel-workspace); with no clusters it shows "No clusters yet" and the New cluster button stays in the bar; the list load error is shown as before.
- Selection default (D10): when no tab is selected and clusters exist, the first cluster by slug is selected; when the selected cluster disappears, the first remaining one is.
- `frontend/src/layout/Shell.tsx` no longer renders an aside or the `ribbon-aside`/`ribbon-drawer` test ids (rewrite as the top-bar shell or delete it).
- Deleted: `frontend/src/ribbon/Ribbon.tsx`, `frontend/src/ribbon/ClusterRow.tsx`, `frontend/src/ribbon/Ribbon.test.tsx`; the "Ribbon wiring" test in `frontend/src/clusters/ClusterForm.test.tsx` is removed (its create and discard coverage moves to `App.test.tsx`). No UI path opens `ClusterForm mode="edit"`; the edit mode code itself and `patchCluster` stay (the cluster-presets epic removes them).

#### Acceptance conditions

- AC1: the app shows the top bar with one tab per cluster and the selected cluster's chat, and no aside [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t top_bar_replaces_ribbon]
- AC2: with no selection the first cluster by slug is selected, also after the selected one disappears [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t first_tab_selected_by_default]
- AC3: New cluster opens the create form and selects the created cluster; Discard opens the discard dialog [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t create_and_discard_from_top_bar]
- AC4: no Edit entry point exists in the rendered UI [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t no_edit_entry_point]
- AC5: Ribbon.tsx, ClusterRow.tsx and Ribbon.test.tsx are gone from git ls-files [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t ribbon_files_retired]
- AC6: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/App.test.tsx src/clusters/ClusterForm.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

#### Files

- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`
- `frontend/src/layout/Shell.tsx`
- `frontend/src/ribbon/Ribbon.tsx`
- `frontend/src/ribbon/ClusterRow.tsx`
- `frontend/src/ribbon/Ribbon.test.tsx`
- `frontend/src/clusters/ClusterForm.test.tsx`

#### Interfaces

- Uses `TopBar` and `SessionsMenu` (part `fe-sessions-menu`), `ClusterForm`, `DiscardClusterDialog`, `useClusters`.

#### Expected outcome

The running UI has tabs at the top and no left ribbon; the ribbon sources are gone from the repo.

#### Steps

- Rewrite `frontend/src/App.test.tsx` with the five tests (titles as in the AC refs; the retirement test runs `git ls-files src/ribbon/Ribbon.tsx src/ribbon/ClusterRow.tsx src/ribbon/Ribbon.test.tsx` with `node:child_process` from the frontend dir and expects empty output); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/App.test.tsx`: fails.
- Rewire `App.tsx`, rewrite or delete `Shell.tsx`, delete the ribbon files with `git rm`, drop the Ribbon wiring test; rerun; run the verify command: passes.

#### Notes

- Retirement tests assert on `git ls-files`, never on the filesystem (an untracked file can survive a merge). This task's deletions are pinned by `ribbon_files_retired`.
- `ribbon/AgentRow.tsx` stays for now (task fe-agents-strip retires it); `ribbon/useClusters.ts`, `stateMark.tsx`, `ContextGauge.tsx` stay.
- Keep `useLayout` breakpoints; on phone the top bar must still fit (tabs scroll).

### S9: file proxy routes

- Status: done
- Files: `src/agent_orchestrator/api/workspace.py`, `src/agent_orchestrator/api/schemas.py`, `tests/test_api_files.py`, `tests/fakes/fake_wrapper.py`, `tests/test_fake_wrapper_contract.py`, `README.md`, `openapi.json`, `frontend/src/api/schema.d.ts`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_files.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check .`
- Verified head: f2a3dfd9fa289c8eccad7bd1d0f4e734761d3a4a

#### Requirement

Proxy the wrapper file API through the orchestrator api (design D1, D4; user Q8, Q9), test-first.

Routes in `src/agent_orchestrator/api/workspace.py` (prefix `/api/v1`), with response models in `api/schemas.py`:

- `GET /api/v1/clusters/{cluster_id}/files?path=&offset=&agent_id=` -> 200 `FileListing` `{cluster_id, agent_id, root, path, entries: [{name, type, size, mtime}], next_offset}`: forwards to `GET /v1/sessions/{session_id}/files` on the agent chosen by `resolve_agent` (first ready agent, or `agent_id`).
- `GET /api/v1/clusters/{cluster_id}/files/content?path=&agent_id=` -> 200 `FileContent` `{cluster_id, agent_id, path, size, mtime, mime, kind, content}` from `GET /v1/sessions/{session_id}/files/content`.
- Wrapper errors pass through with status and code (`invalid_path` 400, `not_found` 404, `not_a_directory` 400, `not_a_file` 400); the proxy errors of D4 apply. `invalid_path`, `not_a_directory`, `not_a_file` are added to the README API error code list.

FakeWrapper (`tests/fakes/fake_wrapper.py`) gains both routes over a per-session temp workdir with the wrapper's field names, paging, kinds and error codes, and `tests/test_fake_wrapper_contract.py` gains file cases run against both the fake and the real image (`-m integration`), so the fake stays honest.

README: a `### \`GET /api/v1/clusters/{cluster_id}/files\`` and a `### \`GET /api/v1/clusters/{cluster_id}/files/content\`` section (parameters, response, errors). Regenerate `openapi.json` and `frontend/src/api/schema.d.ts`.

#### Acceptance conditions

- AC1: listing through the api returns the wrapper listing of the first ready agent with cluster_id and agent_id added, paging intact [evidence: test:tests/test_api_files.py::test_list_proxied_from_first_ready_agent]
- AC2: agent_id selects that agent and an agent of another cluster is not_found [evidence: test:tests/test_api_files.py::test_agent_id_selects_and_scopes]
- AC3: content is proxied with text, binary and too_large kinds [evidence: test:tests/test_api_files.py::test_content_proxied]
- AC4: wrapper invalid_path and not_found pass through and an unreachable wrapper is 502 wrapper_unreachable [evidence: test:tests/test_api_files.py::test_errors_pass_through]
- AC5: no ready agent answers 409 agent_not_ready [evidence: test:tests/test_api_files.py::test_no_ready_agent]
- AC6: README, openapi.json and schema.d.ts match the app [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_readme_api.py]
- AC7: the fake's file routes have contract cases collected under the integration marker [evidence: command:uv run pytest -q -p no:cacheprovider -m integration --collect-only tests/test_fake_wrapper_contract.py]
- AC8: targeted suites, schema check and lint pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_files.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check .]
- AC9: a wrapper not_found for path empty (missing workdir root) passes through as 404 not_found [evidence: test:tests/test_api_files.py::test_missing_root_not_found_passes_through]

#### Files

- `src/agent_orchestrator/api/workspace.py`
- `src/agent_orchestrator/api/schemas.py`
- `tests/test_api_files.py`
- `tests/fakes/fake_wrapper.py`
- `tests/test_fake_wrapper_contract.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`

#### Interfaces

- `GET /api/v1/clusters/{cluster_id}/files`, `GET /api/v1/clusters/{cluster_id}/files/content`; `schemas.FileEntry`, `FileListing`, `FileContent` (owns part `orch-files-api`, consumed by fe-filesystem-panel and kind-e2e-workspace).
- Uses `workspace-proxy-module` and the wrapper contract `wrapper-files-api` (wrapper README, task wrapper-file-api).

#### Expected outcome

A headless client can browse and read a cluster's workdir through `/api/v1` alone; the UI types exist in `schema.d.ts`.

#### Steps

- Extend FakeWrapper with the two routes and write `tests/test_api_files.py` (`client_for` pattern with `httpx.ASGITransport`, DB factories, a FakeWrapper per agent); run `uv run pytest -q -p no:cacheprovider tests/test_api_files.py`: fails (404).
- Add the routes and schemas; rerun: passes.
- README sections; `uv run python -m agent_orchestrator.api.openapi > openapi.json`; `mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend run gen:api`; run the verify command: passes.
- Add the contract cases to `tests/test_fake_wrapper_contract.py`; the integration run needs the new wrapper image and happens after wrapper-sha-pin (CI); here confirm collection only.

#### Notes

- `tests/test_readme_api.py::test_frontend_schema_matches_openapi` needs `frontend/node_modules`; the verify runs `npm ci` first.
- `schema.d.ts` is generated; never hand-edit it.
- The wrapper field names are the contract (wrapper README `GET /v1/sessions/{id}/files`); copy them, do not rename.
- Builder check ruling 11: A missing workdir root (not_found for path "") renders as an empty tree with the line "workdir not created yet", not as an error.

- 2026-10-23 amended: builder check rulings 11 add acceptance conditions AC9-AC9

### S10: terminal websocket api

- Status: done
- Files: `src/claude_code_wrapper/api/terminals.py`, `src/claude_code_wrapper/api/auth.py`, `src/claude_code_wrapper/api/app.py`, `README.md`, `tests/test_api_terminals.py`, `tests/test_api_auth.py`, `tests/test_readme_api.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py tests/test_api_auth.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 09b92769f4b2906f37cdc2f900aac39a5851f4e7

#### Requirement

Expose the terminal registry over HTTP and a WebSocket (design D2, D3), test-first, and make bearer auth work on WebSocket routes.

- `api/auth.py:require_auth` takes `starlette.requests.HTTPConnection` instead of `Request`, so the same dependency guards HTTP and WebSocket routes; a WebSocket upgrade without a valid bearer is denied before accept (HTTP 401 denial response with the `unauthorized` envelope).
- New `src/claude_code_wrapper/api/terminals.py`, registered in `api/app.py` under the `/v1` router:
  - `POST /v1/sessions/{id}/terminals` body `{"rows"?: int, "cols"?: int}` (extra keys rejected) -> 201 terminal object `{terminal_id, session_id, created_at, alive, exit_code, attached, rows, cols}`; 409 `terminal_limit` at the cap, 404 `not_found` for an unknown session.
  - `GET /v1/sessions/{id}/terminals` -> 200 `{"terminals": [...]}`.
  - `DELETE /v1/sessions/{id}/terminals/{terminal_id}` -> 204; 404 `terminal_not_found` when unknown.
  - `WS /v1/sessions/{id}/terminals/{terminal_id}/attach`: unknown session or terminal is denied before accept with 404. After accept: the scrollback snapshot as binary frames, then live PTY output as binary frames; client binary frames are written to the PTY; client text frames are JSON control: `{"type":"resize","cols","rows"}` resizes, `{"type":"ping"}` answers `{"type":"pong"}`, anything else closes 1003. A frame over `limits.terminal_max_frame_bytes` closes 1009. A subscriber dropped for overflow closes 1013. Shell exit sends `{"type":"exit","code":N}` then closes 1000. Closing the socket detaches (the shell keeps running).
- README (`## API reference`): a `###` section per HTTP route and one hand-written `### \`WS /v1/sessions/{id}/terminals/{terminal_id}/attach\`` section with the frame protocol and close codes; `## Errors` rows for `terminal_limit`, `terminal_not_found`, `session_not_active` (409) and `invalid_size` (422); `## Trust model` note that terminals are interactive login shells of the agent uid with every secret-kind Claude variable and the `CCW_*` tokens removed from their environment.
- `tests/test_readme_api.py` gains a check that every WebSocket route of the app (`APIWebSocketRoute`) has a README `### \`WS <path>\`` heading, since `_walk` sees only `APIRoute`.
- `terminal_id` path parameters (DELETE and the WebSocket attach) are accepted only in the registry's id format, `TERMINAL_ID_RE = ^term_[0-9a-f]{12}$`, defined once in `api/terminals.py` next to the id generator's format; anything else is 422 `invalid_request` (the WebSocket is denied before accept with the same 422), so a crafted id never reaches the registry or a path (interrogate ruling 4).

#### Acceptance conditions

- AC1: a WebSocket upgrade without a valid bearer is denied with 401 before accept, and HTTP auth behaves as before [evidence: test:tests/test_api_auth.py::test_websocket_requires_bearer]
- AC2: create, list and delete follow the documented statuses and bodies, with terminal_limit at the cap and terminal_not_found on unknown ids [evidence: test:tests/test_api_terminals.py::test_http_lifecycle]
- AC3: attach replays scrollback, streams output and writes input bytes to the shell [evidence: test:tests/test_api_terminals.py::test_attach_round_trip]
- AC4: resize and ping control frames work and an unknown control closes 1003 [evidence: test:tests/test_api_terminals.py::test_control_frames]
- AC5: an oversized frame closes 1009 and shell exit sends the exit frame then closes 1000 [evidence: test:tests/test_api_terminals.py::test_frame_cap_and_exit]
- AC6: detach leaves the shell alive and a second attach replays what was printed meanwhile [evidence: test:tests/test_api_terminals.py::test_reattach_replays]
- AC7: every WebSocket route is documented in the README [evidence: test:tests/test_readme_api.py::test_every_websocket_route_documented]
- AC8: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py tests/test_api_auth.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .]
- AC9: attaching to an exited shell replays the scrollback, sends the exit frame and closes 1000 [evidence: test:tests/test_api_terminals.py::test_attach_exited_replays_and_closes]
- AC10: create with rows or cols outside 1..1000 answers 422 invalid_size [evidence: test:tests/test_api_terminals.py::test_create_invalid_size]
- AC11: a resize frame out of range or malformed is ignored and the socket stays open [evidence: test:tests/test_api_terminals.py::test_bad_resize_ignored]
- AC12: create or attach on a known but not active session answers 409 session_not_active and an unknown session 404 [evidence: test:tests/test_api_terminals.py::test_session_not_active_vs_unknown]
- AC13: a terminal_id outside ^term_[0-9a-f]{12}$ (for example ..%2F, term_zz, an uppercase or overlong id) is 422 invalid_request on DELETE and denied with 422 before accept on the WebSocket [evidence: test:tests/test_api_terminals.py::test_invalid_terminal_id_rejected]
- AC14: the README Errors table lists session_not_active and invalid_size and the README tests stay green [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_readme_api.py]

#### Files

- `src/claude_code_wrapper/api/terminals.py`
- `src/claude_code_wrapper/api/auth.py`
- `src/claude_code_wrapper/api/app.py`
- `README.md`
- `tests/test_api_terminals.py`
- `tests/test_api_auth.py`
- `tests/test_readme_api.py`

#### Interfaces

- `claude_code_wrapper.api.auth.require_auth(conn: HTTPConnection) -> None`.
- Routes above (owns part `wrapper-terminals-api`, cross-repo contract `wrapper-terminals-api`, consumed by agent-orchestrator tasks terminal-proxy-routes and terminal-ws-relay): body fields, frame protocol and close codes are the contract.
- Uses `TerminalRegistry` (part `terminal-registry`).

#### Expected outcome

A client with the bearer token can create a shell in a session workdir, attach over WebSocket, type, resize, detach and reattach with scrollback, and delete it; every route is in the README.

#### Steps

- Write `tests/test_api_auth.py::test_websocket_requires_bearer` and `tests/test_api_terminals.py` (Starlette `TestClient.websocket_connect`, a real registry over `tmp_path` and `/bin/sh`), and `tests/test_readme_api.py::test_every_websocket_route_documented`; run `uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py tests/test_api_auth.py tests/test_readme_api.py`: new tests fail.
- Retype `require_auth`, add `api/terminals.py` and register it; write the README sections; rerun: passes.
- `uv run ruff check . && uv run ruff format --check .`: clean.

#### Notes

- Probe result from discovery: with `Request` typing, a WebSocket route under `v1` fails with `TypeError: require_auth() missing ... 'request'`; `HTTPConnection` works for both, and an `ApiError` raised during the handshake becomes a denial response.
- HTTP exception handlers do not apply inside an accepted WebSocket: errors there are close codes or the JSON control frames above.
- Run the send loop (queue to socket) and the receive loop (socket to PTY) as two tasks; when either ends, cancel the other and detach, so no task leaks per connection.
- `tests/test_manager.py::test_shutdown_stops_all` fails only in this container; never a verify target.
- Builder check ruling 1: Attaching to an exited shell replays the scrollback, sends the exit control frame, then closes 1000. The panel reopens tabs on mount only for alive shells from listTerminals.
- Builder check ruling 3: Rows or cols outside 1..1000 on create answer 422 with code invalid_size (wrapper, passed through by the orchestrator); a resize control frame out of range or malformed is ignored and logged, the socket stays open.
- Builder check ruling 5: Terminals exist only for an active session; create or attach on a known but not active session answers 409 session_not_active; 404 only for an unknown session. Stopping or destroying a session closes its shells.

- 2026-10-23 amended: builder check rulings 1,3,5 add acceptance conditions AC9-AC12

- 2026-10-23 amended: interrogate rulings 4 (terminal_id format check in the wrapper routes), 5 (README Errors rows session_not_active and invalid_size), 1 (Trust model wording follows the new env contract)

### S11: fe agents strip

- Status: done
- Files: `frontend/src/chat/AgentsStrip.tsx`, `frontend/src/chat/AgentsStrip.test.tsx`, `frontend/src/chat/ChatView.tsx`, `frontend/src/chat/AgentFilter.tsx`, `frontend/src/ribbon/AgentRow.tsx`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/chat src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build`
- Verified head: d5bce5e9fcc11eab8332bb1a546b54d578315aac

#### Requirement

Move the per-agent rows into the chat panel header as an agents strip merged with the agent filter (user Q2), test-first.

- New `frontend/src/chat/AgentsStrip.tsx`: `AgentsStrip({agents, selected, onToggle, autoCompactPct})`, one compact chip-like item per agent in `sortedAgents` order showing ordinal or pod name, `StateMark` for the agent state, "free since" age (`formatAge`, refreshed every second as `AgentRow` does today) and the agent's own `ContextGauge`; clicking an item toggles it in the chat filter exactly as `AgentFilter` chips do today (same selection semantics, same ChatLog filtering). The strip wraps or scrolls horizontally on narrow panels.
- `frontend/src/chat/ChatView.tsx` renders `AgentsStrip` where `AgentFilter` was; nothing else in ChatView changes (log, queue strip, composer, paging).
- Retired: `frontend/src/chat/AgentFilter.tsx` and `frontend/src/ribbon/AgentRow.tsx` (its `formatAge` and the 1 s clock move into `AgentsStrip.tsx` or a small `chat/agentAge.ts`).

#### Acceptance conditions

- AC1: the strip shows each agent's name, state mark, free-since age and own gauge in ordinal order [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/chat/AgentsStrip.test.tsx -t shows_agent_rows]
- AC2: clicking an agent toggles the chat filter as the old chips did [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/chat/AgentsStrip.test.tsx -t click_toggles_filter]
- AC3: formatAge keeps its outputs [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/chat/AgentsStrip.test.tsx -t format_age_unchanged]
- AC4: AgentFilter.tsx and AgentRow.tsx are gone from git ls-files [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/chat/AgentsStrip.test.tsx -t agent_filter_and_row_retired]
- AC5: chat tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/chat src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

#### Files

- `frontend/src/chat/AgentsStrip.tsx`
- `frontend/src/chat/AgentsStrip.test.tsx`
- `frontend/src/chat/ChatView.tsx`
- `frontend/src/chat/AgentFilter.tsx`
- `frontend/src/ribbon/AgentRow.tsx`

#### Interfaces

- `frontend/src/chat/AgentsStrip.tsx`: `AgentsStrip` props as above; `formatAge(ms: number): string` keeps its signature wherever it lands.

#### Expected outcome

The agent detail the ribbon used to show sits in the chat header, and filtering by agent works from the same items.

#### Steps

- Write `frontend/src/chat/AgentsStrip.test.tsx` (jsdom; titles as in the AC refs; retirement via `git ls-files src/chat/AgentFilter.tsx src/ribbon/AgentRow.tsx`); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/chat/AgentsStrip.test.tsx`: fails.
- Implement the strip, swap it into ChatView, `git rm` the two files; run the verify command: passes.

#### Notes

- `ChatLog.test.tsx`, `Composer.test.tsx` and `chatModel.test.ts` must stay green unchanged: they pin "chat stays as is".
- Retirement tests assert on `git ls-files`, never on the filesystem.

### S12: fe panel workspace

- Status: done
- Files: `frontend/src/layout/Workspace.tsx`, `frontend/src/layout/panelLayout.ts`, `frontend/src/layout/Workspace.test.tsx`, `frontend/src/App.tsx`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/Workspace.test.tsx src/App.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build`
- Verified head: e666c3ac101be8b9943acd66be46269a00a5fe86

#### Requirement

The three-panel cluster workspace (design D7; user Q11, Q12), test-first.

- New `frontend/src/layout/panelLayout.ts`: pure layout state per cluster: `sizes` (three percentages, default `[25, 45, 30]`), `collapsed` (set of `files`, `chat`, `terminal`). Rules: `minimize(p)` is refused when it would leave no expanded panel (so at most two are minimized); `maximize(p)` collapses the other two and expands `p`; `restore(p)` expands `p`; `reset()` returns to the default sizes with nothing collapsed. Serialised and validated for storage.
- New `frontend/src/layout/Workspace.tsx`: `Workspace({clusterId, files, chat, terminal})` where the three props are React nodes (slots). Desktop and tablet: a `react-resizable-panels` `Group` (horizontal) of three collapsible `Panel`s with two `Separator`s; each expanded panel has a small header with its name and minimize and maximize `IconButton`s (`@mui/icons-material`, `aria-label`s "Minimize <name>", "Maximize <name>"); a minimized panel renders as a narrow vertical strip with its name and a restore button ("Restore <name>"); double-click on a separator calls `reset()`. Layout and collapsed set persist per cluster with `saveJson`/`loadJson` under `orch:layout:<clusterId>` and are restored when the tab is shown again. Phone: one panel at a time with a three-way `ToggleButtonGroup` (Files, Chat, Terminal), default Chat.
- `frontend/src/App.tsx` renders `Workspace` for the selected cluster with `chat` = `ChatView`, and placeholder text nodes for `files` and `terminal` (the next tasks fill them).

#### Acceptance conditions

- AC1: minimize is refused for the last expanded panel, so at most two are minimized [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/Workspace.test.tsx -t at_most_two_minimized]
- AC2: maximize collapses the other two and restore expands a panel [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/Workspace.test.tsx -t maximize_and_restore]
- AC3: a minimized panel renders as a strip with its name and a restore button [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/Workspace.test.tsx -t minimized_strip_has_name_and_restore]
- AC4: double-click on a separator resets to 25/45/30 [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/Workspace.test.tsx -t separator_double_click_resets]
- AC5: layout persists per cluster and survives a remount; corrupt stored data falls back to the default [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/Workspace.test.tsx -t layout_persists_per_cluster]
- AC6: phone shows one panel at a time with a three-way switch, Chat by default [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/Workspace.test.tsx -t phone_three_way_switch]
- AC7: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/Workspace.test.tsx src/App.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]
- AC8: a maximized panel shows one Restore control that returns the layout from before maximize [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/Workspace.test.tsx -t maximized_restore_returns_previous_layout]
- AC9: restoring a single minimized strip returns that panel to its pre-minimize size [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/Workspace.test.tsx -t restore_minimized_to_previous_size]
- AC10: a minimized panel stays mounted [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/Workspace.test.tsx -t minimized_panel_stays_mounted]
- AC11: only the active cluster tab's Workspace is mounted and switching away unmounts it [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t only_active_cluster_workspace_mounted]

#### Files

- `frontend/src/layout/Workspace.tsx`
- `frontend/src/layout/panelLayout.ts`
- `frontend/src/layout/Workspace.test.tsx`
- `frontend/src/App.tsx`

#### Interfaces

- `Workspace({clusterId, files, chat, terminal})` slots (owns part `fe-workspace-slots`, consumed by fe-filesystem-panel and fe-terminal-panel).
- `panelLayout.ts` pure functions; uses `loadJson`/`saveJson` (part `fe-storage`) and `react-resizable-panels` 4 (`Group`, `Panel` with `collapsible`, `collapsedSize`, `panelRef` `collapse()`/`expand()`, `Separator`, `onLayoutChanged`) (part `fe-deps`).

#### Expected outcome

Each cluster tab is a resizable three-panel workspace with chat in the middle, and its arrangement is remembered per cluster.

#### Steps

- Write `frontend/src/layout/Workspace.test.tsx` (jsdom; mock `react-resizable-panels` with thin components that expose the imperative handle, or stub `ResizeObserver` if the real library works; titles as in the AC refs) and pure tests of `panelLayout.ts` in the same file; run `mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/Workspace.test.tsx`: fails.
- Implement `panelLayout.ts`, `Workspace.tsx`, wire `App.tsx`; run the verify command: passes.

#### Notes

- react-resizable-panels v4 renamed components (`Group`, `Panel`, `Separator`); v3 examples with `PanelGroup`/`PanelResizeHandle` do not apply. Numbers are pixels, unit-less strings are percent.
- Keep `App.test.tsx` green (it now sees the workspace around ChatView).
- Builder check ruling 7: A maximized panel shows one Restore control that returns the layout from before maximize; restoring a single minimized strip returns that panel to its pre-minimize size (Panel.expand()); double-click on a separator still resets 25/45/30.
- Builder check ruling 9: Only the active cluster tab's Workspace is mounted; switching away unmounts it and terminals reattach with scrollback replay on return. A minimized panel stays mounted, so its event subscription stays live.

- 2026-10-23 amended: builder check rulings 7,9 add acceptance conditions AC8-AC11

### S13: terminal proxy routes

- Status: done
- Files: `src/agent_orchestrator/api/workspace.py`, `src/agent_orchestrator/api/schemas.py`, `tests/test_api_terminals.py`, `tests/fakes/fake_wrapper.py`, `tests/test_fake_wrapper_contract.py`, `README.md`, `openapi.json`, `frontend/src/api/schema.d.ts`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py tests/test_api_files.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check .`
- Verified head: fbd686b83861ccc1c74ee3bfa203f13a5e8fbfd2

#### Requirement

Proxy the wrapper terminal lifecycle through the orchestrator api (design D4, D5; user Q4, Q5), test-first.

Routes in `src/agent_orchestrator/api/workspace.py`, models in `api/schemas.py`:

- `POST /api/v1/agents/{agent_id}/terminals` body `CreateTerminal` `{rows?, cols?}` (extra forbidden) -> 201 `TerminalView` `{agent_id, cluster_id, pod_name, terminal_id, created_at, alive, exit_code, attached, rows, cols}`; forwards to `POST /v1/sessions/{session_id}/terminals` on that agent; wrapper `terminal_limit` passes through as 409, `session_not_active` as 409 and `invalid_size` as 422.
- `GET /api/v1/clusters/{cluster_id}/terminals` -> 200 `TerminalList` `{terminals: [TerminalView], unavailable_agents: [agent_id]}`: queries every ready agent of the cluster concurrently (bounded by the shared client timeouts); an agent that fails is listed in `unavailable_agents` instead of failing the request.
- `DELETE /api/v1/agents/{agent_id}/terminals/{terminal_id}` -> 204; wrapper `terminal_not_found` passes through as 404. `terminal_id` is checked with `validate_terminal_id` (part `workspace-proxy-module`, `^term_[0-9a-f]{12}$`) before any upstream request: anything else is 422 `invalid_request` and the wrapper is never called.
- POST and DELETE depend on `require_allowed_origin` (part `origin-allowlist`): an unlisted Origin is 403 `forbidden_origin`.

FakeWrapper gains the terminal HTTP routes and a WebSocket attach route that emulates the wrapper protocol (replay buffer, echo of input bytes as output, resize and ping control, exit frame, close codes, bearer check), and `tests/test_fake_wrapper_contract.py` gains terminal cases (HTTP and WebSocket) against fake and real image under `-m integration`.

README: a `###` section per route; `terminal_limit` (409), `terminal_not_found` (404), `session_not_active` (409), `invalid_size` (422), `invalid_request` (422 for a malformed terminal id) and `forbidden_origin` usage in the error code list. Regenerate `openapi.json` and `frontend/src/api/schema.d.ts`.
- Token hygiene: the routes send the derived token only through the seam's helper as an `Authorization` header; a DEBUG `caplog` test over create, list and delete finds the token in no log record and no response body (interrogate ruling 7).
- The routes use the seam's lazily created shared client, so their tests run through `httpx.ASGITransport` without the lifespan (interrogate ruling 8).

#### Acceptance conditions

- AC1: create forwards to the agent's session and returns TerminalView with agent and pod fields [evidence: test:tests/test_api_terminals.py::test_create_on_agent]
- AC2: the cluster list merges every ready agent's terminals and reports a failing agent in unavailable_agents [evidence: test:tests/test_api_terminals.py::test_cluster_list_fans_out]
- AC3: delete returns 204 and unknown terminals are 404 terminal_not_found [evidence: test:tests/test_api_terminals.py::test_delete]
- AC4: terminal_limit passes through as 409 [evidence: test:tests/test_api_terminals.py::test_limit_passes_through]
- AC5: POST and DELETE with an unlisted Origin are 403 forbidden_origin, without Origin they pass [evidence: test:tests/test_api_terminals.py::test_origin_guard]
- AC6: README, openapi.json and schema.d.ts match the app [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_readme_api.py]
- AC7: terminal contract cases are collected under the integration marker [evidence: command:uv run pytest -q -p no:cacheprovider -m integration --collect-only tests/test_fake_wrapper_contract.py]
- AC8: targeted suites, schema check and lint pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py tests/test_api_files.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check .]
- AC9: invalid_size passes through as 422 [evidence: test:tests/test_api_terminals.py::test_invalid_size_passes_through]
- AC10: a terminal_id outside ^term_[0-9a-f]{12}$ on DELETE is 422 invalid_request and the fake wrapper receives no request [evidence: test:tests/test_api_terminals.py::test_invalid_terminal_id_rejected]
- AC11: session_not_active passes through as 409 [evidence: test:tests/test_api_terminals.py::test_session_not_active_passes_through]
- AC12: the README error code list names session_not_active and invalid_size and the README tests stay green [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_readme_api.py]
- AC13: a DEBUG caplog over create, list and delete finds the derived token in no log record and no response [evidence: test:tests/test_api_terminals.py::test_token_not_in_logs_or_responses]
- AC14: the terminal routes work in tests that never run the app lifespan [evidence: test:tests/test_api_terminals.py::test_routes_work_without_lifespan]

#### Files

- `src/agent_orchestrator/api/workspace.py`
- `src/agent_orchestrator/api/schemas.py`
- `tests/test_api_terminals.py`
- `tests/fakes/fake_wrapper.py`
- `tests/test_fake_wrapper_contract.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`

#### Interfaces

- `POST /api/v1/agents/{agent_id}/terminals`, `GET /api/v1/clusters/{cluster_id}/terminals`, `DELETE /api/v1/agents/{agent_id}/terminals/{terminal_id}`; `schemas.CreateTerminal`, `TerminalView`, `TerminalList` (owns part `orch-terminals-api`, consumed by fe-terminal-socket and kind-e2e-workspace).
- FakeWrapper terminal HTTP and WebSocket routes (owns part `fake-wrapper-terminals`, consumed by terminal-ws-relay).
- Uses `workspace-proxy-module`, `origin-allowlist` and the wrapper contract `wrapper-terminals-api`.

#### Expected outcome

A headless client can create, list and delete shells on any agent of a cluster through `/api/v1`; FakeWrapper speaks the wrapper terminal protocol for the relay task.

#### Steps

- Extend FakeWrapper (HTTP and WebSocket, real socket so the relay can use it) and write `tests/test_api_terminals.py`; run `uv run pytest -q -p no:cacheprovider tests/test_api_terminals.py`: fails (404).
- Add routes and schemas; rerun: passes.
- README sections, regenerate `openapi.json` and `schema.d.ts`; run the verify command: passes.
- Add contract cases to `tests/test_fake_wrapper_contract.py`; confirm collection.

#### Notes

- `tests/test_api_files.py` stays in the verify because both tasks edit `api/workspace.py` and `fake_wrapper.py`.
- The fake's WebSocket route must check the bearer header like the real wrapper (denial 401) so the relay test proves the token is sent.
- `schema.d.ts` is generated; never hand-edit it.
- Builder check ruling 3: Rows or cols outside 1..1000 on create answer 422 with code invalid_size (wrapper, passed through by the orchestrator); a resize control frame out of range or malformed is ignored and logged, the socket stays open.

- 2026-10-23 amended: builder check rulings 3 add acceptance conditions AC9-AC9

- 2026-10-23 amended: interrogate rulings 4 (terminal_id format check, 422), 5 (README error list gains session_not_active and invalid_size), 7 (token hygiene caplog test), 8 (lifespan-less tests)

### S14: wrapper workspace e2e

- Status: done
- Files: `tests/test_e2e_workspace.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_e2e_workspace.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: bd2c0235f91dea63f7b390a6bd2d1874ec36d0c8

#### Requirement

An API-only end-to-end test of the new wrapper workspace surface on the real service (headless parity), in a new `tests/test_e2e_workspace.py`.

Using the existing `ccw_service` and `fake_claude_bin` fixtures (real `run_service` on loopback ports, real HTTP and WebSocket, bearer auth on), one test module drives only the public `/v1` API:

- create a session (fake claude), write two files and a subdirectory into its workdir from the test, then `GET /files` lists them (dirs first) and `GET /files/content` returns a file's text; a `..` path is refused with `invalid_path`.
- `POST /terminals`, attach over WebSocket with the bearer header, send `echo $PWD; env\n`, and see the session workdir. The service is started with sentinel values seeded for every scrubbed name in both its own env and the session `env` (every `ClaudeEnv` secret-kind name such as `ANTHROPIC_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN`, plus `CCW_AUTH_TOKEN`, `CCW_PEER_TOKEN`, `CCW_HOOK_TOKEN`), so an absence is meaningful: the `env` output contains none of the names or sentinel values, while a seeded non-secret passthrough name is present; send a resize control and `stty size\n` and see the new size; ping gets pong.
- close the socket, reattach, and receive the earlier output as replay; `DELETE` the terminal; a further attach is denied with 404.
- an upgrade without the bearer is denied with 401.

Every wait is bounded (the module's own `wait_until` style), so a hang fails with what it waited for.

#### Acceptance conditions

- AC1: files are listed and read and an escape is refused through the real service [evidence: test:tests/test_e2e_workspace.py::test_files_over_real_service]
- AC2: a terminal runs in the workdir with an env from which every seeded secret name and value is absent (non-secret passthrough present), resizes, pongs, replays on reattach and is gone after delete [evidence: test:tests/test_e2e_workspace.py::test_terminal_over_real_service]
- AC3: an unauthenticated upgrade is denied [evidence: test:tests/test_e2e_workspace.py::test_terminal_upgrade_needs_bearer]
- AC4: the module and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_e2e_workspace.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `tests/test_e2e_workspace.py`

#### Interfaces

Consumes the parts `wrapper-files-api` and `wrapper-terminals-api` exactly as the README documents them; adds no product code.

#### Expected outcome

A headless client can browse the workdir and run a shell on a real wrapper with nothing but the documented API.

#### Steps

- Write `tests/test_e2e_workspace.py` (config built like `tests/test_e2e_lifecycle.py`, the `websockets` client already locked through `uvicorn[standard]`); run `uv run pytest -q -p no:cacheprovider tests/test_e2e_workspace.py`.
- If a test fails because the product deviates from the README, fix the product in its module under this task only when the README is right; otherwise record it as discovered.
- `uv run ruff check . && uv run ruff format --check .`: clean.

#### Ruling

- 2026-10-24 accepted: process-only tdd-skipped on an e2e test over surfaces already landed and verified; verify passes on HEAD

#### Notes

- Tests never use a real claude; the fake claude bin from `tests/conftest.py` is enough to bring a session up. Do not edit `tests/conftest.py`.
- `tests/test_manager.py::test_shutdown_stops_all` fails only in this container (PID 1 does not reap zombies; CI on main is green); never a verify target.

- 2026-10-23 amended: interrogate ruling 2: the scrub assertion must seed every scrubbed name into the service and Claude env before asserting absence

### S15: fe filesystem panel

- Status: done
- Files: `frontend/src/api/files.ts`, `frontend/src/files/useFileTree.ts`, `frontend/src/files/fileEvents.ts`, `frontend/src/files/FilesPanel.tsx`, `frontend/src/files/FilesPanel.test.tsx`, `frontend/src/App.tsx`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/files src/App.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build`
- Verified head: 4ce96dff654c4486a84d50f0b9f344500cf53aac

#### Requirement

The filesystem panel (design D8; user Q8, Q9, Q10), test-first.

- New `frontend/src/api/files.ts`: `listFiles(clusterId, path, offset?)` and `readFile(clusterId, path)` over `request` with the generated `FileListing`/`FileContent` types.
- New `frontend/src/files/useFileTree.ts`: per-cluster cache of loaded directories keyed by relative path; `expand(path)` loads a directory lazily on first expand; a truncated directory (`next_offset` not null) shows a "more" row that loads the next page and appends; `refresh(path)` re-fetches one directory; `refreshExpanded()` re-fetches every expanded directory.
- New `frontend/src/files/fileEvents.ts`: maps cluster events to refreshes: `tool_call` with name `Write`, `Edit` or `NotebookEdit` and `tool_input.file_path` inside the listing `root` refreshes the parent directory if it is loaded; a `tool_result` of `Bash` triggers `refreshExpanded()`, debounced to at most once per second. The panel subscribes with `openStream` on the cluster event stream URL for `tool_call` and `tool_result` from the live tail (no history replay) and closes it on unmount or cluster change.
- New `frontend/src/files/FilesPanel.tsx`: MUI X `SimpleTreeView` (MIT) rendering everything the API lists (dotfiles and `.git` included), folders and files with `@mui/icons-material` icons, a refresh button for the whole tree, and a read-only preview below or beside the tree: `text` shown in a monospace block, `binary` shown as size and mime type, `too_large` shown as size and "too large to preview"; errors shown inline (for example `agent_not_ready` while the cluster starts).
- `frontend/src/App.tsx` passes `FilesPanel` into the workspace `files` slot.

#### Acceptance conditions

- AC1: the root loads on mount and a folder's children load only on first expand [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t lazy_load_on_expand]
- AC2: a truncated directory shows a more row that loads the next page [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t more_row_pages]
- AC3: clicking a file previews text, binary and too-large files as specified [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t preview_kinds]
- AC4: a Write or Edit tool_call refreshes the loaded parent directory and a Bash tool_result refreshes expanded directories, debounced [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t event_driven_refresh]
- AC5: the refresh button re-fetches the tree and errors render inline [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t manual_refresh_and_errors]
- AC6: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/files src/App.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]
- AC7: a symlink entry is a leaf that previews through the content route and an escape error shows inline [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t symlink_previews_and_escape_error]
- AC8: other entry types are leaves showing the type only with no preview [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t other_entries_type_only]
- AC9: a missing workdir root renders an empty tree with the line workdir not created yet and no error [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t missing_root_empty_tree]
- AC10: the event stream stays open while the panel is mounted and closes on unmount [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/files/FilesPanel.test.tsx -t event_stream_closes_on_unmount]

#### Files

- `frontend/src/api/files.ts`
- `frontend/src/files/useFileTree.ts`
- `frontend/src/files/fileEvents.ts`
- `frontend/src/files/FilesPanel.tsx`
- `frontend/src/files/FilesPanel.test.tsx`
- `frontend/src/App.tsx`

#### Interfaces

- Uses `GET /api/v1/clusters/{cluster_id}/files` and `/files/content` (part `orch-files-api`, types from `schema.d.ts`), `openStream` and `eventStreamUrl`, the `files` slot (part `fe-workspace-slots`), `@mui/x-tree-view` and icons (part `fe-deps`).

#### Expected outcome

The left panel shows the cluster workdir like the VS Code explorer, stays current as agents write, and previews files read-only.

#### Steps

- Write `frontend/src/files/FilesPanel.test.tsx` (jsdom; `vi.mock('../api/files')` and `vi.mock('../api/stream')`, fake timers for the debounce; titles as in the AC refs); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/files/FilesPanel.test.tsx`: fails.
- Implement `api/files.ts`, `useFileTree.ts`, `fileEvents.ts`, `FilesPanel.tsx`, wire the slot; run the verify command: passes.

#### Notes

- MUI X tree lazy loading and virtualization are Pro features; load children by hand on expand (`onExpandedItemsChange`) and render a placeholder child so collapsed folders show an expand icon.
- Event data shape: `chatModel.ts` reads tool input as `data.tool_input ?? data.input` and name as `data.name ?? data.tool_name`; reuse the same accessors.
- `file_path` is absolute; map it to the tree with the listing `root` (paths outside `root` are ignored).
- Do not lift or change the private stream in `useClusterChat.ts`; ChatView stays untouched.
- Builder check ruling 8: Symlink entries are leaves that preview through the content route (an escape outside the workdir shows the wrapper error inline); other entries are leaves showing type only, no preview.
- Builder check ruling 9: Only the active cluster tab's Workspace is mounted; switching away unmounts it and terminals reattach with scrollback replay on return. A minimized panel stays mounted, so its event subscription stays live.
- Builder check ruling 11: A missing workdir root (not_found for path "") renders as an empty tree with the line "workdir not created yet", not as an error.

- 2026-10-23 amended: builder check rulings 8,9,11 add acceptance conditions AC7-AC10

### S16: terminal ws relay

- Status: done
- Files: `src/agent_orchestrator/api/workspace.py`, `pyproject.toml`, `uv.lock`, `tests/test_terminal_relay.py`, `README.md`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_terminal_relay.py tests/test_api_terminals.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 876c5be2f6eb34da9e0097b289e3646dfac4f030

#### Requirement

Relay terminal WebSockets from browsers and headless clients to the wrapper (design D2, D5, D6), test-first.

- `WS /api/v1/agents/{agent_id}/terminals/{terminal_id}/attach` in `src/agent_orchestrator/api/workspace.py`: the Origin middleware (part `origin-allowlist`) has already refused unlisted origins with 1008 before accept. The route accepts the client socket, resolves the agent with `resolve_agent`, and opens a client connection to `ws://<agent url host:port>/v1/sessions/{session_id}/terminals/{terminal_id}/attach` with `Authorization: Bearer <derived token>` using `websockets`. Failures close the client socket with: 4404 for an unknown agent or a wrapper 404 (unknown session or terminal), 4409 for an agent that is not ready, 1011 for an unreachable wrapper, a wrapper 401 or any other upstream failure.
- After both sides are open: binary frames and text frames are relayed unchanged in both directions; when either side closes, the other side is closed with the mapped code and both relay tasks end. Mapping: 1000, 1003, 1008, 1009, 1011, 1013 and 4000-4999 pass through unchanged; 1005 (no status received) maps to 1000; 1006 (abnormal), 1015 (TLS failure) and a close with no code map to 1011; 1005, 1006 and 1015 are reserved and are never sent in a close frame. No buffering beyond the `websockets` defaults; a relay never outlives its connections.
- `websockets` becomes a declared dependency in `pyproject.toml` (`websockets>=17.3`) and `uv.lock` is updated (`uv lock`).
- README: a hand-written `### \`WS /api/v1/agents/{agent_id}/terminals/{terminal_id}/attach\`` section with the frame protocol (binary PTY bytes; JSON `resize`, `ping`/`pong`, `exit`), the replay on attach, the close codes, the Origin rule and a headless example (Python `websockets` client), since WebSocket routes are not in OpenAPI.
- `terminal_id` is validated with `validate_terminal_id` (part `workspace-proxy-module`, `^term_[0-9a-f]{12}$`) before any upstream connection: an invalid id closes the client socket with 1008 and no wrapper connection is opened, so the derived bearer cannot reach another upstream path (interrogate ruling 4).
- Token hygiene: the derived token is sent only as the upstream `Authorization` header. `websockets` logs handshake headers at DEBUG, so the upstream connection is opened with `logger=` a dedicated logger held at WARNING that does not propagate its DEBUG output; a DEBUG `caplog` test over a full relay session finds the token in no log record and no frame sent to the client (interrogate ruling 7).

#### Acceptance conditions

- AC1: bytes typed into the api socket reach the fake wrapper shell and its output and replay come back unchanged [evidence: test:tests/test_terminal_relay.py::test_relay_round_trip]
- AC2: resize and ping control frames are relayed and pong comes back [evidence: test:tests/test_terminal_relay.py::test_control_frames_relayed]
- AC3: the relay sends the derived bearer token to the wrapper [evidence: test:tests/test_terminal_relay.py::test_bearer_sent_upstream]
- AC4: an unlisted Origin is refused before any wrapper connection is opened [evidence: test:tests/test_terminal_relay.py::test_origin_refused_before_upstream]
- AC5: unknown agent, unknown terminal, agent not ready and unreachable wrapper close with the documented codes [evidence: test:tests/test_terminal_relay.py::test_failure_close_codes]
- AC6: a close on either side closes the other with the mapped code (1000, 1003, 1009, 1013 pass through; 1005 becomes 1000; 1006, 1015 and no code become 1011; 1005, 1006 and 1015 are never re-sent) and leaves no relay task running [evidence: test:tests/test_terminal_relay.py::test_close_propagates_without_leak]
- AC7: websockets is a declared dependency and the lock is current [evidence: command:uv lock --check]
- AC8: the WebSocket route is documented in the README [evidence: command:grep -qF 'WS /api/v1/agents/{agent_id}/terminals/{terminal_id}/attach' README.md]
- AC9: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_terminal_relay.py tests/test_api_terminals.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .]
- AC10: an invalid terminal_id closes the client socket with 1008 and opens no upstream connection [evidence: test:tests/test_terminal_relay.py::test_invalid_terminal_id_refused]
- AC11: a DEBUG caplog over a full relay session finds the derived token in no log record and no client frame [evidence: test:tests/test_terminal_relay.py::test_token_not_in_logs]

#### Files

- `src/agent_orchestrator/api/workspace.py`
- `pyproject.toml`
- `uv.lock`
- `tests/test_terminal_relay.py`
- `README.md`

#### Interfaces

- `WS /api/v1/agents/{agent_id}/terminals/{terminal_id}/attach` (owns part `orch-terminal-ws`, consumed by fe-terminal-socket and kind-e2e-workspace).
- Uses `workspace-proxy-module`, `origin-allowlist`, `fake-wrapper-terminals` and the wrapper contract `wrapper-terminals-api`.

#### Expected outcome

A browser on an allowed origin, or a headless client with no Origin, gets an interactive shell on any agent pod through the api, with the wrapper token never leaving the api.

#### Steps

- Write `tests/test_terminal_relay.py`: serve `create_app(...)` with uvicorn on 127.0.0.1:0 inside the test loop (same pattern as `FakeWrapper.start`), register a FakeWrapper agent in the DB, connect with `websockets.asyncio.client.connect` (with and without an `origin`); run `uv run pytest -q -p no:cacheprovider tests/test_terminal_relay.py`: fails.
- Implement the relay and declare the dependency (`uv add 'websockets>=17.3'` or edit plus `uv lock`); rerun: passes.
- README section; run the verify command: passes.

#### Notes

- Do not use Starlette `TestClient` for these tests: it runs the app on its own loop, which conflicts with the async psycopg pool fixture; `httpx.ASGITransport` cannot do WebSockets at all (fix-as-ac from the reuse map).
- Only the Origin refusal happens before accept (middleware, 1008, seen by the client as HTTP 403); every other failure is a close after accept with the codes in the requirement, documented in the README.
- `websockets` 17 asyncio client: `from websockets.asyncio.client import connect`; pass headers with `additional_headers=`.
- A ping every 20 s comes from the browser and is relayed like any text frame; the api adds no pings of its own.
- Opus task: two concurrent pumps with cancellation on either close; make sure `asyncio.TaskGroup` or explicit cancel-and-await leaves nothing running.

- 2026-10-23 amended: interrogate rulings 3 (close-code mapping pinned in AC6 and test_close_propagates_without_leak), 4 (terminal_id format check, 1008 before upstream), 7 (token hygiene including websockets DEBUG handshake logging)

### S17: wrapper security followups

- Status: done
- Files: `src/claude_code_wrapper/terminals.py`, `src/claude_code_wrapper/api/terminals.py`, `src/claude_code_wrapper/service.py`, `src/claude_code_wrapper/config.py`, `README.md`, `tests/test_terminals.py`, `pyproject.toml`, `uv.lock`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_terminals.py tests/test_config.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 354e6695ad0b7ba9e3acdde446a3fff10aa6301b

#### Requirement

Close the security review findings on the wrapper terminal and file APIs (review 2026-10-24 against the integration branch).

1. PID reuse: when a terminal's shell has exited, closing it must never signal an unrelated process session that reused the pid. Record the shell's start time (field 22 of /proc/<pid>/stat) at spawn and skip the session-wide kill when the pid's current start time differs or the pid no longer exists.
2. Env scrub: besides SCRUBBED_ENV, drop every env key whose name matches the redactor's SECRET_KEY_RE (claude_env.py) from the shell env.
3. Frame cap before buffering: pass ws_max_size=cfg.limits.terminal_max_frame_bytes to uvicorn.Config in service.py so oversized frames are refused by the server before the app buffers them.
4. Attach cap: new setting limits.terminal_max_subscribers (default 8); an attach beyond it is refused with close code 1013 and reason "too many clients"; documented in the README config table.
5. README Trust model and design accuracy: state plainly that (a) the scrub does not cover /proc/<pid>/environ of processes running as the same uid (claude, wrapper), (b) a process started with setsid or a double fork leaves the shell's session and is not killed on close, destroy or reaper, (c) O_NOFOLLOW guards only the final path component, so a parent directory swapped for a symlink between check and open is not prevented (the reader is a trusted bearer holder), (d) passthrough and extra env names that do not match SECRET_KEY_RE (for example GIT_TOKEN when not matched) still reach the shell. Only the wrapper README changes here; the epic design doc is corrected separately.

6. Declare anyio as a direct dependency in pyproject.toml (src/claude_code_wrapper/api/terminals.py imports it), regenerating uv.lock with `uv lock`.

#### Acceptance conditions

- AC1: an exited terminal whose pid was reused by another session leader is closed without signalling that session [evidence: test:tests/test_terminals.py::test_close_skips_reused_pid]
- AC2: an env key matching SECRET_KEY_RE (for example MY_SERVICE_TOKEN) is absent from the shell env [evidence: test:tests/test_terminals.py::test_shell_env_drops_secret_named_keys]
- AC3: service.py passes ws_max_size from limits.terminal_max_frame_bytes to uvicorn.Config [evidence: test:tests/test_terminals.py::test_uvicorn_ws_max_size_matches_frame_cap]
- AC4: the attach beyond limits.terminal_max_subscribers is closed with 1013 [evidence: test:tests/test_terminals.py::test_attach_beyond_subscriber_cap_refused]
- AC5: README Trust model states the four limits (proc environ, setsid escape, parent symlink swap, unmatched passthrough names) and the config table lists terminal_max_subscribers [evidence: doc-section:README.md#trust-model]
- AC6: pyproject.toml lists anyio as a direct dependency and uv.lock is regenerated [evidence: command:grep -q anyio pyproject.toml && uv lock --check]

#### Files

- `src/claude_code_wrapper/terminals.py`
- `src/claude_code_wrapper/api/terminals.py`
- `src/claude_code_wrapper/service.py`
- `src/claude_code_wrapper/config.py`
- `README.md`
- `tests/test_terminals.py`
- `pyproject.toml`
- `uv.lock`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

A closed exited terminal never signals a reused pid; secret-named env keys never reach the shell; frames above the cap are refused by uvicorn; attaches beyond the subscriber cap close 1013; the README states the real isolation limits.

#### Steps

- Write the AC1-AC4 tests in tests/test_terminals.py and run the verify command: they fail.
- Implement the start-time pid guard, the SECRET_KEY_RE scrub, ws_max_size in service.py and limits.terminal_max_subscribers.
- Update the README Trust model and config table (AC5).
- Run the verify command: all pass. tests/test_manager.py::test_shutdown_stops_all fails only in this container (PID 1 does not reap zombies); do not chase it.

#### Ruling

- 2026-10-24 accepted: parking gate false positive: the README states the security limits the task requires (AC5); verified on HEAD 354e669

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S18: fake wrapper workdir regression

- Status: done
- Files: `tests/fakes/fake_wrapper.py`, `tests/test_api_files.py`, `tests/test_api_terminals.py`, `tests/test_terminal_relay.py`, `tests/test_workspace_proxy.py`, `tests/test_fake_wrapper_contract.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_session_bootstrap.py tests/test_api_files.py tests/test_api_terminals.py tests/test_terminal_relay.py tests/test_workspace_proxy.py tests/test_fake_wrapper_contract.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 18851216ec9bf98b5f86640d64674fa6d3b06ddd

#### Requirement

Regression from file-proxy-routes: tests/fakes/fake_wrapper.py now reports each session's workdir as a temp directory (`/tmp/fake-wrapper-*/ses_*`) instead of the workdir the caller requested (`/workdir/<workdir or name or sid>`, as before this epic), so tests/test_session_bootstrap.py::test_session_workdir_matches_rendered_workdir_path fails on the epic branch and passes on main.

Keep the reported session workdir exactly as before this epic (the logical path the real wrapper would report), and back the fake's file and terminal routes with a separate real temp directory per session (for example a `backing_dir` field on the fake session, exposed by the existing `FakeWrapper.workdir()` helper), mapping the logical root onto it. The file listing response's absolute `root` stays the reported (logical) workdir, as the real wrapper reports it. Every test that writes files through `FakeWrapper.workdir()` keeps working. Do not change production code under src/.

#### Acceptance conditions

- AC1: a session created through the fake reports the requested logical workdir [evidence: test:tests/test_session_bootstrap.py::test_session_workdir_matches_rendered_workdir_path]
- AC2: the file proxy tests list and read files written into the fake's backing directory, and the listing root equals the reported workdir [evidence: test:tests/test_api_files.py]
- AC3: the fake wrapper contract suite stays green [evidence: test:tests/test_fake_wrapper_contract.py]

#### Files

- `tests/fakes/fake_wrapper.py`
- `tests/test_api_files.py`
- `tests/test_api_terminals.py`
- `tests/test_terminal_relay.py`
- `tests/test_workspace_proxy.py`
- `tests/test_fake_wrapper_contract.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The full orchestrator suite passes on the epic branch; sessions report their logical workdir while file and terminal tests use a real backing directory.

#### Steps

- Run the verify command: test_session_workdir_matches_rendered_workdir_path fails (red already observed on the integration branch).
- Split the fake session's reported workdir from its backing directory.
- Run the verify command: all pass.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S19: fe terminal socket

- Status: done
- Files: `frontend/src/api/terminals.ts`, `frontend/src/terminal/terminalSocket.ts`, `frontend/src/terminal/terminalSocket.test.ts`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal/terminalSocket.test.ts src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build`
- Verified head: 236c3348fbf3ac753a56d3efb83a547ea82e8024

#### Requirement

The browser side of the terminal protocol (design D2; user Q5), test-first, with no UI yet.

- New `frontend/src/api/terminals.ts`: `createTerminal(agentId, {rows, cols})`, `listTerminals(clusterId)`, `deleteTerminal(agentId, terminalId)` over `request` with the generated `TerminalView`/`TerminalList` types, and `terminalSocketUrl(agentId, terminalId)` that builds `ws://` or `wss://` (matching `location.protocol`) on `location.host` plus `/api/v1/agents/{agent_id}/terminals/{terminal_id}/attach`.
- New `frontend/src/terminal/terminalSocket.ts`: `openTerminalSocket(url, {onData(bytes: Uint8Array), onExit(code), onStatus(status), WebSocketImpl?})` returning `{send(data: string | Uint8Array), resize(cols, rows), close()}`. Binary type `arraybuffer`; incoming binary frames go to `onData` (the first ones are the replay); incoming text frames are JSON control (`pong` ignored, `exit` calls `onExit` and stops); `send` encodes strings as UTF-8 binary frames and splits any input longer than `MAX_FRAME_BYTES` (65536, the wrapper default `terminal_max_frame_bytes`) into consecutive frames of at most that many bytes in order, so a large paste is never one oversized frame that the wrapper would close with 1009; `resize` sends `{"type":"resize","cols","rows"}` and remembers the size to resend after a reconnect; a `{"type":"ping"}` every 20 s while open. Reconnect on an abnormal close (not 1000, not after `exit`, not after `close()`, not on 4404 or 1008) with backoff from 1 s doubling to 30 s; a reconnect receives the replay again, so the caller resets its screen on each `onStatus('open')` after the first. `onStatus` reports `connecting`, `open`, `reconnecting`, `closed`, `refused`.

#### Acceptance conditions

- AC1: binary frames reach onData and strings are sent as UTF-8 binary frames [evidence: test:frontend/src/terminal/terminalSocket.test.ts::bytes_in_and_out]
- AC2: resize sends the control frame and is resent after a reconnect [evidence: test:frontend/src/terminal/terminalSocket.test.ts::resize_and_resend]
- AC3: a ping is sent every 20 s while open [evidence: test:frontend/src/terminal/terminalSocket.test.ts::ping_every_20s]
- AC4: abnormal closes reconnect with 1 to 30 s backoff, while 1000, exit, close(), 4404 and 1008 do not [evidence: test:frontend/src/terminal/terminalSocket.test.ts::reconnect_policy]
- AC5: the exit frame calls onExit with the code [evidence: test:frontend/src/terminal/terminalSocket.test.ts::exit_frame]
- AC6: the socket URL follows the page protocol and host [evidence: test:frontend/src/terminal/terminalSocket.test.ts::socket_url_from_location]
- AC7: tests, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal/terminalSocket.test.ts src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]
- AC8: close codes 1006, 1011, 1013 and 4409 reconnect and 1000, 1003, 1008 and 1009 never do [evidence: test:frontend/src/terminal/terminalSocket.test.ts::reconnect_close_codes]
- AC9: after 10 failed reconnect attempts the state is refused [evidence: test:frontend/src/terminal/terminalSocket.test.ts::refused_after_ten_attempts]
- AC10: send splits a string or Uint8Array larger than 64 KiB into ordered binary frames of at most 65536 bytes whose concatenation equals the input, and a smaller input stays one frame [evidence: test:frontend/src/terminal/terminalSocket.test.ts::large_paste_split_into_frames]

#### Files

- `frontend/src/api/terminals.ts`
- `frontend/src/terminal/terminalSocket.ts`
- `frontend/src/terminal/terminalSocket.test.ts`

#### Interfaces

- `frontend/src/terminal/terminalSocket.ts`: `openTerminalSocket` (owns part `fe-terminal-socket`, consumed by fe-terminal-panel).
- `frontend/src/api/terminals.ts`: the four functions above.
- Uses the api contract parts `orch-terminals-api` and `orch-terminal-ws` (README `WS /api/v1/agents/{agent_id}/terminals/{terminal_id}/attach`).

#### Expected outcome

A tested client that keeps a shell connection alive through ingress idle timeouts and reconnects with replay.

#### Steps

- Write `frontend/src/terminal/terminalSocket.test.ts` (node environment; a fake WebSocket class passed as `WebSocketImpl`; `vi.useFakeTimers()`; titles as in the AC refs); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal/terminalSocket.test.ts`: fails.
- Implement both modules; run the verify command: passes.

#### Notes

- Backoff constants mirror `api/stream.ts` (`BACKOFF_START_MS` 1000, `BACKOFF_MAX_MS` 30000); reuse them rather than duplicating numbers.
- The 20 s ping keeps ingress-nginx from closing an idle connection (its default proxy timeouts are 60 s; the deployed values are 3600).
- Builder check ruling 6: Reconnect on 1006, 1011, 1013 and 4409 with exponential backoff 1 s to 30 s, at most 10 attempts, then state refused; never reconnect on 1000, 1003, 1008, 1009. A refused tab stays with the reason, a Retry and a Close button.

- 2026-10-23 amended: builder check rulings 6 add acceptance conditions AC8-AC9

- 2026-10-23 amended: interrogate ruling 10: a large paste must not kill the terminal, so outgoing input is split into frames of at most 64 KiB

### S20: wrapper sha pin

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `e2e/agent-test.Dockerfile`, `README.md`, `tests/test_images.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 2edeb38eb5b2d6a1f279722387444ec0b6291f04

#### Requirement

Pin agent-orchestrator to the claude-code-wrapper commit that carries this epic's file and terminal APIs (design D9), so the integration contract suite and the kind e2e run against the real new wrapper.

The pin is claude-code-wrapper main merge commit `1ced7750483ee3eecdda5b6b26adc87405680ab1` (sha7 `1ced775`), the merge of PR szymonrychu/claude-code-wrapper#2 carrying this epic's file and terminal APIs.

- `pyproject.toml` dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@1ced7750483ee3eecdda5b6b26adc87405680ab1` and `uv.lock` (`uv lock`).
- `e2e/agent-test.Dockerfile`: `ARG BASE_IMAGE=harbor.szymonrichert.pl/containers/claude-code-wrapper:1ced775` and `ARG WRAPPER_SHA=1ced7750483ee3eecdda5b6b26adc87405680ab1`.
- README `## Images`: the recommended agent image is `harbor.szymonrichert.pl/containers/claude-code-wrapper:1ced775`.
- `tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha` keeps passing (it ties pyproject, uv.lock and README together); a new `test_agent_test_dockerfile_matches_dev_dependency` ties the Dockerfile `BASE_IMAGE` tag and `WRAPPER_SHA` to the same sha.
- `tests/test_render.py` keeps passing against the new wrapper's config schema.

#### Acceptance conditions

- AC1: pyproject, uv.lock, README Images and the agent-test Dockerfile all name the same wrapper commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- AC2: the existing pin consistency test passes on the new sha [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- AC3: the renderer's config validation passes on the new wrapper [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_render.py]
- AC4: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`
- `tests/test_images.py`

#### Interfaces

- The wrapper pin (owns part `wrapper-main-pin`, consumed by kind-e2e-workspace): pyproject dev dependency, `uv.lock`, `e2e/agent-test.Dockerfile` args, README `## Images`.

#### Expected outcome

`mise run test:integration` and the CI e2e job build the test agent image from the wrapper commit that has the file and terminal APIs.

#### Steps

- Add `test_agent_test_dockerfile_matches_dev_dependency` to `tests/test_images.py`, then change the pyproject pin and run `uv lock`; run `uv run pytest -q -p no:cacheprovider tests/test_images.py`: the new test and `test_ccw_dev_dependency_matches_agent_image_sha` fail (Dockerfile and README still name ca2ddf3).
- Update the Dockerfile args and README `## Images`; run the verify command: passes.

#### Notes

- Precedent: done epic agent-orchestrator task `container-images-ci` (dev dependency pinned to the wrapper main merge commit; README Images names the image).
- The Harbor image `claude-code-wrapper:<sha7>` exists only for main builds of the wrapper; check with `docker manifest inspect` or `regctl image digest` when credentials allow; without credentials `scripts/e2e.sh` builds the same commit from source.
- `tests/test_fake_wrapper_contract.py` without `-m integration` runs the fake only; the real-image run is the CI integration and e2e jobs.

- 2026-10-24 amended: wrapper PR #2 merged as 1ced775

### S21: fe terminal panel

- Status: done
- Files: `frontend/src/terminal/XtermView.tsx`, `frontend/src/terminal/TerminalPanel.tsx`, `frontend/src/terminal/TerminalPanel.test.tsx`, `frontend/src/theme.ts`, `frontend/src/App.tsx`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal src/App.test.tsx src/theme.test.ts src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build`
- Verified head: 25e24cc32aab9be6397016de55a79f03c29723dc

#### Requirement

The terminal panel (user Q4, Q5), test-first.

- New `frontend/src/terminal/XtermView.tsx`: one `@xterm/xterm` 6 `Terminal` with `@xterm/addon-fit`, colours from a `terminalTheme` exported by `frontend/src/theme.ts` (the only place colour literals may live); `fit()` on mount and whenever its container resizes (ResizeObserver; this covers panel drags, minimize and maximize), sending the new size through the socket's `resize`; keyboard input goes to `send`; socket data goes to `write`; on each reconnect after the first it calls `reset()` before the replay; on `exit` it prints a one-line notice and leaves the tab open.
- New `frontend/src/terminal/TerminalPanel.tsx`: `TerminalPanel({cluster, agents})` with MUI `Tabs` (one tab per shell, label pod name plus a short id) and a "New terminal" button that opens a menu of the cluster's agents with the first ready agent (by ordinal) preselected; choosing one calls `createTerminal` and opens a tab. On mount and on cluster change it calls `listTerminals(cluster.id)` and opens a tab per existing shell (so shells survive tab switches and reloads, user Q5). Closing a tab calls `deleteTerminal`. Switching tabs keeps the other shells attached or reattaches them (replay restores the screen). Empty state: "No terminals" with the New terminal button. Errors (for example `terminal_limit`, `forbidden_origin`, `agent_not_ready`) show inline.
- `frontend/src/App.tsx` passes `TerminalPanel` into the workspace `terminal` slot.

#### Acceptance conditions

- AC1: existing shells of the cluster open as tabs on mount [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t reattaches_existing_shells]
- AC2: New terminal preselects the first ready agent and creates a shell on the chosen agent [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t new_terminal_on_chosen_agent]
- AC3: several shells live as tabs and closing a tab deletes its shell [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t multiple_tabs_and_close]
- AC4: the view fits on container resize and sends the size, and resets before a reconnect replay [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t fit_on_resize_and_reset_on_reconnect]
- AC5: API errors render inline [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t errors_inline]
- AC6: terminal colours live in theme.ts and design rules pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/theme.test.ts src/layout/designRules.test.ts]
- AC7: tests, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal src/App.test.tsx src/theme.test.ts src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]
- AC8: only alive shells from listTerminals reopen as tabs on mount [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t reopens_only_alive_shells]
- AC9: a refused tab stays with its reason, a Retry button that reconnects and a Close button [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t refused_tab_retry_and_close]
- AC10: unmounting closes the sockets without deleting the shells and remounting reattaches with scrollback replay [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t remount_reattaches_with_replay]

#### Files

- `frontend/src/terminal/XtermView.tsx`
- `frontend/src/terminal/TerminalPanel.tsx`
- `frontend/src/terminal/TerminalPanel.test.tsx`
- `frontend/src/theme.ts`
- `frontend/src/App.tsx`

#### Interfaces

- Uses `openTerminalSocket` (part `fe-terminal-socket`), `api/terminals.ts`, the `terminal` slot (part `fe-workspace-slots`), `@xterm/xterm` 6 and `@xterm/addon-fit` 0.11 (part `fe-deps`).
- `frontend/src/theme.ts`: new export `terminalTheme` (xterm `ITheme`).

#### Expected outcome

The right panel runs several interactive shells on chosen agent pods, sized to the panel, surviving tab switches and reloads.

#### Steps

- Write `frontend/src/terminal/TerminalPanel.test.tsx` (jsdom; `vi.mock('@xterm/xterm')`, `vi.mock('@xterm/addon-fit')`, `vi.mock('../api/terminals')`, `vi.mock('./terminalSocket')`, a stub `ResizeObserver`; titles as in the AC refs); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal/TerminalPanel.test.tsx`: fails.
- Implement `XtermView.tsx`, `TerminalPanel.tsx`, `terminalTheme`, wire the slot; run the verify command: passes.

#### Notes

- xterm 6 removed the canvas renderer addon and reworked the viewport; use the default DOM renderer and import `@xterm/xterm/css/xterm.css` once.
- jsdom has no canvas, no ResizeObserver and no WebSocket: mock them; the real rendering is checked by the user in a browser after deploy.
- A colour literal outside `theme.ts` fails `designRules.test.ts`.
- Builder check ruling 1: Attaching to an exited shell replays the scrollback, sends the exit control frame, then closes 1000. The panel reopens tabs on mount only for alive shells from listTerminals.
- Builder check ruling 6: Reconnect on 1006, 1011, 1013 and 4409 with exponential backoff 1 s to 30 s, at most 10 attempts, then state refused; never reconnect on 1000, 1003, 1008, 1009. A refused tab stays with the reason, a Retry and a Close button.
- Builder check ruling 9: Only the active cluster tab's Workspace is mounted; switching away unmounts it and terminals reattach with scrollback replay on return. A minimized panel stays mounted, so its event subscription stays live.

- 2026-10-23 amended: builder check rulings 1,6,9 add acceptance conditions AC8-AC10

### S22: kind e2e workspace

- Status: done
- Files: `tests/e2e/test_e2e_kind.py`
- Verify: `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 5675058d903ed883d5f02c26f4c6db282765278f

#### Requirement

API-only kind e2e tests for the workspace features (headless parity), in `tests/e2e/test_e2e_kind.py` (marker `e2e`, run by `mise run test:e2e` and the PR CI `e2e` job).

On the kind cluster the existing fixtures bring up (`api`, `cluster`), using only `/api/v1` over the port-forward:

- `GET /api/v1/clusters/{id}/files` lists the cluster workdir (the agent-test scenario's files or a file the test makes an agent write) and `GET .../files/content` returns a file's text; a `..` path is 400 `invalid_path`.
- `POST /api/v1/agents/{agent_id}/terminals` creates a shell; the WebSocket `.../attach` (Python `websockets` client, no Origin) runs `pwd\n` and sees the workdir path and `echo ok\n` and sees `ok`; `GET /api/v1/clusters/{id}/terminals` lists it; reattach replays; `DELETE` removes it.
- the same WebSocket with `Origin: http://evil.example` is refused (HTTP 403 on the upgrade).
- the in-cluster pod refusal test pattern (`test_in_cluster_pod_refused_by_allowlist`) is unchanged.

`e2e/values-kind.yaml` already lists the port-forward origins (task origin-allowlist).

#### Acceptance conditions

- AC1: the new e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC2: the tests cover files, terminal lifecycle over WebSocket and the Origin refusal using only the public API [evidence: judgement:tests/e2e/test_e2e_kind.py reviewed against the requirement; executed by the PR CI e2e job]
- AC3: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `tests/e2e/test_e2e_kind.py`

#### Interfaces

Consumes `orch-files-api`, `orch-terminals-api`, `orch-terminal-ws` as documented in the README, on the agent image pinned by `wrapper-main-pin`.

#### Expected outcome

The PR CI e2e job proves on a real cluster with the real wrapper that a headless client can browse files and run a shell through the orchestrator.

#### Steps

- Write the tests next to the existing ones, reusing `api` and `cluster` fixtures and bounded waits.
- Run `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py`: the new tests are listed.
- `uv run ruff check . && uv run ruff format --check .`: clean.

#### Ruling

- 2026-10-24 accepted: test-only task; red/green shown on a local real-wrapper stack; kind run happens in PR CI

#### Notes

- No cluster access in this container: kind, helm apply and the e2e run are not possible here; verification here is collection plus lint, the real run is the orchestrator PR CI `e2e` job (`mise run test:e2e`).
- `pyproject.toml` addopts deselect `e2e` by default; the `-m e2e` flag is required.

- 2026-10-24 run web-ui-cluster-tabs-with-fil: dependency-failed on wrapper-sha-pin

### S23: be review fixes

- Status: done
- Files: `src/agent_orchestrator/cli.py`, `tests/test_cli.py`, `src/agent_orchestrator/db/agents.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_cli.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 96a6aa1d10d29c69eacfa805f6f2555f5d279cba

#### Requirement

Close the epic and security review findings on the backend (2026-10-24).

1. Frame cap at the server: build_uvicorn_config in src/agent_orchestrator/cli.py passes `ws_max_size=65536` (the wrapper's terminal frame cap; the UI already splits input into 64 KiB frames) so a client cannot make the api buffer 16 MiB frames before the relay forwards them.
2. Stale comment: src/agent_orchestrator/db/agents.py module docstring no longer says "the ribbon shows"; it names the cluster tabs and agents strip.

#### Acceptance conditions

- AC1: build_uvicorn_config sets ws_max_size to 65536 [evidence: test:tests/test_cli.py::test_uvicorn_config_caps_websocket_frames]
- AC2: no source comment refers to the retired ribbon [evidence: command:! grep -rn "ribbon shows" src/agent_orchestrator]

#### Files

- `src/agent_orchestrator/cli.py`
- `tests/test_cli.py`
- `src/agent_orchestrator/db/agents.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

uvicorn refuses WebSocket frames above 64 KiB; no comment names the retired ribbon.

#### Steps

- Write the AC tests and run the verify command: they fail.
- Implement the requirement.
- Run the verify command: all pass.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S24: deploy pin

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agent-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `mise x -- uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k 'not release_chart_version_and_needs and not db_secret_matches_rendered_cnpg_cluster' && uv run ruff check . && uv run ruff format --check .`
- Verified head: feec968aa0c2574aebb25c3ca63e8ae0d1fb973a

#### Requirement

Pin agents-helmfile to this epic's merged agent-orchestrator and claude-code-wrapper builds and allow the UI origin (design D9; precedent `docs/plans/done/cluster-form-defaults-and-ga/tasks/deploy-pin-d5a7738.md`).

The values: agent-orchestrator main merge `f1baa5b` (szymonrychu/agent-orchestrator#4, full `f1baa5ba4abbf968aff4694f6bbd7bae92eaf7a4`) and claude-code-wrapper main merge `1ced775` (szymonrychu/claude-code-wrapper#2).

- `helmfile.yaml.gotmpl`: release `agent-orchestrator` chart version `0.1.0-main.f1baa5b`.
- `values/agent-orchestrator/common.yaml`: `image.tag` `f1baa5b`; `agentImage` and `env.ORCH_AGENT_IMAGES` `harbor.szymonrichert.pl/containers/claude-code-wrapper:1ced775`; `env.ORCH_ALLOWED_ORIGINS: https://agents.szymonrichert.pl`; the ingress timeouts stay 3600 (already set).
- `tests/test_orchestrator_release.py`: the chart version and image tag agree on the orchestrator sha; `agentImage` and `ORCH_AGENT_IMAGES` agree on the wrapper sha; `ORCH_ALLOWED_ORIGINS` lists the ingress host with https.
- Nothing else changes. `helmfile apply` and `mise run smoke` are run by the user after the epic.

- The old `test_orchestrator_pin_is_d5a7738` is replaced by the sha-agreement tests. `test_release_chart_version_and_needs` and `test_db_secret_matches_rendered_cnpg_cluster` pull charts from harbor.szymonrichert.pl and cloudnative-pg.github.io, which this container's network policy blocks; they are deselected in this task's verify and run in CI and locally.

#### Acceptance conditions

- AC1: chart version and image tag agree on the orchestrator sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: agentImage and ORCH_AGENT_IMAGES agree on the wrapper sha [evidence: test:tests/test_orchestrator_release.py::test_agent_image_pins_agree]
- AC3: ORCH_ALLOWED_ORIGINS allows exactly the https ingress host [evidence: test:tests/test_orchestrator_release.py::test_allowed_origins_is_ingress_host]
- AC4: the release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

- Consumes the cross-epic contract `orch-allowed-origins` (`ORCH_ALLOWED_ORIGINS`) and the published chart `0.1.0-main.<sha7>` and images `agent-orchestrator:<sha7>`, `claude-code-wrapper:<sha7>`.

#### Expected outcome

`helmfile diff` shows only the chart version, the two image pins and the new origin setting for agent-orchestrator.

#### Steps

- Write or update the three tests in `tests/test_orchestrator_release.py` for the new values; run `uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py`: fails.
- Change the pins and add the setting; run the verify command: passes.

#### Ruling

- 2026-10-24 accepted: AC4 failures are the two chart-pull tests blocked by this container's network policy (harbor, cloudnative-pg); diff is exactly the pin; PR CI runs the full suite

#### Notes

- Check the chart and images exist before pinning when credentials allow (`helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator --version 0.1.0-main.<sha7>`); the precedent run blocked on a transient Harbor 403 in chart publish.
- Apply and smoke are not this task's verify: no cluster access in this container, and the user runs them.
- Builder check ruling 10: Accepted that only configured origins work; the orchestrator README and chart README document ORCH_ALLOWED_ORIGINS with http://localhost:5173 as the dev example; the helmfile sets only the ingress origin.

- 2026-10-24 run web-ui-cluster-tabs-with-fil: dependency-failed on kind-e2e-workspace

- 2026-10-24 amended: orchestrator PR #4 merged as f1baa5b; wrapper 1ced775

### S25: fe review fixes

- Status: done
- Files: `frontend/src/terminal/terminalSocket.ts`, `frontend/src/terminal/terminalSocket.test.ts`, `frontend/src/terminal/TerminalPanel.tsx`, `frontend/src/terminal/TerminalPanel.test.tsx`, `frontend/src/layout/TopBar.tsx`, `frontend/src/layout/TopBar.test.tsx`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal src/layout && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build`
- Verified head: 6227ccccc4d191c49d2f2f1e4771906651adb473

#### Requirement

Close the epic review findings on the frontend (epic review 2026-10-24).

1. Origin refusal reads as transient: an Origin-refused WebSocket upgrade is an HTTP 403 that the browser reports as close 1006, so frontend/src/terminal/terminalSocket.ts keeps reconnecting for 10 attempts. A socket that closes before it ever reached `open` on two consecutive attempts (the initial attempt and one retry) goes to state `refused` with the reason "connection refused before open (check ORCH_ALLOWED_ORIGINS)". A socket that had been open keeps the existing backoff policy (ruling 6).
2. TerminalPanel lists shells only on mount: re-list the cluster's terminals whenever the set of ready agents of the cluster changes (from the useClusters store), and show the `unavailable_agents` returned by GET /api/v1/clusters/{id}/terminals as a notice line in the panel ("shells on <pod> unavailable") instead of silently hiding them.
3. Indicators lost with the ribbon: each cluster tab label shows a hook-failed mark when the cluster's `discard_hook_failed` is true (with a tooltip "discard hook failed") and the ready/replicas count (for example `2/3`) beside the slug, as ClusterRow did before the ribbon retirement.

#### Acceptance conditions

- AC1: two consecutive closes before open put the terminal socket in refused with the ORCH_ALLOWED_ORIGINS reason; a socket that had opened keeps backoff [evidence: command:mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal/terminalSocket.test.ts -t "refuses after two closes before open"]
- AC2: the terminal panel re-lists shells when the cluster's ready agents change and renders unavailable_agents as a notice [evidence: command:mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal/TerminalPanel.test.tsx -t "relists when ready agents change and shows unavailable agents"]
- AC3: a cluster tab shows the hook-failed mark when discard_hook_failed and the ready/replicas count [evidence: command:mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/TopBar.test.tsx -t "tab shows hook failed mark and ready count"]

#### Files

- `frontend/src/terminal/terminalSocket.ts`
- `frontend/src/terminal/terminalSocket.test.ts`
- `frontend/src/terminal/TerminalPanel.tsx`
- `frontend/src/terminal/TerminalPanel.test.tsx`
- `frontend/src/layout/TopBar.tsx`
- `frontend/src/layout/TopBar.test.tsx`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

A refused terminal shows refused within two attempts; shells appear once an agent turns ready, with unavailable agents named; tabs show the hook-failed mark and ready count.

#### Steps

- Write the AC tests and run the verify command: they fail.
- Implement the requirement.
- Run the verify command: all pass.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none

## Rulings (migrated)

- wrapper-workspace-e2e: accept true, at 2026-10-24T00:23:52Z: process-only tdd-skipped on an e2e test over surfaces already landed and verified; verify passes on HEAD
- wrapper-security-followups: accept true, at 2026-10-24T00:39:51Z: parking gate false positive: the README states the security limits the task requires (AC5); verified on HEAD 354e669
- kind-e2e-workspace: accept true, at 2026-10-24T01:20:45Z: test-only task; red/green shown on a local real-wrapper stack; kind run happens in PR CI
- deploy-pin: accept true, at 2026-10-24T01:56:08Z: AC4 failures are the two chart-pull tests blocked by this container's network policy (harbor, cloudnative-pg); diff is exactly the pin; PR CI runs the full suite
