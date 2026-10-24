# Discovery: claude-code-wrapper (at ca2ddf3)

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
