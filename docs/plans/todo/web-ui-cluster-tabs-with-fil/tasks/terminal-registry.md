---
title: terminal registry
status: todo
repo: claude-code-wrapper
value: "the wrapper can run, share, reap and close login shells in a session workdir with secrets scrubbed"
files: [src/claude_code_wrapper/terminals.py, src/claude_code_wrapper/config.py, src/claude_code_wrapper/manager.py, README.md, tests/test_terminals.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_terminals.py tests/test_readme_config.py tests/test_config.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [pty-resize-and-raw-ring, wrapper-file-api]
owns: [terminal-registry]
uses: [pty-resize, ring-raw-snapshot, wrapper-path-confinement]
model: opus
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# terminal registry

## Requirement

Add the wrapper's terminal registry (design D2, D3, D11; user Q4, Q5, Q6): the in-process owner of interactive shells, test-first, with no HTTP surface yet.

New `src/claude_code_wrapper/terminals.py` with a `TerminalRegistry` held by the `SessionManager` (for example `manager.terminals`):

- `create(session_id, rows=24, cols=80) -> TerminalInfo` starts a shell under `PtyProcess(ring_capacity=limits.terminal_scrollback_bytes)`: argv `/bin/bash -l` (or `/bin/sh -l` when `/bin/bash` is absent), cwd the session workdir resolved through `files.resolve_in_workdir(workdir, "")`, env = `manager.service_env` minus `CCW_AUTH_TOKEN`, `CCW_PEER_TOKEN`, `CCW_HOOK_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN`, with `TERM=xterm-256color`. Ids are `term_<12 lowercase hex>`. `TerminalInfo` carries `terminal_id`, `session_id`, `created_at`, `alive`, `exit_code`, `attached` (client count), `rows`, `cols`.
- Cap: at most `limits.terminals_max` (default 8) live terminals per wrapper process (one pod); one more raises a `TerminalLimit` error.
- `list(session_id) -> list[TerminalInfo]`, `get(session_id, terminal_id)` (unknown raises `TerminalNotFound`), `close(session_id, terminal_id)` (idempotent, uses `PtyProcess.close`).
- `attach(session_id, terminal_id) -> Attachment`: registers a subscriber and returns the scrollback snapshot (`Ring.raw()`) taken in the same synchronous step as the subscription, so no byte is lost or duplicated between replay and live output. Each subscriber has a bounded queue (bytes plus an exit marker); when a subscriber's queue overflows it is marked overflowed and dropped (the API task closes it with 1013) while the PTY reader and the other subscribers carry on. `Attachment.detach()` removes it. Input: `write(bytes)`; `resize(rows, cols)` uses `PtyProcess.resize`.
- Exit: when the shell exits every subscriber receives the exit marker with the exit code; the terminal stays listed with `alive: false` until closed or reaped.
- Reaper: a terminal with no attached client for `limits.terminal_idle_reap_seconds` (default 900) is closed and removed; an attached terminal is never reaped; an exited terminal with no client is removed after the same delay.
- Session destroy closes the session's terminals; `SessionManager.shutdown()` closes every terminal (bounded by the existing shutdown budget) and stops the reaper.

Config (`LimitsConfig`, each with a `## Configuration reference` row and its default in the wrapper README): `terminals_max` 8 (ge=0, 0 disables terminals), `terminal_scrollback_bytes` 262144 (ge=1), `terminal_idle_reap_seconds` 900 (gt=0), `terminal_max_frame_bytes` 65536 (ge=1, read by the API task).

## Acceptance conditions

- AC1: a created shell runs in the session workdir and echoes typed input back through a subscriber [evidence: test:tests/test_terminals.py::test_create_runs_shell_in_workdir]
- AC2: the shell env lacks CCW_AUTH_TOKEN, CCW_PEER_TOKEN, CCW_HOOK_TOKEN and CLAUDE_CODE_OAUTH_TOKEN and has TERM=xterm-256color [evidence: test:tests/test_terminals.py::test_env_scrubbed]
- AC3: the ninth live terminal is refused with TerminalLimit [evidence: test:tests/test_terminals.py::test_cap_per_process]
- AC4: attach returns the scrollback snapshot and then only newer bytes, with no gap or duplicate [evidence: test:tests/test_terminals.py::test_attach_replays_then_streams]
- AC5: an overflowing subscriber is dropped while the other subscriber keeps receiving output [evidence: test:tests/test_terminals.py::test_slow_subscriber_dropped_not_blocking]
- AC6: shell exit delivers the exit code to subscribers and marks the terminal not alive [evidence: test:tests/test_terminals.py::test_exit_reported]
- AC7: the reaper closes a detached terminal after the idle delay and never an attached one [evidence: test:tests/test_terminals.py::test_reaper_respects_attachment]
- AC8: destroying the session and manager shutdown close its terminals [evidence: test:tests/test_terminals.py::test_closed_on_destroy_and_shutdown]
- AC9: the config keys are documented with their defaults [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_readme_config.py tests/test_config.py]
- AC10: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_terminals.py tests/test_readme_config.py tests/test_config.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/terminals.py`
- `src/claude_code_wrapper/config.py`
- `src/claude_code_wrapper/manager.py`
- `README.md`
- `tests/test_terminals.py`

## Interfaces

- `claude_code_wrapper.terminals.TerminalRegistry` with `create`, `list`, `get`, `close`, `attach`, `close_all`; `TerminalInfo`, `Attachment` (`queue`, `detach()`, `write()`, `resize()`), errors `TerminalLimit`, `TerminalNotFound` (owns part `terminal-registry`, consumed by terminal-websocket-api).
- Uses `PtyProcess.resize` and `Ring.raw` (parts `pty-resize`, `ring-raw-snapshot`) and `files.resolve_in_workdir` (part `wrapper-path-confinement`).
- `LimitsConfig.terminals_max`, `terminal_scrollback_bytes`, `terminal_idle_reap_seconds`, `terminal_max_frame_bytes`.

## Expected outcome

The manager can start, fan out, resize, reap and close login shells in a session workdir, with secrets scrubbed and a hard per-pod cap, ready for the HTTP and WebSocket layer.

## Steps

- Write `tests/test_terminals.py` (AC1-AC8). Build a `SessionManager` with a stub or the `world` fixture only if needed; a registry constructed with a fake `workdir_of(session_id)` callable and an explicit `service_env` keeps it fast. Use a tiny reap delay in tests. Run `uv run pytest -q -p no:cacheprovider tests/test_terminals.py`: fails (ImportError).
- Implement `terminals.py`, the config keys and the manager wiring (destroy and shutdown); rerun: passes.
- Add the README config rows; run `uv run pytest -q -p no:cacheprovider tests/test_readme_config.py tests/test_config.py`: passes.
- `uv run ruff check . && uv run ruff format --check .`: clean.

## Notes

- Concurrency is the risk: `PtyProcess` has one `on_output` callback, called on the loop; fan out from it with `queue.put_nowait` per subscriber and treat `QueueFull` as overflow. Never await inside the callback.
- Snapshot and subscribe in the same synchronous block (no await between) so replay and live output join exactly.
- `CCW_HOOK_TOKEN` is per session and normally absent from `service_env`; scrub it anyway (defence in depth, user Q6; the same uid can still read `/proc`, which the trust model accepts).
- The shell is a login shell so `/etc/profile.d/mise-shims.sh` puts the mise tools on PATH in the image (Dockerfile:81).
- Tests run real children: use `/bin/sh` (present everywhere) and short `wait_until` bounds.
- `tests/test_manager.py::test_shutdown_stops_all` fails only in this container (PID 1 does not reap zombies; CI on main is green); never a verify target. Do not edit `tests/conftest.py`.
