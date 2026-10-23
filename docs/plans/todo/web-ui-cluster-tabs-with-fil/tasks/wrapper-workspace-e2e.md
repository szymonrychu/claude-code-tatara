---
title: wrapper workspace e2e
status: todo
repo: claude-code-wrapper
value: proof that a headless client can browse files and run shells on a real wrapper
files: [tests/test_e2e_workspace.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_e2e_workspace.py && mise run lint"
depends_on: [terminal-websocket-api]
owns: []
uses: [wrapper-files-api, wrapper-terminals-api]
model: ""
estimate: 32
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

# wrapper workspace e2e

## Requirement

An API-only end-to-end test of the new wrapper workspace surface on the real service (headless parity), in a new `tests/test_e2e_workspace.py`.

Using the existing `ccw_service` and `fake_claude_bin` fixtures (real `run_service` on loopback ports, real HTTP and WebSocket, bearer auth on), one test module drives only the public `/v1` API:

- create a session (fake claude), write two files and a subdirectory into its workdir from the test, then `GET /files` lists them (dirs first) and `GET /files/content` returns a file's text; a `..` path is refused with `invalid_path`.
- `POST /terminals`, attach over WebSocket with the bearer header, send `echo $PWD; env\n`, and see the session workdir and no `CCW_AUTH_TOKEN`, `CCW_PEER_TOKEN` or `CLAUDE_CODE_OAUTH_TOKEN` in the output; send a resize control and `stty size\n` and see the new size; ping gets pong.
- close the socket, reattach, and receive the earlier output as replay; `DELETE` the terminal; a further attach is denied with 404.
- an upgrade without the bearer is denied with 401.

Every wait is bounded (the module's own `wait_until` style), so a hang fails with what it waited for.

## Acceptance conditions

- AC1: files are listed and read and an escape is refused through the real service [evidence: test:tests/test_e2e_workspace.py::test_files_over_real_service]
- AC2: a terminal runs in the workdir with scrubbed env, resizes, pongs, replays on reattach and is gone after delete [evidence: test:tests/test_e2e_workspace.py::test_terminal_over_real_service]
- AC3: an unauthenticated upgrade is denied [evidence: test:tests/test_e2e_workspace.py::test_terminal_upgrade_needs_bearer]
- AC4: the module and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_e2e_workspace.py && mise run lint]

## Files

- `tests/test_e2e_workspace.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
