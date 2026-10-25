---
title: wrapper security followups
status: done
repo: claude-code-wrapper
value: "shells cannot kill unrelated sessions or exceed attach and frame caps, and the README states the real isolation limits"
files: [src/claude_code_wrapper/terminals.py, src/claude_code_wrapper/api/terminals.py, src/claude_code_wrapper/service.py, src/claude_code_wrapper/config.py, README.md, tests/test_terminals.py, pyproject.toml, uv.lock]
verify: "uv run pytest -q -p no:cacheprovider tests/test_terminals.py tests/test_config.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [terminal-websocket-api, wrapper-workspace-e2e]
model: sonnet
review: ""
verified_head: 354e6695ad0b7ba9e3acdde446a3fff10aa6301b
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 10
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper security followups

## Requirement

Close the security review findings on the wrapper terminal and file APIs (review 2026-10-24 against the integration branch).

1. PID reuse: when a terminal's shell has exited, closing it must never signal an unrelated process session that reused the pid. Record the shell's start time (field 22 of /proc/<pid>/stat) at spawn and skip the session-wide kill when the pid's current start time differs or the pid no longer exists.
2. Env scrub: besides SCRUBBED_ENV, drop every env key whose name matches the redactor's SECRET_KEY_RE (claude_env.py) from the shell env.
3. Frame cap before buffering: pass ws_max_size=cfg.limits.terminal_max_frame_bytes to uvicorn.Config in service.py so oversized frames are refused by the server before the app buffers them.
4. Attach cap: new setting limits.terminal_max_subscribers (default 8); an attach beyond it is refused with close code 1013 and reason "too many clients"; documented in the README config table.
5. README Trust model and design accuracy: state plainly that (a) the scrub does not cover /proc/<pid>/environ of processes running as the same uid (claude, wrapper), (b) a process started with setsid or a double fork leaves the shell's session and is not killed on close, destroy or reaper, (c) O_NOFOLLOW guards only the final path component, so a parent directory swapped for a symlink between check and open is not prevented (the reader is a trusted bearer holder), (d) passthrough and extra env names that do not match SECRET_KEY_RE (for example GIT_TOKEN when not matched) still reach the shell. Only the wrapper README changes here; the epic design doc is corrected separately.

6. Declare anyio as a direct dependency in pyproject.toml (src/claude_code_wrapper/api/terminals.py imports it), regenerating uv.lock with `uv lock`.

## Acceptance conditions

- AC1: an exited terminal whose pid was reused by another session leader is closed without signalling that session [evidence: test:tests/test_terminals.py::test_close_skips_reused_pid]
- AC2: an env key matching SECRET_KEY_RE (for example MY_SERVICE_TOKEN) is absent from the shell env [evidence: test:tests/test_terminals.py::test_shell_env_drops_secret_named_keys]
- AC3: service.py passes ws_max_size from limits.terminal_max_frame_bytes to uvicorn.Config [evidence: test:tests/test_terminals.py::test_uvicorn_ws_max_size_matches_frame_cap]
- AC4: the attach beyond limits.terminal_max_subscribers is closed with 1013 [evidence: test:tests/test_terminals.py::test_attach_beyond_subscriber_cap_refused]
- AC5: README Trust model states the four limits (proc environ, setsid escape, parent symlink swap, unmatched passthrough names) and the config table lists terminal_max_subscribers [evidence: doc-section:README.md#trust-model]
- AC6: pyproject.toml lists anyio as a direct dependency and uv.lock is regenerated [evidence: command:grep -q anyio pyproject.toml && uv lock --check]

## Files

- `src/claude_code_wrapper/terminals.py`
- `src/claude_code_wrapper/api/terminals.py`
- `src/claude_code_wrapper/service.py`
- `src/claude_code_wrapper/config.py`
- `README.md`
- `tests/test_terminals.py`
- `pyproject.toml`
- `uv.lock`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

A closed exited terminal never signals a reused pid; secret-named env keys never reach the shell; frames above the cap are refused by uvicorn; attaches beyond the subscriber cap close 1013; the README states the real isolation limits.

## Steps

- Write the AC1-AC4 tests in tests/test_terminals.py and run the verify command: they fail.
- Implement the start-time pid guard, the SECRET_KEY_RE scrub, ws_max_size in service.py and limits.terminal_max_subscribers.
- Update the README Trust model and config table (AC5).
- Run the verify command: all pass. tests/test_manager.py::test_shutdown_stops_all fails only in this container (PID 1 does not reap zombies); do not chase it.

## Ruling

- 2026-10-24 accepted: parking gate false positive: the README states the security limits the task requires (AC5); verified on HEAD 354e669

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
