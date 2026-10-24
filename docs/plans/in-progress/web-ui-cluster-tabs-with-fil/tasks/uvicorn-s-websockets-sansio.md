---
title: "uvicorn's websockets_sansio_impl logs 'ERROR: ASGI callable returned without completing handshake.' after every WebSocket denial response (401/404/409/422), even though the denial response itself is sent correctly."
status: todo
repo: claude-code-wrapper
value: "Each refused terminal attach on the deployed wrapper will produce a spurious ERROR log line; operators or log alerts may misread it as a server fault."
files: []
verify: ""
depends_on: []
owns: []
uses: []
model: ""
estimate: ""
estimate_by: ""
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# uvicorn's websockets_sansio_impl logs 'ERROR: ASGI callable returned without completing handshake.' after every WebSocket denial response (401/404/409/422), even though the denial response itself is sent correctly.

## Requirement

uvicorn's websockets_sansio_impl logs 'ERROR: ASGI callable returned without completing handshake.' after every WebSocket denial response (401/404/409/422), even though the denial response itself is sent correctly.

Where: uvicorn (third-party), .venv/.../uvicorn/protocols/websockets/websockets_sansio_impl.py:run_asgi

Why: Each refused terminal attach on the deployed wrapper will produce a spurious ERROR log line; operators or log alerts may misread it as a server fault.

## Acceptance conditions

- AC1: uvicorn's websockets_sansio_impl logs 'ERROR: ASGI callable returned without completing handshake.' after every WebSocket denial response (401/404/409/422), even though the denial response itself is sent correctly. at uvicorn (third-party), .venv/.../uvicorn/protocols/websockets/websockets_sansio_impl.py:run_asgi is resolved [evidence: judgement]

## Files



## Interfaces

Keep the interfaces around uvicorn (third-party), .venv/.../uvicorn/protocols/websockets/websockets_sansio_impl.py:run_asgi unchanged unless resolving it requires otherwise: uvicorn's websockets_sansio_impl logs 'ERROR: ASGI callable returned without completing handshake.' after every WebSocket denial response (401/404/409/422), even though the denial response itself is sent correctly..

## Expected outcome

uvicorn's websockets_sansio_impl logs 'ERROR: ASGI callable returned without completing handshake.' after every WebSocket denial response (401/404/409/422), even though the denial response itself is sent correctly. at uvicorn (third-party), .venv/.../uvicorn/protocols/websockets/websockets_sansio_impl.py:run_asgi is resolved, and Each refused terminal attach on the deployed wrapper will produce a spurious ERROR log line; operators or log alerts may misread it as a server fault. no longer applies.

## Steps

1. Write a failing test that shows: uvicorn's websockets_sansio_impl logs 'ERROR: ASGI callable returned without completing handshake.' after every WebSocket denial response (401/404/409/422), even though the denial response itself is sent correctly..
2. Fix it at uvicorn (third-party), .venv/.../uvicorn/protocols/websockets/websockets_sansio_impl.py:run_asgi.
3. Run the task verify command and confirm it passes.

## Notes

Discovered in task `terminal-websocket-api` during run `web-ui-cluster-tabs-with-fil`.

