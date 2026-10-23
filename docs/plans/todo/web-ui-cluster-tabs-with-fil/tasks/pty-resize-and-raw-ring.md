---
title: pty resize and raw ring
status: todo
repo: claude-code-wrapper
value: shells can be resized and their output replayed byte for byte
files: [src/claude_code_wrapper/pty_proc.py, src/claude_code_wrapper/ring.py, tests/test_pty_proc.py, tests/test_ring.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_pty_proc.py tests/test_ring.py && mise run lint"
depends_on: []
owns: [pty-resize, ring-raw-snapshot]
uses: []
model: ""
estimate: 39
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
- AC4: the targeted PTY and ring suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_pty_proc.py tests/test_ring.py && mise run lint]

## Files

- `src/claude_code_wrapper/pty_proc.py`
- `src/claude_code_wrapper/ring.py`
- `tests/test_pty_proc.py`
- `tests/test_ring.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
