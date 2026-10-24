---
title: wrapper security followups
status: todo
repo: claude-code-wrapper
value: "shells cannot kill unrelated sessions or exceed attach and frame caps, and the README states the real isolation limits"
files: [src/claude_code_wrapper/terminals.py, src/claude_code_wrapper/api/terminals.py, src/claude_code_wrapper/service.py, src/claude_code_wrapper/config.py, README.md, tests/test_terminals.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_terminals.py tests/test_config.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [terminal-websocket-api, wrapper-workspace-e2e]
owns: []
uses: []
model: sonnet
estimate: 6
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

# wrapper security followups

## Requirement

Close the security review findings on the wrapper terminal and file APIs (review 2026-10-24 against the integration branch).

1. PID reuse: when a terminal's shell has exited, closing it must never signal an unrelated process session that reused the pid. Record the shell's start time (field 22 of /proc/<pid>/stat) at spawn and skip the session-wide kill when the pid's current start time differs or the pid no longer exists.
2. Env scrub: besides SCRUBBED_ENV, drop every env key whose name matches the redactor's SECRET_KEY_RE (claude_env.py) from the shell env.
3. Frame cap before buffering: pass ws_max_size=cfg.limits.terminal_max_frame_bytes to uvicorn.Config in service.py so oversized frames are refused by the server before the app buffers them.
4. Attach cap: new setting limits.terminal_max_subscribers (default 8); an attach beyond it is refused with close code 1013 and reason "too many clients"; documented in the README config table.
5. README Trust model and design accuracy: state plainly that (a) the scrub does not cover /proc/<pid>/environ of processes running as the same uid (claude, wrapper), (b) a process started with setsid or a double fork leaves the shell's session and is not killed on close, destroy or reaper, (c) O_NOFOLLOW guards only the final path component, so a parent directory swapped for a symlink between check and open is not prevented (the reader is a trusted bearer holder), (d) passthrough and extra env names that do not match SECRET_KEY_RE (for example GIT_TOKEN when not matched) still reach the shell. Only the wrapper README changes here; the epic design doc is corrected separately.

## Acceptance conditions

- AC1: an exited terminal whose pid was reused by another session leader is closed without signalling that session [evidence: test:tests/test_terminals.py::test_close_skips_reused_pid]
- AC2: an env key matching SECRET_KEY_RE (for example MY_SERVICE_TOKEN) is absent from the shell env [evidence: test:tests/test_terminals.py::test_shell_env_drops_secret_named_keys]
- AC3: service.py passes ws_max_size from limits.terminal_max_frame_bytes to uvicorn.Config [evidence: test:tests/test_terminals.py::test_uvicorn_ws_max_size_matches_frame_cap]
- AC4: the attach beyond limits.terminal_max_subscribers is closed with 1013 [evidence: test:tests/test_terminals.py::test_attach_beyond_subscriber_cap_refused]
- AC5: README Trust model states the four limits (proc environ, setsid escape, parent symlink swap, unmatched passthrough names) and the config table lists terminal_max_subscribers [evidence: review]

## Files

- `src/claude_code_wrapper/terminals.py`
- `src/claude_code_wrapper/api/terminals.py`
- `src/claude_code_wrapper/service.py`
- `src/claude_code_wrapper/config.py`
- `README.md`
- `tests/test_terminals.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
