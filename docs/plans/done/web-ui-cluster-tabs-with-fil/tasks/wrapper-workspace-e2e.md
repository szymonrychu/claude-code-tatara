---
title: wrapper workspace e2e
status: done
repo: claude-code-wrapper
value: proof that a headless client can browse files and run shells on a real wrapper
files: [tests/test_e2e_workspace.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_e2e_workspace.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [terminal-websocket-api]
model: ""
review: ""
verified_head: bd2c0235f91dea63f7b390a6bd2d1874ec36d0c8
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 5
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper workspace e2e

## Requirement

An API-only end-to-end test of the new wrapper workspace surface on the real service (headless parity), in a new `tests/test_e2e_workspace.py`.

Using the existing `ccw_service` and `fake_claude_bin` fixtures (real `run_service` on loopback ports, real HTTP and WebSocket, bearer auth on), one test module drives only the public `/v1` API:

- create a session (fake claude), write two files and a subdirectory into its workdir from the test, then `GET /files` lists them (dirs first) and `GET /files/content` returns a file's text; a `..` path is refused with `invalid_path`.
- `POST /terminals`, attach over WebSocket with the bearer header, send `echo $PWD; env\n`, and see the session workdir. The service is started with sentinel values seeded for every scrubbed name in both its own env and the session `env` (every `ClaudeEnv` secret-kind name such as `ANTHROPIC_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN`, plus `CCW_AUTH_TOKEN`, `CCW_PEER_TOKEN`, `CCW_HOOK_TOKEN`), so an absence is meaningful: the `env` output contains none of the names or sentinel values, while a seeded non-secret passthrough name is present; send a resize control and `stty size\n` and see the new size; ping gets pong.
- close the socket, reattach, and receive the earlier output as replay; `DELETE` the terminal; a further attach is denied with 404.
- an upgrade without the bearer is denied with 401.

Every wait is bounded (the module's own `wait_until` style), so a hang fails with what it waited for.

## Acceptance conditions

- AC1: files are listed and read and an escape is refused through the real service [evidence: test:tests/test_e2e_workspace.py::test_files_over_real_service]
- AC2: a terminal runs in the workdir with an env from which every seeded secret name and value is absent (non-secret passthrough present), resizes, pongs, replays on reattach and is gone after delete [evidence: test:tests/test_e2e_workspace.py::test_terminal_over_real_service]
- AC3: an unauthenticated upgrade is denied [evidence: test:tests/test_e2e_workspace.py::test_terminal_upgrade_needs_bearer]
- AC4: the module and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_e2e_workspace.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `tests/test_e2e_workspace.py`

## Interfaces

Consumes the parts `wrapper-files-api` and `wrapper-terminals-api` exactly as the README documents them; adds no product code.

## Expected outcome

A headless client can browse the workdir and run a shell on a real wrapper with nothing but the documented API.

## Steps

- Write `tests/test_e2e_workspace.py` (config built like `tests/test_e2e_lifecycle.py`, the `websockets` client already locked through `uvicorn[standard]`); run `uv run pytest -q -p no:cacheprovider tests/test_e2e_workspace.py`.
- If a test fails because the product deviates from the README, fix the product in its module under this task only when the README is right; otherwise record it as discovered.
- `uv run ruff check . && uv run ruff format --check .`: clean.

## Ruling

- 2026-10-24 accepted: process-only tdd-skipped on an e2e test over surfaces already landed and verified; verify passes on HEAD

## Notes

- Tests never use a real claude; the fake claude bin from `tests/conftest.py` is enough to bring a session up. Do not edit `tests/conftest.py`.
- `tests/test_manager.py::test_shutdown_stops_all` fails only in this container (PID 1 does not reap zombies; CI on main is green); never a verify target.

- 2026-10-23 amended: interrogate ruling 2: the scrub assertion must seed every scrubbed name into the service and Claude env before asserting absence
