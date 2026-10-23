# Reuse map: cluster tabs and presets

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
