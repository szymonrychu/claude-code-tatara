---
title: pty resize and raw ring
status: in-progress
repo: claude-code-wrapper
value: shells can be resized and their output replayed byte for byte
files: [src/claude_code_wrapper/pty_proc.py, src/claude_code_wrapper/ring.py, tests/test_pty_proc.py, tests/test_ring.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_pty_proc.py tests/test_ring.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [pty-resize, ring-raw-snapshot]
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /home/user/claude-code-tatara/.claude/worktrees/web-ui-cluster-tabs-with-fil-pty-resize-and-raw-ring/claude-code-wrapper
branch: web-ui-cluster-tabs-with-fil-pty-resize-and-raw-ring
verified_head: ""
run: ""
provides: []
---

# pty resize and raw ring

## Requirement

Give the wrapper's PTY layer the two primitives an interactive shell needs, without changing how Claude sessions use it.

- `PtyProcess.resize(rows: int, cols: int) -> None` in `src/claude_code_wrapper/pty_proc.py` sets the window size of the running child's PTY (TIOCSWINSZ on the master, which delivers SIGWINCH to the foreground process group). Rows and cols must be 1..1000, else `ValueError`. Calling it before `start()` or after `close()` raises `RuntimeError`; it never blocks the event loop.
- `Ring.raw() -> bytes` in `src/claude_code_wrapper/ring.py` returns the newest bytes exactly as appended (no ANSI stripping, no decoding), at most `capacity` bytes, taken under the ring lock. `text()`, `tail()`, `contains()` and `written` behave as before.
- Existing callers (`session.py:_spawn`) are untouched; the existing tests in `tests/test_pty_proc.py` and `tests/test_ring.py` keep passing.

## Acceptance conditions

- AC1: resize changes the child's window size as seen by the child (`stty size` or `os.get_terminal_size` in a `py(...)` child prints the new rows and cols) [evidence: test:tests/test_pty_proc.py::test_resize_reaches_child]
- AC2: resize rejects out-of-range sizes and calls before start or after close [evidence: test:tests/test_pty_proc.py::test_resize_rejects_bad_sizes_and_states]
- AC3: Ring.raw returns the newest raw bytes, escapes included, capped at capacity [evidence: test:tests/test_ring.py::test_raw_keeps_escapes_and_caps]
- AC4: the targeted PTY and ring suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_pty_proc.py tests/test_ring.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/pty_proc.py`
- `src/claude_code_wrapper/ring.py`
- `tests/test_pty_proc.py`
- `tests/test_ring.py`

## Interfaces

- `claude_code_wrapper.pty_proc.PtyProcess.resize(self, rows: int, cols: int) -> None` (new, owns part `pty-resize`).
- `claude_code_wrapper.ring.Ring.raw(self) -> bytes` (new, owns part `ring-raw-snapshot`).
- Consumed by task terminal-registry (scrollback replay and resize control frames).

## Expected outcome

A shell started under `PtyProcess` can be resized while it runs, and its last N bytes of raw output can be replayed byte for byte.

## Steps

- Write `test_resize_reaches_child` and `test_resize_rejects_bad_sizes_and_states` in `tests/test_pty_proc.py` (use the existing `spawn` fixture and `py(...)` helper; the child loops printing `os.get_terminal_size(0)` on SIGWINCH or on a stdin line) and `test_raw_keeps_escapes_and_caps` in `tests/test_ring.py`; run `uv run pytest -q -p no:cacheprovider tests/test_pty_proc.py tests/test_ring.py`: the three new tests fail with AttributeError.
- Implement `resize` (reuse `_set_winsize` on the master fd) and `raw`; rerun: all pass.
- `uv run ruff check . && uv run ruff format --check .`: "All checks passed!".

## Notes

- Pure asyncio, no threads; `resize` is a synchronous ioctl and must check `self._fd` (or equivalent) is open.
- Do not touch `tests/conftest.py` (wrapper rule: only the fake-claude task edits it).
- `tests/test_manager.py::test_shutdown_stops_all` fails only in this container (PID 1 does not reap zombies; CI on main is green); it is not part of this task's verify.
